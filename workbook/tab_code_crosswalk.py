"""Tab 6: Deduction Code Crosswalk — reference mapping of retailer codes."""

import sqlite3
from pathlib import Path

from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from workbook.styles import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    BORDER_THIN,
    FONT_HEADER,
    FONT_SMALL,
)

FILL_ALT_ROW = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

COLUMNS = [
    ("Retailer", 20),
    ("Retailer Code", 13),
    ("Description", 36),
    ("Category", 16),
    ("Status", 10),
]


def _query_crosswalk(db_path: Path) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT
            retailer_id,
            code,
            name,
            deduction_type,
            CASE WHEN is_published = 1 THEN 'Verified' ELSE 'Inferred' END
        FROM deduction_codes
        ORDER BY retailer_id, deduction_type, code
    """).fetchall()
    conn.close()
    return rows


def build_code_crosswalk(ws: Worksheet, db_path: Path) -> None:
    rows = _query_crosswalk(db_path)

    ws.sheet_view.showGridLines = True

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
        cell.border = BORDER_THIN
        cell.alignment = ALIGN_CENTER
        ws.column_dimensions[get_column_letter(c)].width = width

    ws.freeze_panes = "A5"

    last_col = get_column_letter(len(COLUMNS))
    ws.auto_filter.ref = f"A{header_row}:{last_col}{header_row + len(rows)}"

    # --- Data rows ---
    for i, row_data in enumerate(rows):
        rw = header_row + 1 + i
        alt_fill = FILL_ALT_ROW if i % 2 == 1 else None

        retailer, code, name, category, status = row_data

        cell = ws.cell(row=rw, column=1, value=retailer.replace("_", " ").title())
        cell.border = BORDER_THIN
        if alt_fill:
            cell.fill = alt_fill

        cell = ws.cell(row=rw, column=2, value=code)
        cell.border = BORDER_THIN
        cell.alignment = ALIGN_CENTER
        if alt_fill:
            cell.fill = alt_fill

        cell = ws.cell(row=rw, column=3, value=name)
        cell.border = BORDER_THIN
        if alt_fill:
            cell.fill = alt_fill

        cell = ws.cell(row=rw, column=4, value=category.replace("_", " ").title())
        cell.border = BORDER_THIN
        if alt_fill:
            cell.fill = alt_fill

        cell = ws.cell(row=rw, column=5, value=status)
        cell.border = BORDER_THIN
        cell.alignment = ALIGN_CENTER
        if alt_fill:
            cell.fill = alt_fill

    table_end = header_row + len(rows)

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
