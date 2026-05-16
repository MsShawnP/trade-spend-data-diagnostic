"""Tab 4: Retailer Risk — net-net margin by retailer with what-if scenarios."""

from datetime import date

from workbook.db import connect

from openpyxl.comments import Comment
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Font, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table
from openpyxl.worksheet.worksheet import Worksheet

from workbook.channel_mapping import (
    CHANNEL_RATE_COLS,
    CHANNEL_DISPLAY_ORDER,
    REGIONAL_RETAILERS,
    RETAILER_TO_CHANNEL,
)
from workbook.styles import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    ALIGN_RIGHT,
    FILL_INPUT,
    FONT_BODY,
    FONT_HEADER,
    FONT_SECTION,
    FONT_SMALL,
    NUM_FMT_DOLLAR,
    NUM_FMT_PCT,
    TABLE_STYLE,
)


def _query_retailer_data() -> dict:
    conn = connect()

    weeks = conn.execute(
        "SELECT DISTINCT week_ending FROM stg_scan_data ORDER BY week_ending DESC LIMIT 52"
    ).fetchall()
    oldest_week = weeks[-1][0]
    max_scan = weeks[0][0]

    rev_rows = conn.execute("""
        SELECT s.retailer, SUM(sd.dollars_sold)
        FROM stg_scan_data sd JOIN stg_stores s ON sd.store_id = s.store_id
        WHERE sd.week_ending >= %s
        GROUP BY s.retailer
    """, (oldest_week,)).fetchall()
    revenue_map = dict(rev_rows)
    total_revenue = sum(revenue_map.values())

    rates = {}
    for channel, col in CHANNEL_RATE_COLS.items():
        rates[channel] = conn.execute(f"SELECT AVG({col}) FROM stg_sku_costs").fetchone()[0]

    gm_map = {}
    for channel, wcol in [("Walmart", "wholesale_walmart"), ("Costco", "wholesale_costco"),
                          ("Whole Foods", "wholesale_whole_foods"), ("UNFI", "wholesale_unfi"),
                          ("DTC", "wholesale_dtc"), ("Regional", "wholesale_regional")]:
        r = conn.execute(f"SELECT AVG(cogs_per_unit), AVG({wcol}) FROM stg_sku_costs").fetchone()
        gm_map[channel] = (r[1] - r[0]) / r[1] if r[1] else 0

    op_ded_rows = conn.execute("""
        SELECT retailer_id, SUM(amount)
        FROM stg_deductions
        WHERE deduction_date > (%s::date - interval '365 days')::date AND deduction_date <= %s
          AND deduction_type != 'promo_billback'
        GROUP BY retailer_id
    """, (max_scan, max_scan)).fetchall()
    op_ded_map = dict(op_ded_rows)

    pb_rows = conn.execute("""
        SELECT retailer_id, SUM(amount)
        FROM stg_deductions
        WHERE deduction_date > (%s::date - interval '365 days')::date AND deduction_date <= %s
          AND deduction_type = 'promo_billback'
        GROUP BY retailer_id
    """, (max_scan, max_scan)).fetchall()
    pb_map = dict(pb_rows)

    conn.close()

    channel_order = ["Walmart", "UNFI", "Whole Foods", "Costco", "DTC"] + REGIONAL_RETAILERS

    retailers = []
    for retailer in channel_order:
        rev = revenue_map.get(retailer, 0)
        rate = rates.get(retailer, rates["Regional"])
        structural = rev * rate

        retailer_key = retailer.lower().replace(" ", "_")
        op_ded = op_ded_map.get(retailer_key, 0)
        pb_ded = pb_map.get(retailer_key, 0)

        all_in = structural + op_ded + pb_ded
        all_in_rate = all_in / rev if rev else 0

        gm_key = retailer if retailer in gm_map else "Regional"
        gross_margin = gm_map.get(gm_key, gm_map.get("Regional", 0.4))

        total_ded = op_ded + pb_ded

        retailers.append({
            "name": retailer,
            "channel": RETAILER_TO_CHANNEL.get(retailer, "Other"),
            "revenue": rev,
            "rev_share": rev / total_revenue if total_revenue else 0,
            "structural": structural,
            "structural_rate": rate,
            "op_deductions": op_ded,
            "op_ded_rate": op_ded / rev if rev else 0,
            "pb_deductions": pb_ded,
            "all_in": all_in,
            "all_in_rate": all_in_rate,
            "gross_margin": gross_margin,
            "net_net_margin": gross_margin - (all_in / rev if rev else 0),
            "total_deductions": total_ded,
        })

    kehe_op = op_ded_map.get("kehe", 0)
    kehe_pb = pb_map.get("kehe", 0)
    if kehe_op > 0 or kehe_pb > 0:
        retailers.append({
            "name": "KeHE (distributor)",
            "channel": "Distributor",
            "revenue": 0,
            "rev_share": 0,
            "structural": 0,
            "structural_rate": 0,
            "op_deductions": kehe_op,
            "op_ded_rate": 0,
            "pb_deductions": kehe_pb,
            "all_in": kehe_op + kehe_pb,
            "all_in_rate": 0,
            "gross_margin": 0,
            "net_net_margin": 0,
            "total_deductions": kehe_op + kehe_pb,
        })

    total_deductions = sum(r["total_deductions"] for r in retailers)
    for r in retailers:
        r["ded_share"] = r["total_deductions"] / total_deductions if total_deductions else 0

    return {
        "retailers": retailers,
        "total_revenue": total_revenue,
        "oldest_week": oldest_week,
        "max_scan": max_scan,
    }


def build_retailer_risk(ws: Worksheet) -> None:
    data = _query_retailer_data()
    retailers = data["retailers"]

    ws.sheet_view.showGridLines = False

    col_widths = [3, 22, 12, 14, 8, 14, 8, 15, 8, 12, 14, 8, 14, 15]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # --- Header ---
    ws.merge_cells("B1:N1")
    ws["B1"] = "Retailer Risk"
    ws["B1"].font = FONT_HEADER

    ws.merge_cells("B2:N2")
    ws["B2"] = f"Trailing 52 weeks ({data['oldest_week']} to {data['max_scan']})  |  Built {date.today().isoformat()}"
    ws["B2"].font = FONT_SMALL
    ws["B2"].alignment = ALIGN_LEFT

    # --- P&L summary table ---
    row = 4
    ws.cell(row=row, column=2, value="Retailer P&L Summary").font = FONT_SECTION

    row += 1
    headers = [
        "Retailer", "Channel", "Revenue", "Rev %", "Structural $",
        "Struct %", "Op Ded $", "Op Ded %", "Promo BB",
        "All-In $", "All-In %", "Gross Mrg", "Net-Net Mrg",
    ]
    for c, h in enumerate(headers, 2):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True)
        cell.alignment = ALIGN_CENTER

    table_start = row + 1
    for i, r in enumerate(retailers):
        rw = table_start + i

        ws.cell(row=rw, column=2, value=r["name"])
        ws.cell(row=rw, column=3, value=r["channel"])

        c = ws.cell(row=rw, column=4, value=r["revenue"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=5, value=r["rev_share"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=6, value=r["structural"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=7, value=r["structural_rate"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=8, value=r["op_deductions"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=9, value=r["op_ded_rate"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=10, value=r["pb_deductions"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=11, value=r["all_in"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=12, value=r["all_in_rate"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=13, value=r["gross_margin"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=14, value=r["net_net_margin"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

    table_end = table_start + len(retailers) - 1

    # Excel Table for P&L
    pnl_table = Table(displayName="tbl_RetailerPnL", ref=f"B{row}:N{table_end}")
    pnl_table.tableStyleInfo = TABLE_STYLE
    ws.add_table(pnl_table)

    # Conditional formatting on net-net margin
    margin_range = f"N{table_start}:N{table_end}"
    ws.conditional_formatting.add(
        margin_range,
        ColorScaleRule(
            start_type="num", start_value=0, start_color="FFC7CE",
            mid_type="num", mid_value=0.25, mid_color="FFEB9C",
            end_type="num", end_value=0.5, end_color="C6EFCE",
        ),
    )

    # --- Concentration risk data table (no chart) ---
    chart_retailers = [r for r in retailers if r["revenue"] > 0]

    cr_section_row = table_end + 3
    ws.cell(row=cr_section_row, column=2, value="Concentration Risk: Revenue Share vs. Deduction Share").font = FONT_SECTION

    cr_header_row = cr_section_row + 1
    ws.cell(row=cr_header_row, column=2, value="Retailer").font = FONT_BODY
    ws.cell(row=cr_header_row, column=3, value="Revenue Share").font = FONT_BODY
    ws.cell(row=cr_header_row, column=4, value="Deduction Share").font = FONT_BODY

    for i, r in enumerate(chart_retailers):
        rw = cr_header_row + 1 + i
        ws.cell(row=rw, column=2, value=r["name"])
        ws.cell(row=rw, column=3, value=r["rev_share"]).number_format = NUM_FMT_PCT
        ws.cell(row=rw, column=4, value=r["ded_share"]).number_format = NUM_FMT_PCT

    cr_end_row = cr_header_row + len(chart_retailers)

    # Excel Table for concentration risk
    cr_table = Table(displayName="tbl_ConcentrationRisk", ref=f"B{cr_header_row}:D{cr_end_row}")
    cr_table.tableStyleInfo = TABLE_STYLE
    ws.add_table(cr_table)

    # --- What-if trade rate inputs (compact — no chart gap) ---
    whatif_row = cr_end_row + 2
    ws.cell(row=whatif_row, column=2, value="What-If Trade Rate Scenario").font = FONT_SECTION

    whatif_row += 1
    ws.merge_cells(f"B{whatif_row}:I{whatif_row}")
    whatif_cell = ws.cell(row=whatif_row, column=2,
            value="Enter target all-in trade rates below. Savings show annual impact of achieving target."
            )
    whatif_cell.font = FONT_SMALL
    whatif_cell.alignment = ALIGN_LEFT

    whatif_row += 1
    whatif_headers = ["Retailer", "Revenue", "Current", "Target",
                      "At Target", "Current $", "Savings", "What-If Mrg"]
    for c, h in enumerate(whatif_headers, 2):
        cell = ws.cell(row=whatif_row, column=c, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True)
        cell.alignment = ALIGN_CENTER

    dv = DataValidation(type="decimal", operator="between", formula1="0", formula2="0.5")
    dv.error = "Enter a rate between 0% and 50%"
    dv.errorTitle = "Invalid rate"
    ws.add_data_validation(dv)

    for i, r in enumerate(chart_retailers):
        rw = whatif_row + 1 + i

        ws.cell(row=rw, column=2, value=r["name"])

        rev_cell = ws.cell(row=rw, column=3, value=r["revenue"])
        rev_cell.number_format = NUM_FMT_DOLLAR
        rev_cell.alignment = ALIGN_RIGHT

        cur_cell = ws.cell(row=rw, column=4, value=r["all_in_rate"])
        cur_cell.number_format = NUM_FMT_PCT
        cur_cell.alignment = ALIGN_CENTER

        target_cell = ws.cell(row=rw, column=5, value=r["all_in_rate"])
        target_cell.number_format = NUM_FMT_PCT
        target_cell.fill = FILL_INPUT
        target_cell.alignment = ALIGN_CENTER
        target_cell.protection = Protection(locked=False)
        target_cell.comment = Comment(
            "Enter a target all-in trade rate for this retailer. "
            "The savings and margin columns show the annual impact.",
            "System", width=260, height=60,
        )
        dv.add(target_cell)

        # Trade at target = revenue × target rate
        ws.cell(row=rw, column=6, value=f"=C{rw}*E{rw}").number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=6).alignment = ALIGN_RIGHT

        cur_trade = ws.cell(row=rw, column=7, value=r["all_in"])
        cur_trade.number_format = NUM_FMT_DOLLAR
        cur_trade.alignment = ALIGN_RIGHT

        # Annual savings = current trade - trade at target
        ws.cell(row=rw, column=8, value=f"=G{rw}-F{rw}").number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=8).alignment = ALIGN_RIGHT

        # What-if margin = gross_margin - target_rate
        gm_literal = f"{r['gross_margin']:.6f}"
        ws.cell(row=rw, column=9, value=f"={gm_literal}-E{rw}").number_format = NUM_FMT_PCT
        ws.cell(row=rw, column=9).alignment = ALIGN_CENTER

    whatif_end_row = whatif_row + len(chart_retailers)

    # --- Channel Rollup ---
    ch_section_row = whatif_end_row + 2
    ws.cell(row=ch_section_row, column=2, value="Channel Rollup").font = FONT_SECTION

    ch_header_row = ch_section_row + 1
    ch_headers = ["Channel", "Revenue", "Structural $", "Op Waste $", "All-In Rate", "Avg Net-Net Margin"]
    for c, h in enumerate(ch_headers, 2):
        cell = ws.cell(row=ch_header_row, column=c, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True)
        cell.alignment = ALIGN_CENTER

    # Aggregate by channel
    channel_agg: dict[str, dict] = {}
    for r in retailers:
        ch = r["channel"]
        if ch not in channel_agg:
            channel_agg[ch] = {"revenue": 0, "structural": 0, "op_deductions": 0,
                               "all_in": 0, "margins": [], "count": 0}
        agg = channel_agg[ch]
        agg["revenue"] += r["revenue"]
        agg["structural"] += r["structural"]
        agg["op_deductions"] += r["op_deductions"]
        agg["all_in"] += r["all_in"]
        if r["revenue"] > 0:
            agg["margins"].append(r["net_net_margin"])
            agg["count"] += 1

    ch_row_idx = 0
    for ch in CHANNEL_DISPLAY_ORDER:
        if ch not in channel_agg:
            continue
        agg = channel_agg[ch]
        rw = ch_header_row + 1 + ch_row_idx
        ws.cell(row=rw, column=2, value=ch)
        ws.cell(row=rw, column=3, value=agg["revenue"]).number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=3).alignment = ALIGN_RIGHT
        ws.cell(row=rw, column=4, value=agg["structural"]).number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=4).alignment = ALIGN_RIGHT
        ws.cell(row=rw, column=5, value=agg["op_deductions"]).number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=5).alignment = ALIGN_RIGHT
        ai_rate = agg["all_in"] / agg["revenue"] if agg["revenue"] else 0
        ws.cell(row=rw, column=6, value=ai_rate).number_format = NUM_FMT_PCT
        ws.cell(row=rw, column=6).alignment = ALIGN_CENTER
        avg_margin = sum(agg["margins"]) / len(agg["margins"]) if agg["margins"] else 0
        ws.cell(row=rw, column=7, value=avg_margin).number_format = NUM_FMT_PCT
        ws.cell(row=rw, column=7).alignment = ALIGN_CENTER
        ch_row_idx += 1

    ch_end_row = ch_header_row + ch_row_idx
    ch_table = Table(displayName="tbl_ChannelRollup", ref=f"B{ch_header_row}:G{ch_end_row}")
    ch_table.tableStyleInfo = TABLE_STYLE
    ws.add_table(ch_table)
