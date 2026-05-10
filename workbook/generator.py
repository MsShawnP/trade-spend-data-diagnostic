"""Generate the trade spend diagnostic workbook."""

from pathlib import Path

from openpyxl import Workbook

from workbook.tab_code_crosswalk import build_code_crosswalk
from workbook.tab_deduction_ledger import build_deduction_ledger
from workbook.tab_executive_pulse import build_executive_pulse
from workbook.tab_leak_diagnostic import build_leak_diagnostic
from workbook.tab_methodology import build_methodology
from workbook.tab_promo_efficacy import build_promo_efficacy
from workbook.tab_retailer_risk import build_retailer_risk


TAB_SPEC = [
    ("Executive Pulse", "228B22"),
    ("Leak Diagnostic", "228B22"),
    ("Promo Efficacy", "228B22"),
    ("Retailer Risk", "228B22"),
    ("Deduction Ledger", "4472C4"),
    ("Deduction Code Crosswalk", "808080"),
    ("Methodology & Logic", "808080"),
]


def generate_workbook(db_path: Path, output_path: Path) -> Path:
    wb = Workbook()
    wb.remove(wb.active)

    for name, color in TAB_SPEC:
        ws = wb.create_sheet(title=name)
        ws.sheet_properties.tabColor = color

    build_executive_pulse(wb["Executive Pulse"], db_path)
    build_leak_diagnostic(wb["Leak Diagnostic"], db_path)
    build_promo_efficacy(wb["Promo Efficacy"], db_path)
    build_retailer_risk(wb["Retailer Risk"], db_path)
    build_deduction_ledger(wb["Deduction Ledger"], db_path)
    build_code_crosswalk(wb["Deduction Code Crosswalk"], db_path)
    build_methodology(wb["Methodology & Logic"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path
