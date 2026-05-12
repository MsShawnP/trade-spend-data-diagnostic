"""Tab 4: Retailer Risk — net-net margin by retailer with what-if scenarios."""

import csv
from datetime import date
from pathlib import Path

from openpyxl.comments import Comment
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Font, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet

from workbook.styles import (
    ALIGN_CENTER,
    ALIGN_RIGHT,
    FILL_INPUT,
    FONT_BODY,
    FONT_HEADER,
    FONT_SECTION,
    FONT_SMALL,
    NUM_FMT_DOLLAR,
    NUM_FMT_PCT,
)

# Display order for the P&L table (channels first, then regionals)
DISPLAY_ORDER = [
    "Walmart", "UNFI", "Whole Foods", "Costco", "DTC",
    "Green Basket Market", "Southside Grocers",
    "Prairie Provisions", "Mountain Pantry Co", "Harbor Fresh",
]

TABLE_STYLE = TableStyleInfo(
    name="TableStyleMedium2", showFirstColumn=False,
    showLastColumn=False, showRowStripes=True, showColumnStripes=False,
)


def _row_to_dict(r, display_name=None):
    """Convert a CSV row dict to the retailer dict used by the build function."""
    return {
        "name": display_name or r["retailer_name"],
        "revenue": float(r["revenue"]),
        "rev_share": float(r["rev_share"]),
        "structural": float(r["structural_trade_dollars"]),
        "structural_rate": float(r["trade_rate"]),
        "op_deductions": float(r["op_deductions"]),
        "op_ded_rate": float(r["op_ded_rate"]),
        "pb_deductions": float(r["promo_billback"]),
        "all_in": float(r["all_in_trade"]),
        "all_in_rate": float(r["all_in_rate"]),
        "gross_margin": float(r["gross_margin"]),
        "net_net_margin": float(r["net_net_margin"]),
        "total_deductions": float(r["total_deductions"]),
        "ded_share": float(r["ded_share"]),
    }


def _load_retailer_data(data_dir: Path) -> dict:
    """Load retailer P&L data from dim_retailer.csv."""
    with open(data_dir / "computed_kpis.csv", encoding="utf-8") as f:
        kpi = next(csv.DictReader(f))

    all_rows = []
    with open(data_dir / "dim_retailer.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            all_rows.append(row)

    by_name = {r["retailer_name"]: r for r in all_rows}

    # Build ordered retailer list: channels + regionals in display order
    retailers = []
    for name in DISPLAY_ORDER:
        if name in by_name:
            retailers.append(_row_to_dict(by_name[name]))

    # Append distributors with deductions (e.g. KeHE)
    for r in all_rows:
        name = r["retailer_name"]
        if name not in DISPLAY_ORDER and float(r["total_deductions"]) > 0:
            display = f"{name} (distributor)" if r.get("channel_type") == "distributor" else name
            retailers.append(_row_to_dict(r, display_name=display))

    return {
        "retailers": retailers,
        "total_revenue": float(kpi["revenue"]),
        "oldest_week": kpi["oldest_week"],
        "max_scan": kpi["max_scan"],
    }


def build_retailer_risk(ws: Worksheet, data_dir: Path) -> None:
    data = _load_retailer_data(data_dir)
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

    # --- P&L summary table ---
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
        cell.alignment = ALIGN_CENTER

    table_start = row + 1
    for i, r in enumerate(retailers):
        rw = table_start + i

        ws.cell(row=rw, column=2, value=r["name"])

        c = ws.cell(row=rw, column=3, value=r["revenue"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=4, value=r["rev_share"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=5, value=r["structural"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=6, value=r["structural_rate"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=7, value=r["op_deductions"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=8, value=r["op_ded_rate"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=9, value=r["pb_deductions"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=10, value=r["all_in"])
        c.number_format = NUM_FMT_DOLLAR
        c.alignment = ALIGN_RIGHT

        c = ws.cell(row=rw, column=11, value=r["all_in_rate"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=12, value=r["gross_margin"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

        c = ws.cell(row=rw, column=13, value=r["net_net_margin"])
        c.number_format = NUM_FMT_PCT
        c.alignment = ALIGN_CENTER

    table_end = table_start + len(retailers) - 1

    # Excel Table for P&L
    pnl_table = Table(displayName="tbl_RetailerPnL", ref=f"B{row}:M{table_end}")
    pnl_table.tableStyleInfo = TABLE_STYLE
    ws.add_table(pnl_table)

    # Conditional formatting on net-net margin
    margin_range = f"M{table_start}:M{table_end}"
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
    ws.cell(row=whatif_row, column=2,
            value="Enter target all-in trade rates below. Savings show annual impact of achieving target."
            ).font = FONT_SMALL

    whatif_row += 1
    whatif_headers = ["Retailer", "Revenue", "Current Rate", "Target Rate",
                      "Trade at Target", "Current Trade", "Annual Savings", "What-If Margin"]
    for c, h in enumerate(whatif_headers, 2):
        cell = ws.cell(row=whatif_row, column=c, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True)
        cell.alignment = ALIGN_CENTER

    dv = DataValidation(type="decimal", operator="between", formula1="0", formula2="0.5")
    dv.errorStyle = "stop"
    dv.showErrorMessage = True
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

        # Trade at target = revenue * target rate
        ws.cell(row=rw, column=6, value=f"=C{rw}*E{rw}").number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=6).alignment = ALIGN_RIGHT

        cur_trade = ws.cell(row=rw, column=7, value=r["all_in"])
        cur_trade.number_format = NUM_FMT_DOLLAR
        cur_trade.alignment = ALIGN_RIGHT

        # Annual savings = current trade - trade at target
        # IF guard: when target rate (E) equals current rate (D), force zero
        # (the two computation paths produce small dollar gaps otherwise)
        ws.cell(row=rw, column=8, value=f"=IF(E{rw}=D{rw},0,ROUND(G{rw}-F{rw},0))").number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=8).alignment = ALIGN_RIGHT

        # What-if margin = gross_margin - target_rate
        gm_literal = f"{r['gross_margin']:.6f}"
        ws.cell(row=rw, column=9, value=f"={gm_literal}-E{rw}").number_format = NUM_FMT_PCT
        ws.cell(row=rw, column=9).alignment = ALIGN_CENTER
