"""Tab 6: Deduction Code Crosswalk — reference mapping of retailer codes."""

from workbook.db import connect

from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table
from openpyxl.worksheet.worksheet import Worksheet

from workbook.deduction_taxonomy import get_taxonomy
from workbook.styles import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    FONT_HEADER,
    FONT_SMALL,
    TABLE_STYLE,
)

COLUMNS = [
    ("Retailer", 20),
    ("Retailer Code", 13),
    ("Description", 36),
    ("Category", 16),
    ("Taxonomy", 16),
    ("Status", 10),
]


def _query_crosswalk(database_url: str) -> list[tuple]:
    conn = connect()
    rows = conn.execute("""
        SELECT
            retailer_id,
            code,
            name,
            deduction_type,
            CASE WHEN is_published THEN 'Verified' ELSE 'Inferred' END
        FROM stg_deduction_codes
        ORDER BY retailer_id, deduction_type, code
    """).fetchall()
    conn.close()
    return rows


def build_code_crosswalk(ws: Worksheet, database_url: str) -> None:
    rows = _query_crosswalk(database_url)

    ws.sheet_view.showGridLines = False

    # --- Header ---
    ws.merge_cells("A1:F1")
    ws["A1"] = "Deduction Code Crosswalk"
    ws["A1"].font = FONT_HEADER

    ws.merge_cells("A2:F2")
    ws["A2"] = (
        "Maps retailer-specific deduction codes to plain-English descriptions "
        "and standardized categories. Used by the Deduction Ledger tab for code translation."
    )
    ws["A2"].font = FONT_SMALL
    ws["A2"].alignment = ALIGN_LEFT

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
        retailer, code, name, category, status = row_data

        ws.cell(row=rw, column=1, value=retailer.replace("_", " ").title())
        c_code = ws.cell(row=rw, column=2, value=code)
        c_code.alignment = ALIGN_CENTER
        ws.cell(row=rw, column=3, value=name)
        ws.cell(row=rw, column=4, value=category.replace("_", " ").title())
        ws.cell(row=rw, column=5, value=get_taxonomy(category)["bucket"])
        c_status = ws.cell(row=rw, column=6, value=status)
        c_status.alignment = ALIGN_CENTER

    table_end = header_row + len(rows)

    # --- Excel Table ---
    last_col = get_column_letter(len(COLUMNS))
    table_ref = f"A{header_row}:{last_col}{table_end}"

    table = Table(displayName="tbl_CodeCrosswalk", ref=table_ref)
    table.tableStyleInfo = TABLE_STYLE
    ws.add_table(table)

    # Conditional formatting on status column
    status_range = f"F{header_row + 1}:F{table_end}"
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
