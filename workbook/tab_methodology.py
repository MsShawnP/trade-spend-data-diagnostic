"""Tab 7: Methodology & Logic — self-contained documentation of all calculations."""

from datetime import date

from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from workbook.styles import FONT_HEADER, FONT_SECTION, FONT_SMALL

_BODY_FONT = Font(name="Calibri", size=11)
_WRAP = Alignment(vertical="top", wrap_text=True)
_LABEL_FONT = Font(name="Calibri", size=11, bold=True)


def _write_section(ws: Worksheet, row: int, title: str) -> int:
    ws.cell(row=row, column=1, value=title).font = FONT_SECTION
    return row + 1


def _write_body(ws: Worksheet, row: int, text: str) -> int:
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = _BODY_FONT
    cell.alignment = _WRAP
    return row + 1


def _write_pair(ws: Worksheet, row: int, label: str, text: str) -> int:
    c1 = ws.cell(row=row, column=1, value=label)
    c1.font = _LABEL_FONT
    c1.alignment = Alignment(vertical="top")
    c2 = ws.cell(row=row, column=2, value=text)
    c2.font = _BODY_FONT
    c2.alignment = _WRAP
    return row + 1


def build_methodology(ws: Worksheet) -> None:
    ws.sheet_view.showGridLines = False

    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 90

    # --- Header ---
    row = 1
    ws.merge_cells("A1:B1")
    ws["A1"] = "Methodology & Logic"
    ws["A1"].font = FONT_HEADER

    row = 2
    ws["A2"] = f"Build date: {date.today().isoformat()}"
    ws["A2"].font = FONT_SMALL

    # === TWO-BUCKET DEFINITION ===
    row = 4
    row = _write_section(ws, row, "1. Two-Bucket Executive Framing")
    row = _write_body(ws, row,
        "This workbook uses a two-bucket model to present trade spend:")
    row += 1
    row = _write_pair(ws, row, "Bucket 1: Structural Trade",
        "The negotiated rate-card discount embedded in wholesale pricing by channel. "
        "Derived from sku_costs.trade_spend_pct columns multiplied by channel revenue. "
        "This is the planned cost of doing business with each retailer — it exists "
        "whether or not a single deduction is ever taken. $4,435,052 (17.3% of revenue).")
    row = _write_pair(ws, row, "Bucket 2: Operational Waste",
        "Trailing-365-day deductions excluding promo_billback. These are unplanned cash "
        "outflows from compliance failures (label fines, pallet fines), logistics issues "
        "(short ships, late deliveries, damages), spoilage, and vague/unclassified codes. "
        "$1,010,940 (4.0% of revenue).")
    row += 1
    row = _write_pair(ws, row, "Why not three buckets?",
        "The original brief proposed a third \"promotional\" bucket using off-invoice discounts. "
        "Investigation revealed that off-invoice is a funding mechanism, not a cost category — "
        "including it as a separate bucket double-counts costs already captured in the structural "
        "trade rate. The promotions table's promo_cost sum ($20.5K) is too small to constitute "
        "a meaningful standalone bucket. Two buckets tell a cleaner story: you budgeted 17%, "
        "you're spending 21%, the extra 4 points is operational waste.")
    row = _write_pair(ws, row, "Promo billback exclusion",
        "Promo_billback deductions ($211,513 trailing-365) are excluded from the operational "
        "waste bucket because they represent planned promotional activity, not operational failures. "
        "They appear on the Deduction Ledger tab but do not inflate the waste figure.")

    # === DATA LINEAGE ===
    row += 1
    row = _write_section(ws, row, "2. Data Lineage")
    row = _write_body(ws, row,
        "All data originates from the Cinderhaven Postgres data platform (staging tables prefixed stg_). "
        "21 tables covering scan data, costs, deductions, promotions, stores, retailers, and disputes.")
    row += 1
    row = _write_pair(ws, row, "scan_data",
        "Point-of-sale weekly volumes and dollar sales by SKU and store. "
        "104 weeks (2024-05-11 to 2026-05-02). Used for revenue calculations (trailing 52 weeks = "
        "52 most recent distinct week_ending values) and promotion lift analysis.")
    row = _write_pair(ws, row, "sku_costs",
        "Per-SKU cost structure: COGS, wholesale prices by channel, trade spend percentages by channel. "
        "Static reference table. Used for structural trade rate calculation and gross margin derivation.")
    row = _write_pair(ws, row, "deductions",
        "3,087 deduction records (2024-07-04 to 2026-05-02). Each record: retailer, type, amount, date, "
        "codes, flags (vague, post-audit, double-dip). Trailing-365 filter applied for operational waste "
        "calculations. Joined to deduction_codes for translations and to disputes for recovery data.")
    row = _write_pair(ws, row, "promotions",
        "188 promotion rows across 75 distinct events. Fields: SKU, retailer, date window, promo type, "
        "promo_cost, funding_mechanism. Coverage: not all promotions have matched POS data. "
        "Limitation: promo calendar may be incomplete — ghost promo analysis identifies deductions "
        "that reference promotions not in this table.")
    row = _write_pair(ws, row, "deduction_codes",
        "97 retailer-specific code entries mapping raw remittance codes to plain-English descriptions "
        "and standardized categories. 19 verified from vendor guides, 78 inferred via pattern matching. "
        "292 deduction records in the trailing-365 window have no matching crosswalk entry.")
    row = _write_pair(ws, row, "disputes",
        "~1,410 dispute records with outcome, recovered amount, filed/closed dates. "
        "Joined to deductions on deduction_id. Recovery rate = total recovered / total disputed dollars.")
    row = _write_pair(ws, row, "stores",
        "Store-to-retailer mapping. Used to aggregate scan_data from store level to retailer/channel level.")

    # === ROI METHODOLOGY ===
    row += 1
    row = _write_section(ws, row, "3. Promotion ROI Methodology")
    row = _write_body(ws, row,
        "Simple pre/during/post volume comparison. Not a causal model.")
    row += 1
    row = _write_pair(ws, row, "Step 1: Baseline",
        "Average weekly unit volume for the SKU at that retailer over the N weeks immediately "
        "preceding the promotion start date, where N = the adjustable window parameter (default 4, range 1–8).")
    row = _write_pair(ws, row, "Step 2: During-period",
        "Average weekly unit volume during the promotion weeks (start_week through end_week).")
    row = _write_pair(ws, row, "Step 3: Incremental volume",
        "(During-period avg − Baseline avg) × promotion duration in weeks.")
    row = _write_pair(ws, row, "Step 4: Incremental revenue",
        "Incremental volume × average selling price (ASP) for that SKU at that retailer, "
        "calculated from scan_data as dollars_sold / units_sold.")
    row = _write_pair(ws, row, "Step 5: ROI",
        "Incremental revenue ÷ promotion cost. Uses actual cost (matched promo_billback deduction) "
        "if available; otherwise uses planned cost from the promotions table and flags it.")
    row += 1
    row = _write_pair(ws, row, "Window parameter",
        "The pre/post window (Tab 3 cell D5) controls how many weeks are used for baseline and "
        "post-period comparison. Larger windows smooth noise but may include other promotions. "
        "Smaller windows are more sensitive but noisier. All ROI formulas reference this cell — "
        "changing it recalculates every promotion's ROI.")
    row = _write_pair(ws, row, "Limitations",
        "This methodology does not adjust for seasonality, does not establish causality, "
        "does not control for distribution changes or out-of-stocks, and does not model "
        "post-promotion dip (pantry-loading). Sophisticated baseline modeling with "
        "causal inference is engagement-level work beyond this diagnostic's scope.")

    # === NET-NET MARGIN ===
    row += 1
    row = _write_section(ws, row, "4. Net-Net Effective Margin Methodology")
    row = _write_body(ws, row,
        "Margin waterfall from gross to effective, calculated per retailer:")
    row += 1
    row = _write_pair(ws, row, "Gross margin",
        "( Wholesale price − COGS ) / Wholesale price. Uses channel-specific wholesale prices "
        "from sku_costs, averaged across all SKUs. Example: Walmart GM = 39.0%, DTC GM = 62.5%.")
    row = _write_pair(ws, row, "After structural trade",
        "Gross margin − structural trade rate. The structural rate is the average "
        "trade_spend_pct for that channel from sku_costs.")
    row = _write_pair(ws, row, "Net-net effective margin",
        "After-structural margin − (operational deductions + promo billback) / revenue. "
        "This is the true margin after all trade costs are accounted for.")
    row = _write_pair(ws, row, "Exclusions",
        "Freight, warehousing, and non-trade SG&A are not included. This is trade margin only, "
        "not net income margin.")

    # === RECOVERY METHODOLOGY ===
    row += 1
    row = _write_section(ws, row, "5. Recovery Rate & Addressable Improvement")
    row = _write_pair(ws, row, "Current recovery rate",
        "Total recovered dollars ($98,216) ÷ total disputed dollars ($716,082) = 13.7%. "
        "Scope is all-time (not trailing-365) to reflect the full dispute track record. "
        "This counts won_full (100% recovery) and won_partial (~49% average recovery) outcomes.")
    row = _write_pair(ws, row, "Target recovery input",
        "Tab 2 cell C41 allows entering a target recovery rate (0–100%). "
        "Recovery at target = operational waste × target rate. "
        "Incremental opportunity = recovery at target − current recovered.")
    row = _write_pair(ws, row, "Interpretation",
        "The addressable improvement assumes all operational waste is disputable. "
        "In practice, some categories (slotting, label fines) have low recoverability. "
        "The recoverability score on Tab 2 provides qualitative guidance on which "
        "categories realistically support higher recovery targets.")

    # === EXTERNAL BENCHMARK ===
    row += 1
    row = _write_section(ws, row, "6. External Benchmark")
    row = _write_body(ws, row,
        "Executive Pulse displays an industry benchmark range (19–23% all-in trade rate) "
        "for context. This positions Cinderhaven's 21.3% all-in rate within the natural/specialty "
        "CPG category average.")
    row += 1
    row = _write_pair(ws, row, "Source",
        "Cadent Consulting Group and Booz & Company trade promotion effectiveness studies, "
        "cross-referenced with published natural/specialty CPG category analysis. The 19–23% "
        "range reflects all-in trade spend (planned + unplanned) as a percentage of gross "
        "revenue for mid-market natural/specialty CPG manufacturers.")
    row = _write_pair(ws, row, "Interpretation",
        "Cinderhaven's 17.3% structural rate is within the planned-trade portion of the range. "
        "The 21.3% all-in rate (structural + operational waste) sits at the high end. "
        "The 4-point gap between planned and all-in is the operational waste — this is where "
        "the diagnostic focuses remediation effort.")
    row = _write_pair(ws, row, "Limitations",
        "Published benchmarks vary by sub-category, company size, retailer mix, and geographic "
        "scope. The 19–23% range is directional, not a precision target. A full engagement would "
        "source retailer-specific and category-specific benchmarks from NielsenIQ, IRI, or direct "
        "peer comparisons.")

    # === GLOSSARY ===
    row += 1
    row = _write_section(ws, row, "7. Glossary")
    terms = [
        ("Trade spend", "All costs a manufacturer pays to retailers beyond product COGS — includes rate-card discounts, promotional allowances, and compliance deductions."),
        ("Structural trade", "The contractual discount rate embedded in wholesale pricing, applied to every unit sold through that channel."),
        ("Operational waste", "Deductions taken by retailers for operational or compliance issues — not planned promotional activity."),
        ("Off-invoice", "A funding mechanism where the promotional discount is deducted from the invoice price at time of sale, rather than billed back later."),
        ("Bill-back", "A funding mechanism where the retailer bills the manufacturer after the promotion executes, typically with documentation."),
        ("Scan-back", "A funding mechanism where the manufacturer pays based on actual units scanned during the promotion window."),
        ("Double-dip", "When a retailer collects the same promotional discount twice — once via off-invoice pricing and again via a billback deduction."),
        ("MCB", "Marketing contribution — billback. A retailer fee for marketing or merchandising support, billed after execution."),
        ("TPR", "Temporary price reduction. A short-term promotional discount on shelf price."),
        ("Ghost promo", "A promo_billback deduction referencing a promotion not found in the planned promotions calendar."),
        ("Deduction", "A dollar amount subtracted by the retailer from a remittance payment, with a reason code."),
        ("Dispute", "A formal challenge filed against a deduction, seeking full or partial recovery."),
        ("Recovery rate", "Percentage of disputed dollars successfully recovered (won_full + won_partial) out of total dollars disputed."),
    ]
    for term, definition in terms:
        row = _write_pair(ws, row, term, definition)

    # === SQL LOGIC ===
    row += 1
    row = _write_section(ws, row, "8. SQL Logic Summary")
    row = _write_body(ws, row,
        "Key queries that produce the locked numbers. All use cinderhaven_product_master.db.")
    row += 1

    sql_blocks = [
        ("Revenue (trailing 52w)",
         "SELECT SUM(dollars_sold) FROM scan_data\n"
         "WHERE week_ending >= (SELECT DISTINCT week_ending\n"
         "  FROM scan_data ORDER BY week_ending DESC LIMIT 1 OFFSET 51)"),
        ("Structural trade",
         "SELECT s.retailer, SUM(sd.dollars_sold) AS channel_rev\n"
         "FROM scan_data sd JOIN stores s ON sd.store_id = s.store_id\n"
         "WHERE sd.week_ending >= [trailing_52w_start]\n"
         "GROUP BY s.retailer\n"
         "-- Then: channel_rev × AVG(trade_spend_pct_[channel]) from sku_costs"),
        ("Operational waste",
         "SELECT SUM(amount) FROM deductions\n"
         "WHERE deduction_date > date([max_scan], '-365 days')\n"
         "  AND deduction_date <= [max_scan]\n"
         "  AND deduction_type != 'promo_billback'"),
        ("Recovery rate",
         "SELECT SUM(recovered_amount) / \n"
         "  (SELECT SUM(d.amount) FROM deductions d\n"
         "   JOIN disputes dis ON dis.deduction_id = d.deduction_id)\n"
         "FROM disputes"),
        ("Promo ROI",
         "-- Per promo: baseline = AVG(units) for N weeks pre-start\n"
         "-- incr_vol = (AVG(units during) - baseline) × duration_weeks\n"
         "-- incr_rev = incr_vol × AVG(dollars_sold/units_sold)\n"
         "-- ROI = incr_rev / COALESCE(actual_cost, planned_cost)"),
    ]
    for title, sql in sql_blocks:
        row = _write_pair(ws, row, title, sql)
