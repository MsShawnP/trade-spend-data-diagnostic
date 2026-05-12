"""Tab 6: Deduction Code Crosswalk — reference mapping of retailer codes."""

import csv
from pathlib import Path

from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet

from workbook.styles import (
    ALIGN_CENTER,
    FONT_HEADER,
    FONT_SMALL,
)

COLUMNS = [
    ("Retailer", 20),
    ("Retailer Code", 13),
    ("Description", 36),
    ("Category", 16),
    ("Status", 10),
]


def _load_crosswalk(data_dir: Path) -> list[dict]:
    """Load deduction code crosswalk from CSV."""
    rows = []
    with open(data_dir / "deduction_codes.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def build_code_crosswalk(ws: Worksheet, data_dir: Path) -> None:
    rows = _load_crosswalk(data_dir)

    ws.sheet_view.showGridLines = False

    # --- Header ---
    ws.merge_cells("A1:E1")
    ws["A1"] = "Deduction Code Crosswalk"
    ws["A1"].font = FONT_HEADER

    ws.merge_cells("A2:E2")
    ws["A2"] = (
        "Maps retailer-specific deduction codes to plain-English descriptions "
        "and standardized categories. Used by the Deduction Ledger tab for code translation."
    )
    ws["A2"].font = FONT_SMALL

    # --- Column headers (row 4) ---
    header_row = 4
    header_font = Font(name="Calibri", size=10, bold=True)

    for c, (name, width) in enumerate(COLUMNS, 1):
        cell = ws.cell(row=header_row, column=c, value=name)
        cell.font = header_font
        cell.alignment = ALIGN_CENTER
        ws.column_dimensions[get_column_letter(c)].width = width

    ws.freeze_panes = "A5"

    # --- Data rows ---
    for i, row_data in enumerate(rows):
        rw = header_row + 1 + i

        ws.cell(row=rw, column=1, value=row_data["retailer_name"])
        c_code = ws.cell(row=rw, column=2, value=row_data["code"])
        c_code.alignment = ALIGN_CENTER
        ws.cell(row=rw, column=3, value=row_data["name"])
        ws.cell(row=rw, column=4, value=row_data["deduction_type"])
        c_status = ws.cell(row=rw, column=5, value=row_data["status"])
        c_status.alignment = ALIGN_CENTER

    table_end = header_row + len(rows)

    # --- Excel Table ---
    last_col = get_column_letter(len(COLUMNS))
    table_ref = f"A{header_row}:{last_col}{table_end}"

    style = TableStyleInfo(
        name="TableStyleMedium2", showFirstColumn=False,
        showLastColumn=False, showRowStripes=True, showColumnStripes=False,
    )
    table = Table(displayName="tbl_CodeCrosswalk", ref=table_ref)
    table.tableStyleInfo = style
    ws.add_table(table)

    # Conditional formatting on status column
    status_range = f"E{header_row + 1}:E{table_end}"
    ws.conditional_formatting.add(
        status_range,
        CellIsRule(operator="equal", formula=['"Verified"'],
                   fill=PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")),
    )
    ws.conditional_formatting.add(
        status_range,
        CellIsRule(operator="equal", formula=['"Inferred"'],
                   fill=PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")),
    )
