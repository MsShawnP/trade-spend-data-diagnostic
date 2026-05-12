"""Tab 5: Deduction Ledger — full trailing-365 deduction log for investigation."""

import csv
from datetime import date
from pathlib import Path

from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet

from workbook.styles import (
    ALIGN_CENTER,
    ALIGN_RIGHT,
    FONT_HEADER,
    FONT_SMALL,
    NUM_FMT_DOLLAR,
)

COLUMNS = [
    ("Deduction ID", 14),
    ("Date", 11),
    ("Retailer", 16),
    ("Raw Code", 10),
    ("Translated Code", 30),
    ("Category", 14),
    ("Amount", 12),
    ("Order Ref", 12),
    ("Shipment Ref", 12),
    ("Remittance ID", 14),
    ("Remittance Desc", 24),
    ("Dispute Status", 14),
    ("Recovered", 11),
    ("Dispute Filed", 11),
    ("Dispute Closed", 12),
    ("Days Outstanding", 10),
    ("Deadline", 11),
    ("Vague", 6),
    ("Post-Audit", 9),
    ("Double-Dip", 9),
]

# Maps CSV column names to the 20-column display order
_CSV_FIELDS = [
    "deduction_id", "deduction_date", "retailer_id",
    "code_as_remitted", "translated_code", "deduction_type",
    "amount", "order_id", "shipment_id", "remittance_id",
    "remittance_description", "dispute_outcome", "recovered_amount",
    "dispute_filed_date", "dispute_closed_date", "days_outstanding",
    "dispute_deadline", "is_vague", "is_post_audit", "is_double_dip",
]


def _load_ledger(data_dir: Path) -> tuple[list[tuple], str, str]:
    """Load trailing-window deductions from fact_deductions.csv."""
    with open(data_dir / "computed_kpis.csv", encoding="utf-8") as f:
        kpi = next(csv.DictReader(f))
    oldest_week = kpi["oldest_week"]
    max_scan = kpi["max_scan"]

    rows = []
    with open(data_dir / "fact_deductions.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["in_trailing_window"] != "1":
                continue

            # Convert types to match what openpyxl expects
            amount = float(r["amount"]) if r["amount"] else 0
            recovered = float(r["recovered_amount"]) if r["recovered_amount"] else None
            days = int(r["days_outstanding"]) if r["days_outstanding"] else None

            rows.append((
                r["deduction_id"],
                r["deduction_date"],
                r["retailer_id"],
                r["code_as_remitted"] or None,
                r["translated_code"] or None,
                r["deduction_type"],
                amount,
                r["order_id"] or None,
                r["shipment_id"] or None,
                r["remittance_id"] or None,
                r["remittance_description"] or None,
                r["dispute_outcome"] or None,
                recovered,
                r["dispute_filed_date"] or None,
                r["dispute_closed_date"] or None,
                days,
                r["dispute_deadline"] or None,
                int(r["is_vague"]) if r["is_vague"] else 0,
                int(r["is_post_audit"]) if r["is_post_audit"] else 0,
                int(r["is_double_dip"]) if r["is_double_dip"] else 0,
            ))

    return rows, oldest_week, max_scan


def build_deduction_ledger(ws: Worksheet, data_dir: Path) -> None:
    rows, oldest_week, max_scan = _load_ledger(data_dir)

    ws.sheet_view.showGridLines = True

    # --- Header ---
    ws.merge_cells("A1:F1")
    ws["A1"] = "Deduction Ledger"
    ws["A1"].font = FONT_HEADER

    ws.merge_cells("A2:F2")
    ws["A2"] = (
        f"{len(rows):,} deductions  |  "
        f"Trailing 365 days ({oldest_week} to {max_scan})  |  "
        f"Built {date.today().isoformat()}"
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

    ws.freeze_panes = "B5"

    # --- Data rows ---
    for i, row_data in enumerate(rows):
        rw = header_row + 1 + i

        for c, val in enumerate(row_data, 1):
            ws.cell(row=rw, column=c, value=val)

        # Amount (col 7)
        ws.cell(row=rw, column=7).number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=7).alignment = ALIGN_RIGHT
        # Recovered (col 13)
        ws.cell(row=rw, column=13).number_format = NUM_FMT_DOLLAR
        ws.cell(row=rw, column=13).alignment = ALIGN_RIGHT
        # Days outstanding (col 16)
        ws.cell(row=rw, column=16).alignment = ALIGN_CENTER
        # Boolean flags (cols 18-20): show Yes/blank
        for flag_col in (18, 19, 20):
            cell = ws.cell(row=rw, column=flag_col)
            cell.value = "Yes" if cell.value == 1 else ""
            cell.alignment = ALIGN_CENTER

    # --- Excel Table ---
    last_col = get_column_letter(len(COLUMNS))
    table_end = header_row + len(rows)
    table_ref = f"A{header_row}:{last_col}{table_end}"

    style = TableStyleInfo(
        name="TableStyleMedium2", showFirstColumn=False,
        showLastColumn=False, showRowStripes=True, showColumnStripes=False,
    )
    table = Table(displayName="tbl_DeductionLedger", ref=table_ref)
    table.tableStyleInfo = style
    ws.add_table(table)
