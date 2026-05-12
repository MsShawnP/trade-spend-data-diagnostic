"""End-to-end validation of the trade spend diagnostic workbook.

Validates workbook structure, locked numbers, cross-tab consistency,
and formatting. Uses computed CSVs as the reference data source.
"""

import csv
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.stdout.reconfigure(encoding="utf-8")

from openpyxl import load_workbook

OUTPUT = Path(__file__).resolve().parent / "output" / "trade_spend_diagnostic.xlsx"
DATA_DIR = Path(__file__).resolve().parent / "powerbi" / "data"

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name}")
        if detail:
            print(f"        {detail}")


def approx(a, b, tolerance=0.005):
    """Check if two numbers are approximately equal (within tolerance ratio)."""
    if b == 0:
        return a == 0
    return abs(a - b) / abs(b) < tolerance


def main():
    global PASS, FAIL

    print(f"Validating: {OUTPUT}")
    print(f"CSV dir:    {DATA_DIR}")
    print()

    wb = load_workbook(OUTPUT, data_only=False)

    # Load CSV reference data
    with open(DATA_DIR / "computed_kpis.csv", encoding="utf-8") as f:
        kpi = next(csv.DictReader(f))

    # === TAB STRUCTURE ===
    print("=== Tab Structure ===")
    expected_tabs = [
        "Executive Pulse", "Leak Diagnostic", "Promo Efficacy",
        "Retailer Risk", "Deduction Ledger", "Deduction Code Crosswalk",
        "Methodology & Logic",
    ]
    check("Tab count is 7", len(wb.sheetnames) == 7,
          f"Got {len(wb.sheetnames)}: {wb.sheetnames}")
    check("No default 'Sheet' tab", "Sheet" not in wb.sheetnames)
    check("Tab order correct", wb.sheetnames == expected_tabs,
          f"Got {wb.sheetnames}")
    check("Active sheet is Tab 1", wb.active.title == "Executive Pulse",
          f"Got {wb.active.title}")

    # Tab colors
    green_tabs = ["Executive Pulse", "Leak Diagnostic", "Promo Efficacy", "Retailer Risk"]
    for tab in green_tabs:
        color = wb[tab].sheet_properties.tabColor.rgb if wb[tab].sheet_properties.tabColor else ""
        check(f"{tab} is green", "00B050" in color, f"Got {color}")

    color = wb["Deduction Ledger"].sheet_properties.tabColor.rgb
    check("Deduction Ledger is blue", "4472C4" in color, f"Got {color}")

    for tab in ["Deduction Code Crosswalk", "Methodology & Logic"]:
        color = wb[tab].sheet_properties.tabColor.rgb if wb[tab].sheet_properties.tabColor else ""
        check(f"{tab} is gray", "A5A5A5" in color, f"Got {color}")

    # === LOCKED NUMBERS (Tab 1) ===
    print()
    print("=== Locked Numbers (Tab 1) ===")
    ws1 = wb["Executive Pulse"]

    revenue = ws1["D11"].value
    check("Revenue = $25,593,052", approx(revenue, 25593052),
          f"Got ${revenue:,.0f}")

    structural = ws1["D12"].value
    check("Structural trade = $4,435,052", approx(structural, 4435052),
          f"Got ${structural:,.0f}")

    waste = ws1["D13"].value
    check("Operational waste ≈ $1,010,940", approx(waste, 1010940, 0.002),
          f"Got ${waste:,.0f} (minor DB rebuild variance accepted)")

    all_in_rate = ws1["B5"].value
    check("All-in trade rate = 21.3%", approx(all_in_rate, 0.213, 0.005),
          f"Got {all_in_rate*100:.1f}%")

    structural_rate = ws1["C5"].value
    check("Structural trade rate = 17.3%", approx(structural_rate, 0.173, 0.005),
          f"Got {structural_rate*100:.1f}%")

    waste_rate = ws1["D5"].value
    check("Operational waste rate = 4.0%", approx(waste_rate, 0.040, 0.015),
          f"Got {waste_rate*100:.1f}%")

    # === DOUBLE-DIP CHECK (Tab 2) ===
    print()
    print("=== Double-Dip Check (Tab 2) ===")
    ws2 = wb["Leak Diagnostic"]

    dd_count = 0
    dd_total = 0
    for r in range(1, ws2.max_row + 1):
        cell = ws2.cell(row=r, column=2)
        if cell.value and str(cell.value).startswith("DED-"):
            if r > 15:
                dd_count += 1
                dd_total += ws2.cell(row=r, column=4).value or 0

    check("3 double-dip events", dd_count == 3, f"Got {dd_count}")
    check("Double-dip total ≈ $19,306", approx(dd_total, 19306),
          f"Got ${dd_total:,.0f}")

    # === RECOVERY CHECK (from CSV) ===
    print()
    print("=== Recovery Check ===")
    csv_dispute_count = int(kpi["dispute_count"])
    csv_recovered = float(kpi["total_recovered"])
    check("Disputes ~ 1,409", abs(csv_dispute_count - 1409) <= 2, f"Got {csv_dispute_count}")
    check("Recovered ≈ $98,216", approx(csv_recovered, 98216),
          f"Got ${csv_recovered:,.0f}")

    # === RETAILER TOTALS (Tab 4) ===
    print()
    print("=== Retailer Totals (Tab 4) ===")
    ws4 = wb["Retailer Risk"]

    retailer_rev_sum = 0
    retailer_struct_sum = 0
    for r in range(6, 17):
        rev = ws4.cell(row=r, column=3).value or 0
        struct = ws4.cell(row=r, column=5).value or 0
        retailer_rev_sum += rev
        retailer_struct_sum += struct

    check("Tab 4 revenue sums to total", approx(retailer_rev_sum, revenue),
          f"Got ${retailer_rev_sum:,.0f} vs ${revenue:,.0f}")
    check("Tab 4 structural sums to total", approx(retailer_struct_sum, structural),
          f"Got ${retailer_struct_sum:,.0f} vs ${structural:,.0f}")

    # === DEDUCTION COUNT (Tab 5, from CSV) ===
    print()
    print("=== Deduction Count (Tab 5) ===")
    ws5 = wb["Deduction Ledger"]

    csv_trailing_count = 0
    with open(DATA_DIR / "fact_deductions.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["in_trailing_window"] == "1":
                csv_trailing_count += 1

    ledger_rows = 0
    for r in range(5, ws5.max_row + 1):
        if ws5.cell(row=r, column=1).value:
            ledger_rows += 1
        else:
            break

    check(f"Tab 5 rows match CSV ({csv_trailing_count})", ledger_rows == csv_trailing_count,
          f"Tab 5 has {ledger_rows} rows, CSV has {csv_trailing_count}")

    # === CROSSWALK COMPLETENESS (Tab 6) ===
    print()
    print("=== Crosswalk Completeness (Tab 6) ===")
    ws6 = wb["Deduction Code Crosswalk"]

    tab5_retailers = set()
    for r in range(5, 5 + ledger_rows):
        ret = ws5.cell(row=r, column=3).value
        if ret:
            tab5_retailers.add(ret.lower().replace(" ", "_"))

    tab6_retailers = set()
    for r in range(5, ws6.max_row + 1):
        ret = ws6.cell(row=r, column=1).value
        if ret:
            tab6_retailers.add(ret.lower().replace(" ", "_"))

    missing = tab5_retailers - tab6_retailers
    check("Tab 6 covers all Tab 5 retailers", len(missing) == 0,
          f"Missing: {missing}" if missing else "")

    # === CROSS-TAB CONSISTENCY ===
    print()
    print("=== Cross-Tab Consistency ===")

    tab2_cat_total = 0
    for r in range(6, 14):
        amt = ws2.cell(row=r, column=4).value
        if isinstance(amt, (int, float)):
            tab2_cat_total += amt

    check("Tab 2 categories sum ≈ Tab 1 waste", approx(tab2_cat_total, waste),
          f"Tab 2 sum: ${tab2_cat_total:,.0f} vs Tab 1: ${waste:,.0f}")

    check("Tab 4 rev sum = Tab 1 revenue", approx(retailer_rev_sum, revenue),
          f"${retailer_rev_sum:,.0f} vs ${revenue:,.0f}")

    # === NO ERRORS ===
    print()
    print("=== Error Scan ===")
    error_values = {"#N/A", "#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!"}
    errors_found = []
    for tab_name in wb.sheetnames:
        ws = wb[tab_name]
        for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 300), values_only=False):
            for cell in row:
                if cell.value and str(cell.value) in error_values:
                    errors_found.append(f"{tab_name}!{cell.coordinate}: {cell.value}")

    check("No #N/A, #REF, #VALUE errors", len(errors_found) == 0,
          f"Found: {errors_found[:5]}" if errors_found else "")

    # === NAMED RANGES ===
    print()
    print("=== Named Ranges ===")
    expected_names = [
        "AllInTradeRate", "StructuralTradeRate", "OperationalWasteRate",
        "TotalRevenue", "StructuralTrade", "OperationalWaste",
        "AllInTradeCost", "RecoveryRate",
        "KPI_AllInTradeRate", "KPI_PlannedTradeRate", "KPI_OperationalWaste",
        "KPI_Revenue", "KPI_StructuralTrade", "KPI_OpWasteAmount",
    ]
    defined = [dn.name for dn in wb.defined_names.values()]
    for name in expected_names:
        check(f"Named range '{name}' defined", name in defined,
              f"Defined names: {defined}" if name not in defined else "")

    # === EXCEL TABLES ===
    print()
    print("=== Excel Tables ===")
    expected_tables = {
        "Executive Pulse": ["tbl_AddressableImprovement", "tbl_ResponsibilityMatrix"],
        "Leak Diagnostic": ["tbl_WasteByCategory", "tbl_DoubleDips"],
        "Promo Efficacy": ["tbl_PromoEfficacy"],
        "Retailer Risk": ["tbl_RetailerPnL", "tbl_ConcentrationRisk"],
        "Deduction Ledger": ["tbl_DeductionLedger"],
        "Deduction Code Crosswalk": ["tbl_CodeCrosswalk"],
    }
    for tab_name, table_names in expected_tables.items():
        ws = wb[tab_name]
        actual_tables = [t.displayName for t in ws.tables.values()]
        for tbl in table_names:
            check(f"Table '{tbl}' in {tab_name}", tbl in actual_tables,
                  f"Found tables: {actual_tables}" if tbl not in actual_tables else "")

    # === DATA VALIDATION ===
    print()
    print("=== Data Validation ===")
    ws2_dvs = ws2.data_validations.dataValidation
    check("Tab 2 has data validation", len(ws2_dvs) > 0,
          f"Found {len(ws2_dvs)} validations")

    ws3 = wb["Promo Efficacy"]
    ws3_dvs = ws3.data_validations.dataValidation
    check("Tab 3 has data validation", len(ws3_dvs) > 0,
          f"Found {len(ws3_dvs)} validations")

    ws4_dvs = ws4.data_validations.dataValidation
    check("Tab 4 has data validation", len(ws4_dvs) > 0,
          f"Found {len(ws4_dvs)} validations")

    # === CONDITIONAL FORMATTING ===
    print()
    print("=== Conditional Formatting ===")
    ws1_cf = list(ws1.conditional_formatting)
    check("Tab 1 has conditional formatting (data bars)", len(ws1_cf) >= 4,
          f"Found {len(ws1_cf)} rules")

    ws2_cf = list(ws2.conditional_formatting)
    check("Tab 2 has conditional formatting", len(ws2_cf) > 0,
          f"Found {len(ws2_cf)} rules")

    ws3_cf = list(ws3.conditional_formatting)
    check("Tab 3 has conditional formatting (ROI + quality)", len(ws3_cf) >= 2,
          f"Found {len(ws3_cf)} ranges")

    ws4_cf = list(ws4.conditional_formatting)
    check("Tab 4 has conditional formatting (margin)", len(ws4_cf) > 0,
          f"Found {len(ws4_cf)} ranges")

    ws6_cf = list(ws6.conditional_formatting)
    check("Tab 6 has conditional formatting (verified/inferred)", len(ws6_cf) > 0,
          f"Found {len(ws6_cf)} ranges")

    # === SUMMARY ===
    print()
    print("=" * 50)
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    if FAIL == 0:
        print("All checks passed.")
    else:
        print("SOME CHECKS FAILED — see details above.")
    print("=" * 50)

    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
