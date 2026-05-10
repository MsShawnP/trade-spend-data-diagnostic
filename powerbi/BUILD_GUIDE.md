# Power BI Dashboard — Build Guide

Step-by-step instructions to assemble the Cinderhaven Trade Spend
dashboard. Sections 1–3 cover automated setup (data model, measures
via pbi-tools). Section 4 covers manual visual assembly.

---

## 1. Prerequisites

- **Power BI Desktop** — June 2024 or later (needed for small
  multiples waterfall)
- **pbi-tools** — `winget install pbi-tools` or https://pbi.tools
- **Python 3.10+** — for export and measure generation scripts
- **Data files** — 7 CSVs in `powerbi/data/`, exported by
  `python powerbi/export_data.py`
- **Reference docs** — keep open while building:
  - `DESIGN.md` — page layouts, visual specs
  - `DAX_MEASURES.md` — full measure formulas and notes
  - `data/DATA_DICTIONARY.md` — column definitions

---

## 2. Automated Steps

### 2.1 Data Import

For each CSV: Home → Get Data → Text/CSV → select the file →
Transform Data to review types → Load.

**Critical type overrides** (Power BI auto-detection gets these wrong):

| File | Column | Change to | Why |
|------|--------|-----------|-----|
| fact_deductions.csv | deduction_id | Text | IDs must not aggregate |
| fact_deductions.csv | deduction_date | Date | |
| fact_deductions.csv | dispute_deadline | Date | |
| fact_deductions.csv | dispute_filed_date | Date | |
| fact_deductions.csv | dispute_closed_date | Date | |
| fact_deductions.csv | is_vague, is_post_audit, is_double_dip | Whole Number | |
| fact_disputes.csv | dispute_id | Text | |
| fact_disputes.csv | deduction_id | Text | Must match fact_deductions type |
| fact_disputes.csv | filed_date, closed_date | Date | |
| dim_promo.csv | start_week, end_week | Date | |
| fact_scan_data.csv | week_ending | Date | |

All other numeric columns: Decimal Number. All text columns: keep
as Text.

**Verify row counts** after loading all 7 tables:

| Table | Rows |
|-------|------|
| dim_retailer | 11 |
| dim_product | 90 |
| dim_promo | 188 |
| fact_deductions | 2,374 |
| fact_structural_trade | 10 |
| fact_scan_data | 601,341 |
| fact_disputes | 1,410 |

### 2.2 Relationships

Switch to Model view. Create each relationship by dragging one column
onto the other. All are single cross-filter direction, from the "one"
side to the "many" side.

```
dim_retailer[retailer_name] → fact_structural_trade[retailer_id]   1:many, single
dim_retailer[retailer_name] → fact_scan_data[retailer]             1:many, single
dim_retailer[retailer_name] → dim_promo[retailer]                  1:many, single
dim_retailer[retailer_id]   → fact_deductions[retailer_id]         1:many, single
dim_retailer[retailer_id]   → fact_disputes[retailer_id]           1:many, single
dim_product[sku]             → fact_scan_data[sku]                  1:many, single
dim_product[sku]             → dim_promo[sku]                       1:many, single
dim_promo[promo_id]          → fact_scan_data[promo_id]             1:many, single
fact_deductions[deduction_id] → fact_disputes[deduction_id]         1:many, single
dim_date[Date]               → fact_deductions[deduction_date]      1:many, single
```

**Notes:**
- dim_retailer joins via `retailer_name` (display name) to some
  tables and `retailer_id` (slug) to others. Both are active — each
  targets a different table.
- The dim_date relationship is created after pbi-tools injects the
  dim_date calculated table (Step 2.3). Create it manually after
  opening the compiled .pbix.
- No date relationship to fact_scan_data — scan data is already
  windowed to trailing 52 weeks in the export.
- WaterfallSteps, WindowWeeks, TargetAllInRate are disconnected
  tables — no relationships.

**Quick verification:** Create a temp table with
`dim_retailer[retailer_name]` and `SUM(fact_scan_data[dollars_sold])`
— total should be $25,593,052. Delete after checking.

### 2.3 Measures via pbi-tools

Save the .pbix, close Power BI Desktop, then run:

```
pbi-tools extract powerbi/trade_spend_diagnostic.pbix
python powerbi/generate_pbix_model.py powerbi/trade_spend_diagnostic
pbi-tools compile powerbi/trade_spend_diagnostic.pbix
```

This injects 49 measures and 4 calculated tables. See
[PBITOOLS_WORKFLOW.md](PBITOOLS_WORKFLOW.md) for full details and
troubleshooting.

After reopening, verify:
- `_Measures` table exists (hidden) with 6 display folders
- dim_date, WaterfallSteps, WindowWeeks, TargetAllInRate tables exist
- Create the dim_date → fact_deductions relationship (§ 2.2, last row)
- Mark dim_date as a date table: Table tools → Mark as date table →
  select `Date`
- Set WaterfallSteps[Step] to sort by WaterfallSteps[SortOrder]
- Format TargetAllInRate column as Percentage

**Alternative — manual measure entry:** If pbi-tools is unavailable,
create the calculated tables and measures manually using the formulas
in `DAX_MEASURES.md`. Create Tier 1 measures first (no dependencies),
then Tier 2–4 in order. See `DAX_MEASURES.md` for the full list.

---

## 3. Format Strings

Set these in the Properties pane after measures are created (whether
via pbi-tools or manually):

| Format | Measures |
|--------|----------|
| `$#,##0` | TotalRevenue, StructuralTradeAmount, OperationalWasteAmount, PromoBillbackAmount, AllInTradeCost, TotalRecovered, DeductionAmount, RetailerRevenue, WasteAmount, PromoCost, IncrementalRevenue, IncrementalRevenueDynamic, DoubleDipTotal, GhostPromoTotal, SavingsAtTarget, TotalSavingsAtTarget, Revenue |
| `0.0%` | AllInTradeRate, StructuralTradeRate, OperationalWasteRate, RecoveryRate, GrossMarginPct, StructuralRate, OpDedRate, PromoBBRate, NetNetMargin, NetNetMarginPct, RevenueShare, DeductionShare |
| `#,##0` | DeductionCount, DisputeCount, PromoCount, FullDataCount, PartialDataCount, NoPOSCount, DoubleDipCount, UnmappedCodeCount, GhostPromoCount |
| `0.00` | PromoROI, PromoROIDynamic, AvgROI, BaselineVolume, BaselineVolumeDynamic |
| `0` | AvgDaysToResolve |

Format strings are embedded in the generated JSON — pbi-tools may
apply them automatically. Verify after compile and correct any that
didn't take.

---

## 4. Page-by-Page Assembly (Manual)

All measures are now available in the Fields pane. This section
covers visual layout, slicers, conditional formatting, and
drill-through — all of which require manual work in Power BI Desktop.

### 4.1 Page 1: Executive Overview

Rename Page 1 to **"Executive Overview"**.

#### Navigation Strip

Add 4 buttons across the top (Insert → Buttons → Blank): "Overview",
"Deductions", "Promos", "Retailers". Each button: Action → Type =
Page navigation, Destination = corresponding page. Style the active
button with darker fill.

#### KPI Cards (Visuals 1–4)

Four cards in a row below the nav strip:

| Visual | Measure | Title |
|--------|---------|-------|
| 1 | AllInTradeRate | All-In Trade Rate |
| 2 | StructuralTradeRate | Structural Trade Rate |
| 3 | OperationalWasteRate | Operational Waste Rate |
| 4 | TotalRevenue | Total Revenue |

Conditional formatting on Visual 3: Background color → Rules:
- value > 0.05 → Red (#FF4444)
- value 0.03–0.05 → Yellow (#FFCC00)
- value < 0.03 → Green (#44BB44)

#### Visual 5 — Margin Erosion Waterfall

- Type: Waterfall chart, full width below cards
- Category: `WaterfallSteps[Step]`, Y-axis: `WaterfallValue`
- Sort by `WaterfallSteps[SortOrder]` ascending
- Increase = blue (#4472C4), Decrease = red (#C44444)
- Mark "Revenue" and "Net After Trade" as totals

#### Visual 6 — Waste Breakdown Bar

- Type: Clustered bar, bottom-left
- Y-axis: `fact_deductions[deduction_type]`, X-axis: `WasteAmount`
- Visual-level filter: deduction_type ≠ "promo_billback"
- Sort by WasteAmount descending, single color (#C44444)

#### Visual 7 — Revenue Donut

- Type: Donut, bottom-right upper
- Legend: `dim_retailer[retailer_name]`, Values: `RetailerRevenue`
- Labels: category name + percentage

#### Visual 8 — Recovery Snapshot

- Type: Multi-row card, bottom-right lower
- Fields: `RecoveryRate`, `DisputeCount`, `TotalRecovered`

#### Slicers

| Slicer | Field | Type | Default |
|--------|-------|------|---------|
| Retailer | `dim_retailer[retailer_name]` | Dropdown multi-select | All |
| Date range | `dim_date[Date]` | Between slider | Trailing 365 days |

#### Drill-Through

This page is a drill-through SOURCE. Destinations configured on
target pages (§ 4.2 and § 4.4).

---

### 4.2 Page 2: Deduction Deep-Dive

New page → rename to **"Deduction Deep-Dive"**. Add Back button
(Insert → Buttons → Back) and the nav strip (copy from Page 1).

#### Visual 1 — Deduction Trend Area Chart

- Type: Stacked area chart, top half, full width
- X-axis: `dim_date[year_month]`, Y-axis: `DeductionAmount`
- Legend: `fact_deductions[deduction_type]`
- Assign consistent colors per deduction type:
  short_ship (#E06666), pricing_error (#6FA8DC),
  unauthorized_deduction (#93C47D), compliance_fine (#FFD966),
  promo_billback (#8E7CC3), damaged_goods (#F6B26B),
  logistics_chargeback (#76A5AF), quality_claim (#CC4125)

#### Visual 2 — Category Treemap

- Type: Treemap, left below area chart
- Group: `fact_deductions[deduction_type]`, Values: `DeductionAmount`
- Colors: match area chart

#### Visual 3 — Retailer × Category Matrix

- Type: Matrix, right below area chart
- Rows: `fact_deductions[deduction_type]`
- Columns: `dim_retailer[retailer_name]`
- Values: `DeductionAmount`
- Conditional formatting: 3-color scale white → yellow (#FFCC00) →
  red (#CC0000)

#### Visual 4 — Detail Table

- Type: Table, bottom full width
- Columns: deduction_id, deduction_date, retailer_id, translated_code,
  deduction_type, amount, dispute_outcome, recovered_amount
- Conditional formatting on dispute_outcome: won_full → green
  (#44BB44), won_partial → yellow (#FFCC00), lost → red (#FF4444),
  pending → gray (#CCCCCC)

#### Visual 5 — Double-Dip Alert

- Type: Multi-row card, top-right corner
- Fields: `DoubleDipCount`, `DoubleDipTotal`
- Background: light red (#FFE0E0)

#### Visual 6 — Unmapped Code Count

- Type: Card, below Visual 5
- Field: `UnmappedCodeCount`, title "Unmapped Codes"

#### Slicers

| Slicer | Field | Type | Default |
|--------|-------|------|---------|
| Retailer | `dim_retailer[retailer_name]` | Dropdown multi-select | All |
| Deduction type | `fact_deductions[deduction_type]` | Checkbox list | All |
| Date range | `dim_date[Date]` | Between slider | Trailing 365 days |
| Vague flag | `fact_deductions[is_vague]` | Dropdown single-select | All |

#### Drill-Through Setup

Drag `fact_deductions[deduction_type]` AND `dim_retailer[retailer_name]`
into the Drill-through field well. This makes the page a target from:
- Page 1 waste breakdown bar (by deduction type)
- Page 4 retailer bars (by retailer name)

---

### 4.3 Page 3: Promo Performance

New page → rename to **"Promo Performance"**. Add Back button and
nav strip.

#### Visual 1 — Cost vs. Value Scatter

- Type: Scatter chart, top-left (half width, ~40% height)
- X-axis: `PromoCost`, Y-axis: `IncrementalRevenue`
  (or `IncrementalRevenueDynamic` for what-if window)
- Size: `dim_promo[duration_weeks]`
- Legend: `dim_promo[promo_type]`
- Details: `dim_promo[promo_id]`
- Analytics: constant line on X (median PromoCost) and Y (value 0)
  to create quadrant reference lines
- Quadrant shading: Power BI lacks native quadrant fills. Use
  constant lines alone, or add a calculated column to color dots
  by quadrant (see `DAX_MEASURES.md` implementation notes)
- Visual filter: exclude rows where IncrementalRevenue is blank

#### Visual 2 — ROI Histogram

- Type: Clustered column (as histogram), top-right
- X-axis: right-click `dim_promo[roi]` → New group → Bin size 0.5
- Y-axis: `PromoCount`
- Visual filter: roi is not blank
- Analytics: constant line at X = 1.0 (breakeven)

#### Visual 3 — ROI by Promo Type Bar

- Type: Clustered bar, middle-left
- Y-axis: `dim_promo[promo_type]`, X-axis: `AvgROI`
- Tooltips: `PromoCount`
- Sort by AvgROI descending, constant line at 1.0

#### Visual 4 — Ghost Promo Alert

- Type: Two cards, middle-right
- `GhostPromoCount` ("Ghost Promos"), `GhostPromoTotal` ("Ghost $")
- Background: light orange (#FFF0E0)

#### Visual 5 — Promo Detail Table

- Type: Table, bottom full width
- Columns: promo_id, retailer, sku, promo_type, start_week,
  planned_cost, actual_cost, incremental_revenue, roi, data_quality
- Conditional formatting on roi: >1.5 green, 0.8–1.5 yellow, <0.8 red
- Conditional formatting on data_quality: Full green, Partial yellow,
  No POS red

#### Visual 6 — Data Coverage Cards

- Type: Three cards, above detail table
- `FullDataCount` ("Full POS"), `PartialDataCount` ("Partial"),
  `NoPOSCount` ("No POS")

#### Slicers

| Slicer | Field | Type | Default |
|--------|-------|------|---------|
| Retailer | `dim_retailer[retailer_name]` | Dropdown multi-select | All |
| Promo type | `dim_promo[promo_type]` | Checkbox list | All |
| Funding | `dim_promo[funding_mechanism]` | Checkbox list | All |
| Data quality | `dim_promo[data_quality]` | Dropdown single-select | All |
| Window | `WindowWeeks[WindowWeeks Value]` | Slider | 4 |

#### Visual Interactions

Clicking a bar in the ROI chart (Visual 3) cross-filters the scatter
and detail table automatically. No additional configuration needed.

#### Drill-Through

Add `dim_promo[promo_type]` to the Drill-through field well.

---

### 4.4 Page 4: Retailer Comparison

New page → rename to **"Retailer Comparison"**. Add Back button and
nav strip.

#### Visual 1 — Margin Composition Stacked Bar

- Type: 100% stacked bar, top, full width
- Y-axis: `dim_retailer[retailer_name]`
- X-axis (layer order): `StructuralRate`, `OpDedRate`, `PromoBBRate`,
  `NetNetMargin`
- Colors: StructuralRate yellow (#FFCC00), OpDedRate orange (#F6B26B),
  PromoBBRate red (#CC4125), NetNetMargin green (#44BB44)
- Sort by dim_retailer[revenue] descending

#### Visual 2 — Concentration Risk Bar

- Type: Clustered bar, middle-left
- Y-axis: `dim_retailer[retailer_name]`
- X-axis: `RevenueShare`, `DeductionShare`
- Colors: Revenue blue (#4472C4), Deductions red (#CC4125)
- Conditional formatting: red outline where DeductionShare >
  RevenueShare

#### Visual 3 — Per-Retailer Waterfall (Small Multiples)

- Type: Waterfall chart, middle-right
- Category: `WaterfallSteps[Step]`, Y-axis: `RetailerWaterfallValue`
- Small multiples: `dim_retailer[retailer_name]`
- Sort by SortOrder ascending
- Mark first and last steps as totals
- Layout: 2 columns × 5 rows, uniform Y-axis

#### Visual 4 — P&L Summary Table

- Type: Table, bottom full width
- Columns: retailer_name, Revenue, GrossMarginPct, StructuralRate,
  OpDedRate, NetNetMarginPct, SavingsAtTarget
- Sort by Revenue descending
- Conditional formatting on NetNetMarginPct: <15% red, 15–25% yellow,
  >25% green
- Conditional formatting on SavingsAtTarget: green data bars

#### Visual 5 — Total Savings Card

- Type: Card, top-right
- Field: `TotalSavingsAtTarget`
- Title: "Portfolio Savings at Target Rate"

#### Visual 6 — Highest Risk Retailer

- Type: Card, below savings card
- Field: `HighestRiskRetailer`, font color red

#### Slicers

| Slicer | Field | Type | Default |
|--------|-------|------|---------|
| Target rate | `TargetAllInRate[TargetAllInRate Value]` | Slider, percentage format | 18% |

Page-level filter: `dim_retailer[retailer_name]` ≠ "DTC" (excludes
zero-trade benchmark).

#### Drill-Through Setup

Drag `dim_retailer[retailer_name]` into the Drill-through field well.
This makes the page a target from Page 1's donut chart.

---

## 5. Bookmarks and Navigation

### Page Navigation Buttons

Already created per § 4.1. Build on Page 1, copy to Pages 2–4. Style
the active page button distinctly on each page.

### Back Buttons

Pages 2–4 have Back buttons that auto-return to the source page.

### No Additional Bookmarks

The dashboard uses page navigation and drill-through only.

---

## 6. Final Checklist

- [ ] **Page names**: "Executive Overview", "Deduction Deep-Dive",
      "Promo Performance", "Retailer Comparison"
- [ ] **Page order**: Overview first (tab order left to right)
- [ ] **Default page**: File → Options → Current File → Report
      Settings → Default page = "Executive Overview"
- [ ] **Navigation buttons**: all 4 work on all 4 pages
- [ ] **Back buttons**: present on Pages 2–4
- [ ] **Drill-through paths**:
  - Page 1 donut → Page 4 (by retailer)
  - Page 1 waste bar → Page 2 (by deduction type)
  - Page 4 stacked bar → Page 2 (by retailer)
- [ ] **KPI spot-check** (no slicers active):
  - AllInTradeRate: 21.3%
  - StructuralTradeRate: 17.3%
  - OperationalWasteRate: ~4.0%
  - TotalRevenue: ~$25.6M
  - DoubleDipCount: 3
  - GhostPromoCount: 137
- [ ] **Cross-filter test**: click Walmart in Page 1 donut — all
      visuals update. Click again to deselect.
- [ ] **What-if test**:
  - Page 4: slide TargetAllInRate to 20% — SavingsAtTarget updates
  - Page 3: slide WindowWeeks (if using dynamic measures)
- [ ] **Conditional formatting visible** on all pages
- [ ] **Hide helper tables**: right-click WaterfallSteps, WindowWeeks,
      TargetAllInRate → Hide in report view
- [ ] **Save**: Ctrl+S
