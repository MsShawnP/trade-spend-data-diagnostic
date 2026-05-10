"""Tab 4: Retailer Risk — net-net margin by retailer with what-if scenarios."""

import sqlite3
from datetime import date
from pathlib import Path

from openpyxl.chart import BarChart, Reference
from openpyxl.comments import Comment
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from workbook.styles import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    ALIGN_RIGHT,
    BORDER_THIN,
    FILL_INPUT,
    FONT_BODY,
    FONT_HEADER,
    FONT_SECTION,
    FONT_SMALL,
    NUM_FMT_DOLLAR,
    NUM_FMT_PCT,
)

CHANNEL_RATE_COLS = {
    "Walmart": "trade_spend_pct_walmart",
    "Costco": "trade_spend_pct_costco",
    "Whole Foods": "trade_spend_pct_whole_foods",
    "UNFI": "trade_spend_pct_unfi",
    "DTC": "trade_spend_pct_dtc",
}

REGIONAL_RETAILERS = [
    "Green Basket Market", "Southside Grocers",
    "Prairie Provisions", "Mountain Pantry Co", "Harbor Fresh",
]


def _query_retailer_data(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)

    weeks = conn.execute(
        "SELECT DISTINCT week_ending FROM scan_data ORDER BY week_ending DESC LIMIT 52"
    ).fetchall()
    oldest_week = weeks[-1][0]
    max_scan = weeks[0][0]

    # Revenue by retailer
    rev_rows = conn.execute("""
        SELECT s.retailer, SUM(sd.dollars_sold)
        FROM scan_data sd JOIN stores s ON sd.store_id = s.store_id
        WHERE sd.week_ending >= ?
        GROUP BY s.retailer
    """, (oldest_week,)).fetchall()
    revenue_map = dict(rev_rows)
    total_revenue = sum(revenue_map.values())

    # Structural trade rates
    rates = {}
    for channel, col in CHANNEL_RATE_COLS.items():
        rates[channel] = conn.execute(f"SELECT AVG({col}) FROM sku_costs").fetchone()[0]
    regional_rate = conn.execute("SELECT AVG(trade_spend_pct_regional) FROM sku_costs").fetchone()[0]

    # Gross margin by channel
    gm_map = {}
    for channel, wcol in [("Walmart", "wholesale_walmart"), ("Costco", "wholesale_costco"),
                          ("Whole Foods", "wholesale_whole_foods"), ("UNFI", "wholesale_unfi"),
                          ("DTC", "wholesale_dtc"), ("Regional", "wholesale_regional")]:
        r = conn.execute(f"SELECT AVG(cogs_per_unit), AVG({wcol}) FROM sku_costs").fetchone()
        gm_map[channel] = (r[1] - r[0]) / r[1] if r[1] else 0

    # Operational deductions by retailer (trailing 365, excl promo_billback)
    op_ded_rows = conn.execute("""
        SELECT retailer_id, SUM(amount)
        FROM deductions
        WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ?
          AND deduction_type != 'promo_billback'
        GROUP BY retailer_id
    """, (max_scan, max_scan)).fetchall()
    op_ded_map = dict(op_ded_rows)

    # Promo billback by retailer
    pb_rows = conn.execute("""
        SELECT retailer_id, SUM(amount)
        FROM deductions
        WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ?
          AND deduction_type = 'promo_billback'
        GROUP BY retailer_id
    """, (max_scan, max_scan)).fetchall()
    pb_map = dict(pb_rows)

    conn.close()

    # Build retailer data list
    # Order: major channels first by revenue, then regionals grouped
    channel_order = ["Walmart", "UNFI", "Whole Foods", "Costco", "DTC"] + REGIONAL_RETAILERS

    retailers = []
    for retailer in channel_order:
        rev = revenue_map.get(retailer, 0)
        rate = rates.get(retailer, regional_rate)
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

    # Also include KeHE (deductions only, no revenue in scan_data)
    kehe_op = op_ded_map.get("kehe", 0)
    kehe_pb = pb_map.get("kehe", 0)
    if kehe_op > 0 or kehe_pb > 0:
        retailers.append({
            "name": "KeHE (distributor)",
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


def build_retailer_risk(ws: Worksheet, db_path: Path) -> None:
    data = _query_retailer_data(db_path)
    retailers = data["retailers"]

    ws.sheet_view.showGridLines = False

    col_widths = [3, 20, 14, 10, 14, 10, 14, 10, 13, 14, 10, 10, 10]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # --- Header ---
    ws.merge_cells("B1:L1")
    ws["B1"] = "Retailer Risk"
    ws["B1"].font = FONT_HEADER

    ws.merge_cells("B2:L2")
    ws["B2"] = f"Trailing 52 weeks ({data['oldest_week']} to {data['max_scan']})  |  Built {date.today().isoformat()}"
    ws["B2"].font = FONT_SMALL

    # --- Summary table ---
    row = 4
    ws.cell(row=row, column=2, value="Retailer P&L Summary").font = FONT_SECTION

    row += 1
    headers = [
        "Retailer", "Revenue", "Rev %", "Structural $",
        "Struct %", "Op Deductions", "Op Ded %", "Promo BB",
        "All-In Trade", "All-In %", "Gross Margin", "Net-Net Margin",
    ]
    for c, h in enumerate(headers, 2):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True)
        cell.border = BORDER_THIN
        cell.alignment = ALIGN_CENTER

    table_start = row + 1
    ws.auto_filter.ref = f"B{row}:{get_column_letter(len(headers) + 1)}{row + len(retailers)}"

    for i, r in enumerate(retailers):
        rw = table_start + i

        ws.cell(row=rw, column=2, value=r["name"]).border = BORDER_THIN

        c = ws.cell(row=rw, column=3, value=r["revenue"])
        c.number_format = NUM_FMT_DOLLAR
        c.border = BORDER_THIN
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=4, value=r["rev_share"])
        c.number_format = NUM_FMT_PCT
        c.border = BORDER_THIN
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=5, value=r["structural"])
        c.number_format = NUM_FMT_DOLLAR
        c.border = BORDER_THIN
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=6, value=r["structural_rate"])
        c.number_format = NUM_FMT_PCT
        c.border = BORDER_THIN
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=7, value=r["op_deductions"])
        c.number_format = NUM_FMT_DOLLAR
        c.border = BORDER_THIN
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=8, value=r["op_ded_rate"])
        c.number_format = NUM_FMT_PCT
        c.border = BORDER_THIN
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=9, value=r["pb_deductions"])
        c.number_format = NUM_FMT_DOLLAR
        c.border = BORDER_THIN
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=10, value=r["all_in"])
        c.number_format = NUM_FMT_DOLLAR
        c.border = BORDER_THIN
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=11, value=r["all_in_rate"])
        c.number_format = NUM_FMT_PCT
        c.border = BORDER_THIN
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=12, value=r["gross_margin"])
        c.number_format = NUM_FMT_PCT
        c.border = BORDER_THIN
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=13, value=r["net_net_margin"])
        c.number_format = NUM_FMT_PCT
        c.border = BORDER_THIN
        c.alignment = ALIGN_CENTER

    table_end = table_start + len(retailers) - 1

    # Conditional formatting on net-net margin (gradient green to red)
    margin_range = f"M{table_start}:M{table_end}"
    ws.conditional_formatting.add(
        margin_range,
        ColorScaleRule(
            start_type="num", start_value=0, start_color="FFC7CE",
            mid_type="num", mid_value=0.25, mid_color="FFEB9C",
            end_type="num", end_value=0.5, end_color="C6EFCE",
        ),
    )

    # --- Concentration risk chart ---
    chart_row = table_end + 3
    ws.cell(row=chart_row, column=2, value="Concentration Risk: Revenue Share vs. Deduction Share").font = FONT_SECTION

    # Write chart data (only retailers with revenue)
    chart_data_row = chart_row + 1
    ws.cell(row=chart_data_row, column=2, value="Retailer").font = FONT_BODY
    ws.cell(row=chart_data_row, column=3, value="Revenue Share").font = FONT_BODY
    ws.cell(row=chart_data_row, column=4, value="Deduction Share").font = FONT_BODY

    chart_retailers = [r for r in retailers if r["revenue"] > 0]
    for i, r in enumerate(chart_retailers):
        rw = chart_data_row + 1 + i
        ws.cell(row=rw, column=2, value=r["name"])
        ws.cell(row=rw, column=3, value=r["rev_share"]).number_format = NUM_FMT_PCT
        ws.cell(row=rw, column=4, value=r["ded_share"]).number_format = NUM_FMT_PCT

    chart_data_end = chart_data_row + len(chart_retailers)

    chart = BarChart()
    chart.type = "col"
    chart.grouping = "clustered"
    chart.title = "Revenue Share vs. Deduction Share"
    chart.y_axis.numFmt = '0%'
    chart.width = 18
    chart.height = 10

    cats = Reference(ws, min_col=2, min_row=chart_data_row + 1, max_row=chart_data_end)
    rev_data = Reference(ws, min_col=3, min_row=chart_data_row, max_row=chart_data_end)
    ded_data = Reference(ws, min_col=4, min_row=chart_data_row, max_row=chart_data_end)
    chart.add_data(rev_data, titles_from_data=True)
    chart.add_data(ded_data, titles_from_data=True)
    chart.set_categories(cats)
    chart.series[0].graphicalProperties.solidFill = "2F5496"
    chart.series[1].graphicalProperties.solidFill = "C00000"

    ws.add_chart(chart, f"B{chart_data_end + 2}")

    # --- Net-net margin chart ---
    margin_chart_row = chart_data_end + 18
    ws.cell(row=margin_chart_row, column=2, value="Net-Net Effective Margin by Retailer").font = FONT_SECTION

    margin_data_row = margin_chart_row + 1
    ws.cell(row=margin_data_row, column=2, value="Retailer").font = FONT_BODY
    ws.cell(row=margin_data_row, column=3, value="Gross Margin").font = FONT_BODY
    ws.cell(row=margin_data_row, column=4, value="After Structural").font = FONT_BODY
    ws.cell(row=margin_data_row, column=5, value="Net-Net (after all trade)").font = FONT_BODY

    for i, r in enumerate(chart_retailers):
        rw = margin_data_row + 1 + i
        ws.cell(row=rw, column=2, value=r["name"])
        ws.cell(row=rw, column=3, value=r["gross_margin"]).number_format = NUM_FMT_PCT
        ws.cell(row=rw, column=4, value=r["gross_margin"] - r["structural_rate"]).number_format = NUM_FMT_PCT
        ws.cell(row=rw, column=5, value=r["net_net_margin"]).number_format = NUM_FMT_PCT

    margin_data_end = margin_data_row + len(chart_retailers)

    mchart = BarChart()
    mchart.type = "col"
    mchart.grouping = "clustered"
    mchart.title = "Margin Erosion by Retailer"
    mchart.y_axis.numFmt = '0%'
    mchart.width = 18
    mchart.height = 10

    cats2 = Reference(ws, min_col=2, min_row=margin_data_row + 1, max_row=margin_data_end)
    for col_idx in range(3, 6):
        series_data = Reference(ws, min_col=col_idx, min_row=margin_data_row, max_row=margin_data_end)
        mchart.add_data(series_data, titles_from_data=True)
    mchart.set_categories(cats2)
    mchart.series[0].graphicalProperties.solidFill = "70AD47"
    mchart.series[1].graphicalProperties.solidFill = "FFC000"
    mchart.series[2].graphicalProperties.solidFill = "2F5496"

    ws.add_chart(mchart, f"B{margin_data_end + 2}")

    # --- What-if trade rate inputs ---
    whatif_row = margin_data_end + 18
    ws.cell(row=whatif_row, column=2, value="What-If Trade Rate Scenario").font = FONT_SECTION

    whatif_row += 1
    ws.merge_cells(f"B{whatif_row}:G{whatif_row}")
    ws.cell(row=whatif_row, column=2,
            value="Enter target all-in trade rates below. Savings show annual impact of achieving target."
            ).font = FONT_SMALL

    whatif_row += 1
    whatif_headers = ["Retailer", "Revenue", "Current Rate", "Target Rate", "Trade at Target", "Current Trade", "Annual Savings"]
    for c, h in enumerate(whatif_headers, 2):
        cell = ws.cell(row=whatif_row, column=c, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True)
        cell.border = BORDER_THIN
        cell.alignment = ALIGN_CENTER

    dv = DataValidation(type="decimal", operator="between", formula1="0", formula2="0.5")
    dv.error = "Enter a rate between 0% and 50%"
    dv.errorTitle = "Invalid rate"
    ws.add_data_validation(dv)

    for i, r in enumerate(chart_retailers):
        rw = whatif_row + 1 + i

        ws.cell(row=rw, column=2, value=r["name"]).border = BORDER_THIN

        # Revenue (static)
        rev_cell = ws.cell(row=rw, column=3, value=r["revenue"])
        rev_cell.number_format = NUM_FMT_DOLLAR
        rev_cell.border = BORDER_THIN
        rev_cell.alignment = ALIGN_RIGHT

        # Current rate (static)
        cur_cell = ws.cell(row=rw, column=4, value=r["all_in_rate"])
        cur_cell.number_format = NUM_FMT_PCT
        cur_cell.border = BORDER_THIN
        cur_cell.alignment = ALIGN_CENTER

        # Target rate (input)
        target_cell = ws.cell(row=rw, column=5, value=r["all_in_rate"])
        target_cell.number_format = NUM_FMT_PCT
        target_cell.fill = FILL_INPUT
        target_cell.border = BORDER_THIN
        target_cell.alignment = ALIGN_CENTER
        target_cell.comment = Comment(
            "Enter a target all-in trade rate for this retailer. "
            "The savings column shows the annual impact of achieving this rate.",
            "System", width=260, height=60,
        )
        dv.add(target_cell)

        target_ref = f"F{rw}"
        rev_ref = f"C{rw}"

        # Trade at target = revenue × target rate (formula)
        ws.cell(row=rw, column=6, value=f"={rev_ref}*{target_ref}").number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=6).border = BORDER_THIN
        ws.cell(row=rw, column=6).alignment = ALIGN_RIGHT

        # Current trade (static)
        cur_trade = ws.cell(row=rw, column=7, value=r["all_in"])
        cur_trade.number_format = NUM_FMT_DOLLAR
        cur_trade.border = BORDER_THIN
        cur_trade.alignment = ALIGN_RIGHT

        # Annual savings = current trade - trade at target (formula)
        savings_ref = f"H{rw}"
        ws.cell(row=rw, column=8, value=f"=H{rw}-G{rw}").number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=8).border = BORDER_THIN
        ws.cell(row=rw, column=8).alignment = ALIGN_RIGHT

    # Fix: savings formula references need to be correct
    # Column layout: B=retailer, C=rev, D=current_rate, E=target_rate, F=trade_at_target, G=current_trade, H=savings
    # Let me rewrite the formula references correctly
    for i, r in enumerate(chart_retailers):
        rw = whatif_row + 1 + i
        # Trade at target = C{row} * E{row}
        ws.cell(row=rw, column=6, value=f"=C{rw}*E{rw}")
        # Savings = G{row} - F{row}
        ws.cell(row=rw, column=8, value=f"=G{rw}-F{rw}")
