"""Tab 3: Promo Efficacy — which promotions created value vs. destroyed it."""

import csv
from datetime import date
from pathlib import Path

from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Font, PatternFill, Protection
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

_HELPER_COL_START = 27
_MAX_WINDOW = 12

TABLE_STYLE = TableStyleInfo(
    name="TableStyleMedium2", showFirstColumn=False,
    showLastColumn=False, showRowStripes=True, showColumnStripes=False,
)


def _vol_or_none(val):
    """Convert CSV volume value to numeric or None."""
    if val is None or val == "":
        return None
    return float(val)


def _load_promo_data(data_dir: Path) -> dict:
    """Load promo performance data from dim_promo.csv + ghost_promos.csv."""
    with open(data_dir / "computed_kpis.csv", encoding="utf-8") as f:
        kpi = next(csv.DictReader(f))

    promos = []
    with open(data_dir / "dim_promo.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pre_volumes = [
                _vol_or_none(row.get(f"pre_vol_{i:02d}"))
                for i in range(1, _MAX_WINDOW + 1)
            ]
            during_volumes = [
                _vol_or_none(row.get(f"during_vol_{i:02d}"))
                for i in range(1, _MAX_WINDOW + 1)
            ]
            post_volumes = [
                _vol_or_none(row.get(f"post_vol_{i:02d}"))
                for i in range(1, _MAX_WINDOW + 1)
            ]

            # Trim trailing Nones from during (actual duration may be < 12)
            while during_volumes and during_volumes[-1] is None:
                during_volumes.pop()

            promos.append({
                "promo_id": row["promo_id"],
                "sku": row["sku"],
                "retailer": row["retailer"],
                "promo_type": row["promo_type"],
                "start_week": row["start_week"],
                "end_week": row["end_week"],
                "planned_cost": float(row["planned_cost"]) if row["planned_cost"] else None,
                "funding": row["funding_mechanism"],
                "actual_cost": float(row["actual_cost"]) if row["actual_cost"] else None,
                "asp": float(row["asp"]) if row["asp"] else None,
                "dur_wks": int(row["duration_weeks"]) if row["duration_weeks"] else None,
                "roi": float(row["roi"]) if row["roi"] else None,
                "pre_volumes": pre_volumes,
                "during_volumes": during_volumes,
                "post_volumes": post_volumes,
                "data_quality": row["data_quality"],
            })

    ghosts = []
    with open(data_dir / "ghost_promos.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ghosts.append(row)

    return {
        "promos": promos,
        "ghosts": ghosts,
        "ghost_count": int(kpi["ghost_promo_count"]),
        "ghost_total": float(kpi["ghost_promo_total"]),
        "total_promos": len(promos),
    }


def build_promo_efficacy(ws: Worksheet, data_dir: Path) -> None:
    data = _load_promo_data(data_dir)

    ws.sheet_view.showGridLines = False

    visible_widths = {
        1: 3, 2: 14, 3: 16, 4: 12, 5: 12, 6: 12, 7: 12,
        8: 12, 9: 12, 10: 12, 11: 12, 12: 12, 13: 13, 14: 12, 15: 10, 16: 12, 17: 10,
    }
    for col, w in visible_widths.items():
        ws.column_dimensions[get_column_letter(col)].width = w

    # --- Header (rows 1-3) ---
    ws.merge_cells("B1:N1")
    ws["B1"] = "Promo Efficacy"
    ws["B1"].font = FONT_HEADER

    ws.merge_cells("B2:N2")
    ws["B2"] = (
        "ROI calculated as simple pre/during/post volume comparison. "
        "This is not a causal model — see Methodology tab for assumptions and limitations."
    )
    ws["B2"].font = FONT_SMALL

    ws.merge_cells("B3:N3")
    ws["B3"] = f"Built {date.today().isoformat()}"
    ws["B3"].font = FONT_SMALL

    # --- Adjustable window input (row 5) ---
    ws.cell(row=5, column=2, value="Pre/post comparison window (weeks):").font = FONT_BODY
    window_cell = ws.cell(row=5, column=4, value=4)
    window_cell.fill = FILL_INPUT
    window_cell.alignment = ALIGN_CENTER
    window_cell.protection = Protection(locked=False)
    window_cell.comment = Comment(
        "Number of weeks before and after the promotion used to calculate baseline volume. "
        "Changing this value recalculates all ROI figures below.",
        "System", width=280, height=80,
    )
    window_ref = "$D$5"

    dv = DataValidation(type="whole", operator="between", formula1="1", formula2="12")
    dv.errorStyle = "stop"
    dv.showErrorMessage = True
    dv.error = "Enter an integer between 1 and 12"
    dv.errorTitle = "Invalid window"
    ws.add_data_validation(dv)
    dv.add(window_cell)

    # --- Coverage disclosure (row 7) ---
    full_ct = sum(1 for p in data["promos"] if p["data_quality"] == "Full")
    partial_ct = sum(1 for p in data["promos"] if p["data_quality"] == "Partial")
    no_pos_ct = sum(1 for p in data["promos"] if p["data_quality"] == "No POS")
    total_cost = sum(p["planned_cost"] or 0 for p in data["promos"])
    covered_cost = sum(p["planned_cost"] or 0 for p in data["promos"] if p["data_quality"] == "Full")

    ws.cell(row=7, column=2, value="Coverage Summary").font = FONT_SECTION
    ws.merge_cells("B8:N8")
    ws.cell(row=8, column=2, value=(
        f"Full POS data: {full_ct}/{data['total_promos']} promo-rows "
        f"({covered_cost/total_cost*100:.0f}% of planned spend covered)  |  "
        f"Partial: {partial_ct}  |  No POS: {no_pos_ct}"
    )).font = FONT_BODY

    # --- Performance table ---
    table_header_row = 10
    headers = [
        "Promo ID", "Retailer", "SKU", "Type", "Start", "End",
        "Planned $", "Actual $", "Pre Avg Vol", "During Avg Vol",
        "Post Avg Vol", "Incr. Volume", "Incr. Revenue", "ROI",
        "Funding", "Quality",
    ]
    for c, h in enumerate(headers, 2):
        cell = ws.cell(row=table_header_row, column=c, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True)
        cell.alignment = ALIGN_CENTER

    ws.freeze_panes = f"B{table_header_row + 1}"

    # Sort by pre-computed ROI (same order as original SQL-based version)
    def _sort_key(p):
        if p["data_quality"] == "No POS":
            return (2, 0)
        roi = p.get("roi")
        if roi is None:
            return (1, 0)
        return (0, -roi)

    sorted_promos = sorted(data["promos"], key=_sort_key)

    pre_start_col = _HELPER_COL_START
    during_start_col = pre_start_col + _MAX_WINDOW
    post_start_col = during_start_col + _MAX_WINDOW

    for col in range(pre_start_col, post_start_col + _MAX_WINDOW):
        ws.column_dimensions[get_column_letter(col)].hidden = True

    for i, promo in enumerate(sorted_promos):
        row = table_header_row + 1 + i

        ws.cell(row=row, column=2, value=promo["promo_id"])
        ws.cell(row=row, column=3, value=promo["retailer"])
        ws.cell(row=row, column=4, value=promo["sku"])
        ws.cell(row=row, column=5, value=promo["promo_type"])
        ws.cell(row=row, column=6, value=promo["start_week"])
        ws.cell(row=row, column=7, value=promo["end_week"])

        c_plan = ws.cell(row=row, column=8, value=promo["planned_cost"])
        c_plan.number_format = NUM_FMT_DOLLAR
        c_plan.alignment = ALIGN_RIGHT

        c_act = ws.cell(row=row, column=9, value=promo["actual_cost"])
        c_act.number_format = NUM_FMT_DOLLAR
        c_act.alignment = ALIGN_RIGHT

        # Write volume arrays to hidden columns
        for j, vol in enumerate(promo["pre_volumes"]):
            ws.cell(row=row, column=pre_start_col + j, value=vol if vol is not None else "")

        for j, vol in enumerate(promo["during_volumes"][:_MAX_WINDOW]):
            ws.cell(row=row, column=during_start_col + j, value=vol)

        for j, vol in enumerate(promo["post_volumes"]):
            ws.cell(row=row, column=post_start_col + j, value=vol if vol is not None else "")

        dur_wks = promo["dur_wks"] or 1
        asp = promo["asp"]

        if promo["data_quality"] == "No POS" or not asp:
            for col in range(10, 16):
                ws.cell(row=row, column=col, value=None)
        else:
            last_pre_col = get_column_letter(pre_start_col + _MAX_WINDOW - 1)
            pre_formula = f'=AVERAGE(OFFSET({last_pre_col}{row},0,1-{window_ref},1,{window_ref}))'
            c_pre = ws.cell(row=row, column=10, value=pre_formula)
            c_pre.number_format = '#,##0'
            c_pre.alignment = ALIGN_RIGHT

            during_range_start = get_column_letter(during_start_col)
            during_range_end = get_column_letter(during_start_col + min(dur_wks, _MAX_WINDOW) - 1)
            during_formula = f'=AVERAGE({during_range_start}{row}:{during_range_end}{row})'
            c_dur = ws.cell(row=row, column=11, value=during_formula)
            c_dur.number_format = '#,##0'
            c_dur.alignment = ALIGN_RIGHT

            first_post_col = get_column_letter(post_start_col)
            post_formula = f'=AVERAGE(OFFSET({first_post_col}{row},0,0,1,{window_ref}))'
            c_post = ws.cell(row=row, column=12, value=post_formula)
            c_post.number_format = '#,##0'
            c_post.alignment = ALIGN_RIGHT

            pre_ref = f"{get_column_letter(10)}{row}"
            dur_ref = f"{get_column_letter(11)}{row}"
            incr_vol_formula = f'=({dur_ref}-{pre_ref})*{dur_wks}'
            c_incr = ws.cell(row=row, column=13, value=incr_vol_formula)
            c_incr.number_format = '#,##0'
            c_incr.alignment = ALIGN_RIGHT

            incr_ref = f"{get_column_letter(13)}{row}"
            incr_rev_formula = f'={incr_ref}*{asp:.2f}'
            c_rev = ws.cell(row=row, column=14, value=incr_rev_formula)
            c_rev.number_format = NUM_FMT_DOLLAR
            c_rev.alignment = ALIGN_RIGHT

            rev_ref = f"{get_column_letter(14)}{row}"
            cost_ref = f"{get_column_letter(9)}{row}" if promo["actual_cost"] else f"{get_column_letter(8)}{row}"
            roi_formula = f'=IFERROR({rev_ref}/{cost_ref},"")'
            c_roi = ws.cell(row=row, column=15, value=roi_formula)
            c_roi.number_format = '0.0'
            c_roi.alignment = ALIGN_CENTER

        ws.cell(row=row, column=16, value=promo["funding"])

        c_qual = ws.cell(row=row, column=17, value=promo["data_quality"])
        c_qual.alignment = ALIGN_CENTER

    table_end_row = table_header_row + len(sorted_promos)

    # Excel Table
    table_ref = f"B{table_header_row}:Q{table_end_row}"
    promo_table = Table(displayName="tbl_PromoEfficacy", ref=table_ref)
    promo_table.tableStyleInfo = TABLE_STYLE
    ws.add_table(promo_table)

    # Conditional formatting on data quality (col Q = 17)
    qual_range = f"Q{table_header_row + 1}:Q{table_end_row}"
    ws.conditional_formatting.add(
        qual_range,
        CellIsRule(operator="equal", formula=['"Full"'],
                   fill=PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")),
    )
    ws.conditional_formatting.add(
        qual_range,
        CellIsRule(operator="equal", formula=['"Partial"'],
                   fill=PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")),
    )
    ws.conditional_formatting.add(
        qual_range,
        CellIsRule(operator="equal", formula=['"No POS"'],
                   fill=PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")),
    )

    # Conditional formatting on ROI (col O = 15): <1 red first, >=1 green second
    roi_range = f"O{table_header_row + 1}:O{table_end_row}"
    ws.conditional_formatting.add(
        roi_range,
        CellIsRule(operator="lessThan", formula=["1"],
                   stopIfTrue=True,
                   fill=PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")),
    )
    ws.conditional_formatting.add(
        roi_range,
        CellIsRule(operator="greaterThanOrEqual", formula=["1"],
                   stopIfTrue=True,
                   fill=PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")),
    )

    # --- Ghost promos section ---
    ghost_row = table_end_row + 3
    ws.cell(row=ghost_row, column=2, value="Ghost Promos — Deductions Without Matching Promotion").font = FONT_SECTION

    ghost_row += 1
    ws.merge_cells(f"B{ghost_row}:G{ghost_row}")
    ws.cell(row=ghost_row, column=2, value=(
        f"{data['ghost_count']} promo_billback deductions (${data['ghost_total']:,.0f}) "
        f"have no matching promotion in the calendar. Top 20 shown below."
    )).font = FONT_BODY

    ghost_row += 1
    ghost_headers = ["Deduction ID", "Retailer", "Amount", "Date"]
    for c, h in enumerate(ghost_headers, 2):
        cell = ws.cell(row=ghost_row, column=c, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True)

    for i, ghost in enumerate(data["ghosts"]):
        r = ghost_row + 1 + i
        ws.cell(row=r, column=2, value=ghost["deduction_id"])
        ws.cell(row=r, column=3, value=ghost["retailer_name"])
        c_a = ws.cell(row=r, column=4, value=float(ghost["amount"]))
        c_a.number_format = NUM_FMT_DOLLAR
        c_a.alignment = ALIGN_RIGHT
        ws.cell(row=r, column=5, value=ghost["deduction_date"])
