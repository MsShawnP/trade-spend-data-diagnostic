"""Tab 1: Executive Pulse — the CEO punchline."""

import csv
from datetime import date
from pathlib import Path

from openpyxl.formatting.rule import DataBarRule
from openpyxl.styles import Border, Font, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet

from workbook.styles import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    ALIGN_RIGHT,
    FONT_BODY,
    FONT_HEADER,
    FONT_KPI_LABEL,
    FONT_KPI_VALUE,
    FONT_NAV,
    FONT_SECTION,
    FONT_SMALL,
    NUM_FMT_DOLLAR,
    NUM_FMT_PCT,
)

NAV_TABS = [
    "Executive Pulse",
    "Leak Diagnostic",
    "Promo Efficacy",
    "Retailer Risk",
    "Deduction Ledger",
    "Deduction Code Crosswalk",
    "Methodology & Logic",
]

TABLE_STYLE = TableStyleInfo(
    name="TableStyleMedium2", showFirstColumn=False,
    showLastColumn=False, showRowStripes=True, showColumnStripes=False,
)


def _load_data(data_dir: Path) -> dict:
    """Load pre-computed KPIs and waste categories from CSVs."""
    with open(data_dir / "computed_kpis.csv", encoding="utf-8") as f:
        kpi = next(csv.DictReader(f))

    categories = []
    with open(data_dir / "waste_by_category.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            categories.append(row)

    return {
        "revenue": float(kpi["revenue"]),
        "structural_trade": float(kpi["structural_trade"]),
        "operational_waste": float(kpi["operational_waste"]),
        "categories": categories,
        "total_recovered": float(kpi["total_recovered"]),
        "recovery_rate": float(kpi["recovery_rate"]),
        "oldest_week": kpi["oldest_week"],
        "max_scan": kpi["max_scan"],
    }


def build_executive_pulse(ws: Worksheet, data_dir: Path) -> None:
    metrics = _load_data(data_dir)

    revenue = metrics["revenue"]
    structural = metrics["structural_trade"]
    waste = metrics["operational_waste"]
    all_in = structural + waste
    net_after = revenue - all_in

    structural_rate = structural / revenue
    waste_rate = waste / revenue
    all_in_rate = all_in / revenue

    recovery_rate = metrics["recovery_rate"]
    total_recovered = metrics["total_recovered"]

    ws.sheet_view.showGridLines = False

    col_widths = [3, 22, 18, 18, 18, 18, 14]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # --- Header block (rows 1-3) ---
    ws.merge_cells("B1:F1")
    ws["B1"] = "Cinderhaven Provisions"
    ws["B1"].font = FONT_HEADER

    ws.merge_cells("B2:F2")
    ws["B2"] = "Executive Pulse — Trade Spend Diagnostic"
    ws["B2"].font = FONT_SECTION

    ws.merge_cells("B3:F3")
    ws["B3"] = f"Trailing 52 weeks ({metrics['oldest_week']} to {metrics['max_scan']})  |  Built {date.today().isoformat()}"
    ws["B3"].font = FONT_SMALL

    # --- KPI trio (rows 5-7) ---
    kpis = [
        ("All-In Trade Rate", all_in_rate),
        ("Planned Trade Rate", structural_rate),
        ("Operational Waste", waste_rate),
    ]
    for col_idx, (label, value) in enumerate(kpis, 2):
        cell_val = ws.cell(row=5, column=col_idx, value=value)
        cell_val.font = FONT_KPI_VALUE
        cell_val.number_format = NUM_FMT_PCT
        cell_val.alignment = ALIGN_CENTER

        cell_lbl = ws.cell(row=6, column=col_idx, value=label)
        cell_lbl.font = FONT_KPI_LABEL
        cell_lbl.alignment = ALIGN_CENTER

    ws.merge_cells("B7:F7")
    ws["B7"] = "You budgeted 17%. You're spending 21%. The extra 4 points is operational waste."
    ws["B7"].font = Font(name="Calibri", size=11, italic=True)
    ws["B7"].alignment = ALIGN_LEFT

    section_sep = Border(bottom=Side(style="thin", color="CCCCCC"))
    for col in range(2, 7):
        ws.cell(row=8, column=col).border = section_sep

    # --- Hidden source data (rows 10-14) for named ranges ---
    ws.cell(row=9, column=2, value="Waterfall: Revenue to Net-After-Trade").font = FONT_SECTION

    chart_start = 10
    headers = ["Category", "Base", "Value"]
    for c, h in enumerate(headers, 2):
        ws.cell(row=chart_start, column=c, value=h).font = FONT_BODY

    waterfall_data = [
        ("Revenue", 0, revenue),
        ("Structural Trade", net_after + waste, structural),
        ("Operational Waste", net_after, waste),
        ("Net After Trade", 0, net_after),
    ]
    for i, (cat, base, val) in enumerate(waterfall_data):
        r = chart_start + 1 + i
        ws.cell(row=r, column=2, value=cat)
        ws.cell(row=r, column=3, value=base).number_format = NUM_FMT_DOLLAR
        ws.cell(row=r, column=4, value=val).number_format = NUM_FMT_DOLLAR

    for r in range(chart_start, chart_start + 5):
        ws.row_dimensions[r].hidden = True

    # --- In-cell waterfall (rows 16-19) ---
    waterfall_visible = [
        ("Revenue", f"=D{chart_start + 1}", "2F5496"),
        ("Structural Trade", f"=D{chart_start + 2}", "ED7D31"),
        ("Operational Waste", f"=D{chart_start + 3}", "C00000"),
        ("Net After Trade", f"=D{chart_start + 4}", "2F5496"),
    ]
    for i, (label, formula, color) in enumerate(waterfall_visible):
        r = 16 + i
        ws.cell(row=r, column=2, value=label).font = FONT_BODY
        val_cell = ws.cell(row=r, column=4, value=formula)
        val_cell.number_format = NUM_FMT_DOLLAR
        val_cell.alignment = ALIGN_RIGHT

        ws.conditional_formatting.add(
            f"D{r}",
            DataBarRule(
                start_type="num", start_value=0,
                end_type="num", end_value=revenue,
                color=color,
            ),
        )

    for col in range(2, 7):
        ws.cell(row=21, column=col).border = section_sep

    # --- Addressable Improvement (rows 22-30) ---
    ws.cell(row=22, column=2, value="Addressable Improvement").font = FONT_SECTION

    imp_header_row = 23
    imp_headers = ["Metric", "Value"]
    for c, h in enumerate(imp_headers, 2):
        cell = ws.cell(row=imp_header_row, column=c, value=h)
        cell.font = FONT_BODY
        cell.alignment = ALIGN_CENTER

    improvement_rows = [
        ("Operational waste (trailing 365d)", waste, NUM_FMT_DOLLAR),
        ("Current recovery rate", recovery_rate, NUM_FMT_PCT),
        ("Currently recovered", total_recovered, NUM_FMT_DOLLAR),
        ("At 30% recovery", waste * 0.30, NUM_FMT_DOLLAR),
        ("At 50% recovery", waste * 0.50, NUM_FMT_DOLLAR),
        ("Incremental at 30% vs. current", waste * 0.30 - total_recovered, NUM_FMT_DOLLAR),
        ("Incremental at 50% vs. current", waste * 0.50 - total_recovered, NUM_FMT_DOLLAR),
    ]
    for i, (label, val, fmt) in enumerate(improvement_rows):
        r = imp_header_row + 1 + i
        ws.cell(row=r, column=2, value=label).font = FONT_BODY
        c_val = ws.cell(row=r, column=3, value=val)
        c_val.font = FONT_BODY
        c_val.number_format = fmt
        c_val.alignment = ALIGN_RIGHT

    imp_end_row = imp_header_row + len(improvement_rows)

    imp_table = Table(displayName="tbl_AddressableImprovement", ref=f"B{imp_header_row}:C{imp_end_row}")
    imp_table.tableStyleInfo = TABLE_STYLE
    ws.add_table(imp_table)

    for col in range(2, 7):
        ws.cell(row=imp_end_row + 1, column=col).border = section_sep

    # --- Responsibility Matrix (rows 32+) ---
    resp_title_row = imp_end_row + 2
    ws.cell(row=resp_title_row, column=2, value="Responsibility Matrix — Who Owns the Waste").font = FONT_SECTION

    resp_header_row = resp_title_row + 1
    resp_headers = ["Deduction Type", "Amount", "Owner", "Root Cause"]
    for c, h in enumerate(resp_headers, 2):
        cell = ws.cell(row=resp_header_row, column=c, value=h)
        cell.font = FONT_BODY
        cell.alignment = ALIGN_CENTER

    for i, cat in enumerate(metrics["categories"]):
        r = resp_header_row + 1 + i
        ws.cell(row=r, column=2, value=cat["label"])
        c_amt = ws.cell(row=r, column=3, value=float(cat["total_amount"]))
        c_amt.number_format = NUM_FMT_DOLLAR
        c_amt.alignment = ALIGN_RIGHT
        ws.cell(row=r, column=4, value=cat["owner"])
        ws.cell(row=r, column=5, value=cat["root_cause"])

    resp_end_row = resp_header_row + len(metrics["categories"])

    resp_table = Table(displayName="tbl_ResponsibilityMatrix", ref=f"B{resp_header_row}:E{resp_end_row}")
    resp_table.tableStyleInfo = TABLE_STYLE
    ws.add_table(resp_table)

    # --- Navigation hyperlinks ---
    nav_row = resp_end_row + 2
    ws.cell(row=nav_row, column=2, value="Navigate to:").font = FONT_SECTION

    nav_row += 1
    for i, tab_name in enumerate(NAV_TABS):
        cell = ws.cell(row=nav_row, column=2 + i, value=tab_name)
        cell.font = FONT_NAV
        cell.hyperlink = f"#'{tab_name}'!A1"

    # --- Instructional callout ---
    callout_row = nav_row + 2
    ws.merge_cells(f"B{callout_row}:F{callout_row}")
    callout = ws.cell(
        row=callout_row, column=2,
        value=(
            "This workbook summarizes trailing-12-month trade spend for Cinderhaven Provisions. "
            "Green tabs are analysis. Blue tab is the full deduction ledger. "
            "Gray tabs are reference. Yellow cells are adjustable inputs."
        ),
    )
    callout.font = FONT_SMALL
    callout.alignment = ALIGN_LEFT
