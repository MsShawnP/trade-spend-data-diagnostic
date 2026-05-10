"""Generate the trade spend diagnostic workbook."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import PatternFill


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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path
