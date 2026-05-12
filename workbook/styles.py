"""Shared workbook styles used across tabs."""

from openpyxl.styles import Alignment, Border, Font, NamedStyle, PatternFill, Side

FONT_HEADER = Font(name="Calibri", size=14, bold=True)
FONT_SECTION = Font(name="Calibri", size=12, bold=True)
FONT_KPI_VALUE = Font(name="Calibri", size=18, bold=True)
FONT_KPI_LABEL = Font(name="Calibri", size=11)
FONT_BODY = Font(name="Calibri", size=11)
FONT_SMALL = Font(name="Calibri", size=10, italic=True, color="555555")
FONT_NAV = Font(name="Calibri", size=10, underline="single", color="0563C1")

FILL_INPUT = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")

BORDER_THIN = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

NUM_FMT_DOLLAR = '#,##0'
NUM_FMT_PCT = '0.0%'
