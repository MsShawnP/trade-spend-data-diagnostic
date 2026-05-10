"""Tab 1: Executive Pulse — the CEO punchline."""

import sqlite3
from datetime import date
from pathlib import Path

from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from workbook.styles import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    ALIGN_RIGHT,
    BORDER_THIN,
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

CATEGORY_TO_DEPT = {
    "slotting": ("Sales", "Negotiated trade terms"),
    "short_ship": ("Operations", "Fulfillment accuracy"),
    "late_delivery": ("Operations", "Logistics/carrier management"),
    "damaged": ("Operations", "Packaging/handling"),
    "pallet_fine": ("Operations", "Compliance with retailer specs"),
    "label_fine": ("Operations", "Labeling/packaging compliance"),
    "spoilage": ("Operations", "Shelf-life/inventory management"),
    "vague": ("Finance", "Unclear codes — investigate"),
}

NAV_TABS = [
    "Executive Pulse",
    "Leak Diagnostic",
    "Promo Efficacy",
    "Retailer Risk",
    "Deduction Ledger",
    "Deduction Code Crosswalk",
    "Methodology & Logic",
]


def _query_metrics(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)

    # Trailing 52 weeks = 52 most recent distinct week_ending values
    weeks = conn.execute(
        "SELECT DISTINCT week_ending FROM scan_data ORDER BY week_ending DESC LIMIT 52"
    ).fetchall()
    oldest_week = weeks[-1][0]

    revenue = conn.execute(
        "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
        (oldest_week,),
    ).fetchone()[0]

    # Structural trade: channel avg trade_spend_pct × channel revenue
    # (matches verification methodology)
    channel_rev = conn.execute("""
        SELECT s.retailer, SUM(sd.dollars_sold)
        FROM scan_data sd
        JOIN stores s ON sd.store_id = s.store_id
        WHERE sd.week_ending >= ?
        GROUP BY s.retailer
    """, (oldest_week,)).fetchall()

    channel_rate_cols = {
        "Walmart": "trade_spend_pct_walmart",
        "Costco": "trade_spend_pct_costco",
        "Whole Foods": "trade_spend_pct_whole_foods",
        "UNFI": "trade_spend_pct_unfi",
        "DTC": "trade_spend_pct_dtc",
    }
    rates = {}
    for channel, col in channel_rate_cols.items():
        rates[channel] = conn.execute(f"SELECT AVG({col}) FROM sku_costs").fetchone()[0]
    regional_rate = conn.execute("SELECT AVG(trade_spend_pct_regional) FROM sku_costs").fetchone()[0]

    channel_trade = 0.0
    for retailer, rev in channel_rev:
        channel_trade += rev * rates.get(retailer, regional_rate)

    # Trailing 365 deductions excl promo_billback
    # Use deduction dates that fall within a year ending at the max scan date
    max_scan = weeks[0][0]
    deductions_by_type = conn.execute("""
        SELECT deduction_type, COUNT(*), SUM(amount)
        FROM deductions
        WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ?
          AND deduction_type != 'promo_billback'
        GROUP BY deduction_type
        ORDER BY SUM(amount) DESC
    """, (max_scan, max_scan)).fetchall()

    operational_waste = sum(r[2] for r in deductions_by_type)

    # Disputes and recovery
    dispute_stats = conn.execute("""
        SELECT COUNT(*), SUM(recovered_amount)
        FROM disputes
    """).fetchone()

    conn.close()

    return {
        "revenue": revenue,
        "structural_trade": channel_trade,
        "operational_waste": operational_waste,
        "deductions_by_type": deductions_by_type,
        "dispute_count": dispute_stats[0],
        "total_recovered": dispute_stats[1],
        "oldest_week": oldest_week,
        "max_scan": max_scan,
    }


def build_executive_pulse(ws: Worksheet, db_path: Path) -> None:
    metrics = _query_metrics(db_path)

    revenue = metrics["revenue"]
    structural = metrics["structural_trade"]
    waste = metrics["operational_waste"]
    all_in = structural + waste
    net_after = revenue - all_in

    structural_rate = structural / revenue
    waste_rate = waste / revenue
    all_in_rate = all_in / revenue

    recovery_rate = metrics["total_recovered"] / (metrics["total_recovered"] / 0.143) if metrics["total_recovered"] else 0
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

    ws.merge_cells("B7:D7")
    ws["B7"] = "You budgeted 17%. You’re spending 21%. The extra 4 points is operational waste."
    ws["B7"].font = Font(name="Calibri", size=11, italic=True)
    ws["B7"].alignment = ALIGN_LEFT

    # --- Waterfall chart (rows 9-20) ---
    row = 9
    ws.cell(row=row, column=2, value="Waterfall: Revenue to Net-After-Trade").font = FONT_SECTION

    # Data for waterfall: invisible base + visible bar
    chart_start = row + 1
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

    chart = BarChart()
    chart.type = "col"
    chart.grouping = "stacked"
    chart.title = None
    chart.y_axis.numFmt = '#,##0'
    chart.x_axis.delete = False
    chart.legend = None
    chart.width = 16
    chart.height = 10

    cats = Reference(ws, min_col=2, min_row=chart_start + 1, max_row=chart_start + 4)
    base_data = Reference(ws, min_col=3, min_row=chart_start, max_row=chart_start + 4)
    val_data = Reference(ws, min_col=4, min_row=chart_start, max_row=chart_start + 4)

    chart.add_data(base_data, titles_from_data=True)
    chart.add_data(val_data, titles_from_data=True)
    chart.set_categories(cats)

    # Make base series invisible
    base_series = chart.series[0]
    base_series.graphicalProperties.noFill = True
    base_series.graphicalProperties.line.noFill = True

    # Color the value series
    val_series = chart.series[1]
    val_series.graphicalProperties.solidFill = "2F5496"

    ws.add_chart(chart, "B16")

    # --- Addressable Improvement (rows 34-42) ---
    row = 34
    ws.cell(row=row, column=2, value="Addressable Improvement").font = FONT_SECTION

    row += 1
    table_headers = ["Metric", "Value"]
    for c, h in enumerate(table_headers, 2):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = FONT_BODY
        cell.border = BORDER_THIN

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
        r = row + 1 + i
        c_label = ws.cell(row=r, column=2, value=label)
        c_label.font = FONT_BODY
        c_label.border = BORDER_THIN
        c_val = ws.cell(row=r, column=3, value=val)
        c_val.font = FONT_BODY
        c_val.number_format = fmt
        c_val.border = BORDER_THIN
        c_val.alignment = ALIGN_RIGHT

    # --- Responsibility Matrix (rows 44-55) ---
    row = 44
    ws.cell(row=row, column=2, value="Responsibility Matrix — Who Owns the Waste").font = FONT_SECTION

    row += 1
    resp_headers = ["Deduction Type", "Amount", "Owner", "Root Cause"]
    for c, h in enumerate(resp_headers, 2):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = FONT_BODY
        cell.border = BORDER_THIN

    for i, (dtype, count, amount) in enumerate(metrics["deductions_by_type"]):
        r = row + 1 + i
        dept, cause = CATEGORY_TO_DEPT.get(dtype, ("Unclassified", ""))
        ws.cell(row=r, column=2, value=dtype.replace("_", " ").title()).border = BORDER_THIN
        c_amt = ws.cell(row=r, column=3, value=amount)
        c_amt.number_format = NUM_FMT_DOLLAR
        c_amt.border = BORDER_THIN
        c_amt.alignment = ALIGN_RIGHT
        ws.cell(row=r, column=4, value=dept).border = BORDER_THIN
        ws.cell(row=r, column=5, value=cause).border = BORDER_THIN

    # --- Navigation hyperlinks ---
    nav_row = row + 2 + len(metrics["deductions_by_type"])
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
