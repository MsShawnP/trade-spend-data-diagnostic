# Power BI Dashboard — Build Guide

Step-by-step instructions to assemble the Cinderhaven Trade Spend
dashboard from the exported data files and DAX measures. Follow in
order.

---

## 1. Prerequisites

- **Power BI Desktop** — June 2024 or later (needed for small
  multiples waterfall)
- **Data files** — 7 CSVs in `powerbi/data/`, exported by
  `python powerbi/export_data.py`
- **Reference docs** — keep open while building:
  - `powerbi/DESIGN.md` — page layouts, visual specs
  - `powerbi/DAX_MEASURES.md` — all measure formulas
  - `powerbi/data/DATA_DICTIONARY.md` — column definitions

Save the new file as `CinderhavenTradeSpend.pbix` in the `powerbi/`
directory.

---

## 2. Data Import

For each table: Home → Get Data → Text/CSV → select the file →
Transform Data to review types → Load.

### 2.1 dim_retailer.csv

| Column | Auto-detected | Change to |
|--------|---------------|-----------|
| retailer_id | text | text (keep) |
| retailer_name | text | text (keep) |
| channel_type | text | text (keep) |
| revenue | number | Decimal Number |
| trade_rate | number | Decimal Number |
| gross_margin | number | Decimal Number |
| structural_trade_dollars | number | Decimal Number |
| op_deductions | number | Decimal Number |
| promo_billback | number | Decimal Number |
| all_in_trade | number | Decimal Number |
| all_in_rate | number | Decimal Number |
| net_net_margin | number | Decimal Number |

### 2.2 dim_product.csv

| Column | Auto-detected | Change to |
|--------|---------------|-----------|
| sku | text | text (keep) |
| product_name | text | text (keep) |
| product_line | text | text (keep) |
| subcategory | text | text (keep) |
| cogs_per_unit | number | Decimal Number |
| wholesale_price | number | Decimal Number |
| wholesale_walmart | number | Decimal Number |
| wholesale_costco | number | Decimal Number |
| wholesale_whole_foods | number | Decimal Number |
| wholesale_regional | number | Decimal Number |
| wholesale_unfi | number | Decimal Number |
| wholesale_dtc | number | Decimal Number |

### 2.3 dim_promo.csv

| Column | Auto-detected | Change to |
|--------|---------------|-----------|
| promo_id | text | text (keep) |
| sku | text | text (keep) |
| retailer | text | text (keep) |
| store_scope | text | text (keep) |
| start_week | text | Date |
| end_week | text | Date |
| duration_weeks | number | Whole Number |
| discount_depth_pct | number | Decimal Number |
| promo_type | text | text (keep) |
| planned_cost | number | Decimal Number |
| actual_cost | number | Decimal Number |
| funding_mechanism | text | text (keep) |
| asp | number | Decimal Number |
| baseline_avg_volume | number | Decimal Number |
| during_avg_volume | number | Decimal Number |
| incremental_volume | number | Decimal Number |
| incremental_revenue | number | Decimal Number |
| roi | number | Decimal Number |
| cost_source | text | text (keep) |
| data_quality | text | text (keep) |

### 2.4 fact_deductions.csv

| Column | Auto-detected | Change to |
|--------|---------------|-----------|
| deduction_id | number | **text** (critical — IDs must not aggregate) |
| retailer_id | text | text (keep) |
| deduction_date | text | Date |
| deduction_type | text | text (keep) |
| amount | number | Decimal Number |
| code_as_remitted | text | text (keep) |
| translated_code | text | text (keep) |
| standardized_category | text | text (keep) |
| order_id | text | text (keep) |
| shipment_id | text | text (keep) |
| remittance_id | text | text (keep) |
| remittance_description | text | text (keep) |
| dispute_deadline | text | Date |
| is_vague | number | Whole Number |
| is_post_audit | number | Whole Number |
| is_double_dip | number | Whole Number |
| dispute_outcome | text | text (keep) |
| recovered_amount | number | Decimal Number |
| dispute_filed_date | text | Date |
| dispute_closed_date | text | Date |
| days_outstanding | number | Whole Number |

### 2.5 fact_structural_trade.csv

| Column | Auto-detected | Change to |
|--------|---------------|-----------|
| retailer_id | text | text (keep) |
| revenue | number | Decimal Number |
| trade_rate | number | Decimal Number |
| structural_trade_dollars | number | Decimal Number |

### 2.6 fact_scan_data.csv

This table has 601K rows. In Power Query, set types before loading:

| Column | Auto-detected | Change to |
|--------|---------------|-----------|
| sku | text | text (keep) |
| retailer | text | text (keep) |
| store_id | text | text (keep) |
| week_ending | text | Date |
| units_sold | number | Whole Number |
| dollars_sold | number | Decimal Number |
| promo_id | text | text (keep) |
| promo_period | text | text (keep) |

### 2.7 fact_disputes.csv

| Column | Auto-detected | Change to |
|--------|---------------|-----------|
| dispute_id | number | **text** |
| deduction_id | number | **text** (must match fact_deductions type) |
| retailer_id | text | text (keep) |
| deduction_type | text | text (keep) |
| deduction_amount | number | Decimal Number |
| filed_date | text | Date |
| closed_date | text | Date |
| filing_method | text | text (keep) |
| evidence_quality | text | text (keep) |
| submitted_evidence_count | number | Whole Number |
| was_within_deadline | number | Whole Number |
| outcome | text | text (keep) |
| recovered_amount | number | Decimal Number |
| labor_hours | number | Decimal Number |
| days_to_resolve | number | Whole Number |

After loading all 7 tables, verify row counts in the bottom-right
status bar: dim_retailer (11), dim_product (90), dim_promo (188),
fact_deductions (2,374), fact_structural_trade (10),
fact_scan_data (601,341), fact_disputes (1,410).

---

## 3. Calculated Tables

Create these before any measures. Modeling → New Table for each.

### 3.1 dim_date

```dax
dim_date =
VAR MinDate = MIN(fact_deductions[deduction_date])
VAR MaxDate = MAX(fact_scan_data[week_ending])
RETURN
ADDCOLUMNS(
    CALENDAR(MinDate, MaxDate),
    "year", YEAR([Date]),
    "month", MONTH([Date]),
    "year_month", FORMAT([Date], "YYYY-MM"),
    "week_ending",
        [Date] + (6 - WEEKDAY([Date], 2)),
    "month_name", FORMAT([Date], "MMM YYYY")
)
```

After creation, mark `dim_date` as a date table: select the table
in Model view → Table tools → Mark as date table → select `Date`.

### 3.2 WaterfallSteps

```dax
WaterfallSteps =
DATATABLE(
    "Step", STRING,
    "SortOrder", INTEGER,
    {
        {"Revenue", 1},
        {"Structural Trade", 2},
        {"Operational Waste", 3},
        {"Net After Trade", 4}
    }
)
```

In Model view, set `Step` column to sort by `SortOrder`:
Select `Step` → Column tools → Sort by Column → `SortOrder`.

### 3.3 WindowWeeks

Modeling → New Parameter → What-if:
- Name: `WindowWeeks`
- Data type: Whole number
- Minimum: 1
- Maximum: 8
- Increment: 1
- Default: 4
- Check "Add slicer to this page": No (add manually later)

This creates the table and the `WindowWeeks Value` measure
automatically. If creating manually:

```dax
WindowWeeks = GENERATESERIES(1, 8, 1)
```

Then add the measure:

```dax
WindowWeeks Value =
SELECTEDVALUE(WindowWeeks[WindowWeeks Value], 4)
```

### 3.4 TargetAllInRate

Modeling → New Parameter → What-if:
- Name: `TargetAllInRate`
- Data type: Decimal number
- Minimum: 0
- Maximum: 0.50
- Increment: 0.01
- Default: 0.18
- Check "Add slicer to this page": No

Or manually:

```dax
TargetAllInRate = GENERATESERIES(0, 0.50, 0.01)
```

Then add the measure:

```dax
TargetAllInRate Value =
SELECTEDVALUE(TargetAllInRate[TargetAllInRate Value], 0.18)
```

Format the `TargetAllInRate Value` column and measure as Percentage.

---

## 4. Relationships

Switch to Model view. Create each relationship by dragging one column
onto the other.

### 4.1 Active Relationships

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

All relationships: single cross-filter direction, from the "one" side
to the "many" side.

### 4.2 Relationship Notes

- **dim_retailer connects via two different columns**: `retailer_name`
  (display name like "Walmart") for tables using display names, and
  `retailer_id` (slug like "walmart") for tables using slugs. Both
  are active — each targets a different fact table.
- **No date relationship to fact_scan_data**: Scan data is already
  filtered to the trailing 52 weeks in the export. The date slicer
  on Pages 1–2 filters deduction-based measures only.
- **WaterfallSteps, WindowWeeks, TargetAllInRate**: No relationships.
  These are disconnected tables read via SELECTEDVALUE in measures.

### 4.3 Verification

After creating all relationships, spot-check in Report view:
- Create a temp table visual with `dim_retailer[retailer_name]` and
  `SUM(fact_scan_data[dollars_sold])` — should show revenue per
  retailer, total $25,593,052.
- Add `SUM(fact_deductions[amount])` — should show deductions per
  retailer matched by slug.
- Delete the temp visual when done.

---

## 5. Measures

Open `DAX_MEASURES.md` alongside. All measures go in a dedicated
`_Measures` display folder. To create this: select any table (e.g.,
fact_scan_data) → New Measure → enter the DAX → then in Properties,
set Display Folder to `_Measures`.

### 5.1 Creation Order

Some measures reference others. Create in this order:

**Tier 1 — Base measures (no dependencies):**
1. TotalRevenue
2. StructuralTradeAmount
3. OperationalWasteAmount
4. PromoBillbackAmount
5. DeductionCount
6. TotalRecovered
7. DisputeCount
8. DeductionAmount
9. RetailerRevenue
10. WasteAmount
11. PromoCost
12. IncrementalRevenue
13. BaselineVolume
14. PromoROI
15. PromoCount
16. FullDataCount
17. PartialDataCount
18. NoPOSCount
19. DoubleDipCount
20. DoubleDipTotal
21. UnmappedCodeCount
22. AvgDaysToResolve
23. GrossMarginPct
24. StructuralRate
25. Revenue (Page 4)
26. GhostPromoCount
27. GhostPromoTotal

**Tier 2 — Depend on Tier 1:**
1. StructuralTradeRate (uses TotalRevenue, StructuralTradeAmount)
2. OperationalWasteRate (uses OperationalWasteAmount, TotalRevenue)
3. AllInTradeCost (uses StructuralTradeAmount, OperationalWasteAmount, PromoBillbackAmount)
4. RecoveryRate (uses TotalRecovered)
5. OpDedRate (uses dim_retailer[revenue])
6. PromoBBRate (uses dim_retailer[revenue])
7. RevenueShare (uses TotalRevenue via ALL)
8. DeductionShare (uses DeductionAmount via ALL)
9. AvgROI (uses dim_promo[roi])
10. BaselineVolumeDynamic (uses WindowWeeks Value)

**Tier 3 — Depend on Tier 2:**
1. AllInTradeRate (uses AllInTradeCost, TotalRevenue)
2. NetNetMargin (uses GrossMarginPct, StructuralRate, OpDedRate, PromoBBRate)
3. WaterfallValue (uses TotalRevenue, StructuralTradeAmount, OperationalWasteAmount)
4. IncrementalRevenueDynamic (uses BaselineVolumeDynamic)
5. SavingsAtTarget (uses StructuralRate, OpDedRate, PromoBBRate, TargetAllInRate Value)

**Tier 4 — Depend on Tier 3:**
1. NetNetMarginPct (uses NetNetMargin)
2. TotalSavingsAtTarget (uses StructuralRate, OpDedRate, PromoBBRate, TargetAllInRate Value)
3. HighestRiskRetailer (uses dim_retailer[net_net_margin])
4. RetailerWaterfallValue (uses GrossMarginPct, StructuralRate, OpDedRate, PromoBBRate, NetNetMargin)
5. PromoROIDynamic (uses IncrementalRevenueDynamic, PromoCost)

### 5.2 Format Strings

After creating each measure, set the format in the Properties pane:

| Format | Measures |
|--------|----------|
| `$#,##0` | TotalRevenue, StructuralTradeAmount, OperationalWasteAmount, PromoBillbackAmount, AllInTradeCost, TotalRecovered, DeductionAmount, RetailerRevenue, WasteAmount, PromoCost, IncrementalRevenue, IncrementalRevenueDynamic, DoubleDipTotal, GhostPromoTotal, SavingsAtTarget, TotalSavingsAtTarget, Revenue |
| `0.0%` | AllInTradeRate, StructuralTradeRate, OperationalWasteRate, RecoveryRate, GrossMarginPct, StructuralRate, OpDedRate, PromoBBRate, NetNetMargin, NetNetMarginPct, RevenueShare, DeductionShare |
| `#,##0` | DeductionCount, DisputeCount, PromoCount, FullDataCount, PartialDataCount, NoPOSCount, DoubleDipCount, UnmappedCodeCount, GhostPromoCount |
| `0.00` | PromoROI, PromoROIDynamic, AvgROI, BaselineVolume, BaselineVolumeDynamic |
| `0` | AvgDaysToResolve |
| (none) | WaterfallValue, RetailerWaterfallValue, HighestRiskRetailer |

---

## 6. Page-by-Page Assembly

### 6.1 Page 1: Executive Overview

Rename Page 1 to **"Executive Overview"**.

#### Navigation Strip (top)

Add a row of 4 buttons across the top of the page (Insert → Buttons
→ Blank). Label them: "Overview", "Deductions", "Promos", "Retailers".
Each button's Action: Type = Page navigation, Destination = the
corresponding page. Style the active page button with a darker
background.

#### Visual 1 — AllInTradeRate KPI Card

- Type: Card
- Position: Top-left, below nav strip
- Fields: Value = `AllInTradeRate`
- Title: "All-In Trade Rate"
- Callout value font: 28pt

#### Visual 2 — StructuralTradeRate KPI Card

- Type: Card
- Position: Right of Visual 1
- Fields: Value = `StructuralTradeRate`
- Title: "Structural Trade Rate"

#### Visual 3 — OperationalWasteRate KPI Card

- Type: Card
- Position: Right of Visual 2
- Fields: Value = `OperationalWasteRate`
- Title: "Operational Waste Rate"
- Conditional formatting: Format → Background color → Rules:
  - If value > 0.05 → Red (#FF4444)
  - If value >= 0.03 AND <= 0.05 → Yellow (#FFCC00)
  - If value < 0.03 → Green (#44BB44)

#### Visual 4 — TotalRevenue KPI Card

- Type: Card
- Position: Right of Visual 3
- Fields: Value = `TotalRevenue`
- Title: "Total Revenue"

#### Visual 5 — Margin Erosion Waterfall

- Type: Waterfall chart
- Position: Left half, middle section, spanning full width below cards
- Fields:
  - Category: `WaterfallSteps[Step]`
  - Y-axis: `WaterfallValue`
- Formatting:
  - Sort: by `WaterfallSteps[SortOrder]` ascending
  - Sentiment colors: Increase = blue (#4472C4), Decrease = red
    (#C44444)
  - Total: enable "Total" column formatting. Mark "Revenue" and
    "Net After Trade" as totals (Column → Breakdown → Total)

#### Visual 6 — Waste Breakdown Bar

- Type: Clustered bar chart
- Position: Bottom-left quadrant
- Fields:
  - Y-axis: `fact_deductions[deduction_type]`
  - X-axis: `WasteAmount`
- Visual-level filter: `fact_deductions[deduction_type]` is not
  "promo_billback"
- Sort: by WasteAmount descending
- Data colors: single color (#C44444)

#### Visual 7 — Revenue by Retailer Donut

- Type: Donut chart
- Position: Bottom-right quadrant (upper)
- Fields:
  - Legend: `dim_retailer[retailer_name]`
  - Values: `RetailerRevenue`
- Detail labels: Category name + percentage
- Interaction: clicking a segment cross-filters all other visuals

#### Visual 8 — Recovery Snapshot

- Type: Multi-row card
- Position: Bottom-right quadrant (lower)
- Fields: `RecoveryRate`, `DisputeCount`, `TotalRecovered`
- Show 3 cards in a row

#### Slicers

**Retailer slicer:**
- Type: Slicer
- Position: Top-right corner, below nav strip
- Field: `dim_retailer[retailer_name]`
- Settings: Dropdown, multi-select, "Select all" enabled
- Default: All selected

**Date range slicer:**
- Type: Slicer
- Position: Below retailer slicer
- Field: `dim_date[Date]`
- Settings: Between (range slider)
- Default: trailing 365 days from the max date

#### Drill-through Configuration

This page is a drill-through SOURCE, not a target. Cross-filtering
handles the interactivity. The drill-through destinations are
configured on Pages 2 and 4 (see sections 6.2 and 6.4).

---

### 6.2 Page 2: Deduction Deep-Dive

Create a new page, rename to **"Deduction Deep-Dive"**.

#### Back Button

Insert → Buttons → Back. Position: top-left. This auto-returns to
the page the user drilled through from.

#### Navigation Strip

Same 4-button strip as Page 1 (copy and paste the nav strip from
Page 1).

#### Visual 1 — Deduction Trend Area Chart

- Type: Stacked area chart
- Position: Top half, full width below nav strip
- Fields:
  - X-axis: `dim_date[year_month]`
  - Y-axis: `DeductionAmount`
  - Legend: `fact_deductions[deduction_type]`
- Sort: X-axis by `dim_date[year_month]` ascending
- Colors: assign a consistent color per deduction type (these same
  colors should be used everywhere deduction types appear):
  - short_ship: #E06666
  - pricing_error: #6FA8DC
  - unauthorized_deduction: #93C47D
  - compliance_fine: #FFD966
  - promo_billback: #8E7CC3
  - damaged_goods: #F6B26B
  - logistics_chargeback: #76A5AF
  - quality_claim: #CC4125

#### Visual 2 — Category Treemap

- Type: Treemap
- Position: Left side, below area chart
- Fields:
  - Group: `fact_deductions[deduction_type]`
  - Values: `DeductionAmount`
- Colors: match the area chart colors above
- Interaction: clicking a block filters the area chart, matrix,
  and detail table

#### Visual 3 — Retailer × Category Matrix

- Type: Matrix
- Position: Right side, below area chart
- Fields:
  - Rows: `fact_deductions[deduction_type]`
  - Columns: `dim_retailer[retailer_name]`
  - Values: `DeductionAmount`
- Conditional formatting on values: Background color → Color scale:
  - Minimum: white (#FFFFFF)
  - Center: yellow (#FFCC00)
  - Maximum: red (#CC0000)
  - Based on: value

#### Visual 4 — Deduction Detail Table

- Type: Table
- Position: Bottom section, full width
- Columns (in order):
  1. `fact_deductions[deduction_id]`
  2. `fact_deductions[deduction_date]`
  3. `fact_deductions[retailer_id]`
  4. `fact_deductions[translated_code]`
  5. `fact_deductions[deduction_type]`
  6. `fact_deductions[amount]`
  7. `fact_deductions[dispute_outcome]`
  8. `fact_deductions[recovered_amount]`
- Conditional formatting on `dispute_outcome`: Background color →
  Rules:
  - "won_full" → Green (#44BB44)
  - "won_partial" → Yellow (#FFCC00)
  - "lost" → Red (#FF4444)
  - "pending" → Gray (#CCCCCC)

#### Visual 5 — Double-Dip Alert

- Type: Multi-row card (or two separate cards)
- Position: Top-right corner, persistent
- Fields: `DoubleDipCount`, `DoubleDipTotal`
- Background: light red (#FFE0E0) to draw attention

#### Visual 6 — Unmapped Code Count

- Type: Card
- Position: Below double-dip cards
- Field: `UnmappedCodeCount`
- Title: "Unmapped Codes"

#### Slicers

**Retailer slicer:**
- Field: `dim_retailer[retailer_name]`, dropdown multi-select, default All

**Deduction type slicer:**
- Field: `fact_deductions[deduction_type]`, checkbox list, default All

**Date range slicer:**
- Field: `dim_date[Date]`, between slider, default trailing 365 days

**Vague flag slicer:**
- Field: `fact_deductions[is_vague]`, dropdown single-select
- Values shown: All / 1 (Yes) / 0 (No)
- Default: All

#### Drill-Through Setup

This page is a drill-through TARGET from Page 1. To configure:
1. Select the page in Report view
2. Drag `fact_deductions[deduction_type]` into the Drill-through
   field well in the Visualizations pane
3. Set "Keep all filters" to On
4. Now on Page 1, right-clicking a bar in the waste breakdown chart
   will show "Drill through → Deduction Deep-Dive"

---

### 6.3 Page 3: Promo Performance

Create a new page, rename to **"Promo Performance"**.

#### Back Button and Navigation Strip

Copy from Page 2.

#### Visual 1 — Cost vs. Value Scatter

- Type: Scatter chart
- Position: Top-left, large (half-page width, ~40% height)
- Fields:
  - X-axis: `PromoCost`
  - Y-axis: `IncrementalRevenue` (or `IncrementalRevenueDynamic`
    for dynamic window)
  - Size: `dim_promo[duration_weeks]`
  - Legend: `dim_promo[promo_type]`
  - Details: `dim_promo[promo_id]`
- Analytics pane:
  - Add constant line on X-axis: use median of PromoCost
  - Add constant line on Y-axis: value 0 (breakeven)
  - These create the quadrant reference lines
- Quadrant shading: Power BI does not natively support background
  fills on scatter quadrants. Approximate with: Analytics pane →
  add a filled region (if available in your version), or add a
  semi-transparent shape behind the chart manually. Alternatively,
  add a color-coded calculated column to dim_promo:
  ```dax
  QuadrantLabel =
  IF(dim_promo[roi] > 1 && dim_promo[incremental_revenue] > MEDIAN(dim_promo[incremental_revenue]),
      "High Value",
      IF(dim_promo[roi] < 1, "Low Value", "Moderate"))
  ```
  Then use this column as the scatter Legend instead of promo_type
  to color dots by quadrant. Or keep promo_type on Legend and rely
  on the constant lines alone to delineate the quadrants visually.
- Visual-level filter: exclude rows where IncrementalRevenue is blank

#### Visual 2 — ROI Distribution Histogram

- Type: Clustered column chart (used as histogram)
- Position: Top-right, medium
- Fields:
  - X-axis: Create a new grouping on `dim_promo[roi]`:
    Right-click `roi` column → New group → Bin type = Bin,
    Bin size = 0.5
  - Y-axis: `PromoCount`
- Visual-level filter: `dim_promo[roi]` is not blank
- Add a constant line at X = 1.0 (breakeven reference)

#### Visual 3 — ROI by Promo Type Bar

- Type: Clustered bar chart
- Position: Middle-left
- Fields:
  - Y-axis: `dim_promo[promo_type]`
  - X-axis: `AvgROI`
- Tooltips: add `PromoCount`
- Sort: by AvgROI descending
- Add a constant line at value = 1.0 (breakeven)

#### Visual 4 — Ghost Promo Alert Cards

- Type: Two cards side by side
- Position: Middle-right
- Card 1: `GhostPromoCount`, title "Ghost Promos"
- Card 2: `GhostPromoTotal`, title "Ghost Promo $"
- Background: light orange (#FFF0E0)

#### Visual 5 — Promo Detail Table

- Type: Table
- Position: Bottom section, full width
- Columns (in order):
  1. `dim_promo[promo_id]`
  2. `dim_promo[retailer]`
  3. `dim_promo[sku]`
  4. `dim_promo[promo_type]`
  5. `dim_promo[start_week]`
  6. `dim_promo[planned_cost]`
  7. `dim_promo[actual_cost]`
  8. `dim_promo[incremental_revenue]`
  9. `dim_promo[roi]`
  10. `dim_promo[data_quality]`
- Conditional formatting on `roi`: Background color → Rules:
  - If value > 1.5 → Green (#44BB44)
  - If value >= 0.8 AND <= 1.5 → Yellow (#FFCC00)
  - If value < 0.8 → Red (#FF4444)
- Conditional formatting on `data_quality`: Background color → Rules:
  - "Full" → Green (#44BB44)
  - "Partial" → Yellow (#FFCC00)
  - "No POS" → Red (#FF4444)

#### Visual 6 — Data Coverage Cards

- Type: Three cards in a row
- Position: Above the detail table, right side
- Card 1: `FullDataCount`, title "Full POS"
- Card 2: `PartialDataCount`, title "Partial"
- Card 3: `NoPOSCount`, title "No POS"

#### Slicers

**Retailer slicer:**
- Field: `dim_retailer[retailer_name]`, dropdown multi-select

**Promo type slicer:**
- Field: `dim_promo[promo_type]`, checkbox list

**Funding mechanism slicer:**
- Field: `dim_promo[funding_mechanism]`, checkbox list

**Data quality slicer:**
- Field: `dim_promo[data_quality]`, dropdown single-select

**Pre-period window slicer:**
- Field: `WindowWeeks[WindowWeeks Value]`
- Type: Slider (set in Format → Slicer settings → Options → Style
  → Slider)
- Default: 4

#### Visual Interactions

Clicking a bar in the ROI by Promo Type chart (Visual 3) cross-filters
the scatter (Visual 1) and detail table (Visual 5) to show only that
promo type. This is default Power BI cross-filtering behavior — no
additional configuration needed. Verify by clicking a bar and
confirming the scatter filters.

#### Drill-Through Setup

Add `dim_promo[promo_type]` to the Drill-through field well so that
right-clicking a scatter dot or table row on other pages can drill
through to this page pre-filtered by promo type.

---

### 6.4 Page 4: Retailer Comparison

Create a new page, rename to **"Retailer Comparison"**.

#### Back Button and Navigation Strip

Copy from Page 2.

#### Visual 1 — Margin Composition Stacked Bar

- Type: 100% stacked bar chart
- Position: Top-left, full width
- Fields:
  - Y-axis: `dim_retailer[retailer_name]`
  - X-axis (in this order — order determines layer stacking):
    1. `StructuralRate`
    2. `OpDedRate`
    3. `PromoBBRate`
    4. `NetNetMargin`
- Colors (assign per measure):
  - StructuralRate: Yellow (#FFCC00)
  - OpDedRate: Orange (#F6B26B)
  - PromoBBRate: Red (#CC4125)
  - NetNetMargin: Green (#44BB44)
- Sort: by dim_retailer[revenue] descending

#### Visual 2 — Concentration Risk Bar

- Type: Clustered bar chart
- Position: Middle-left
- Fields:
  - Y-axis: `dim_retailer[retailer_name]`
  - X-axis: `RevenueShare`, `DeductionShare`
- Colors: RevenueShare = Blue (#4472C4), DeductionShare = Red (#CC4125)
- Conditional formatting on DeductionShare series: if DeductionShare >
  RevenueShare at a given retailer, highlight with red border. Set
  via Format → Data colors → fx → Rules: If value is greater than
  field value `RevenueShare`, then red outline.

#### Visual 3 — Per-Retailer Waterfall (Small Multiples)

- Type: Waterfall chart
- Position: Middle-right
- Fields:
  - Category: `WaterfallSteps[Step]`
  - Y-axis: `RetailerWaterfallValue`
  - Small multiples: `dim_retailer[retailer_name]`
- Formatting:
  - Sort category by `WaterfallSteps[SortOrder]` ascending
  - Sentiment colors: same as Page 1 waterfall
  - Mark "Revenue" (first) and "Net After Trade" (last) as totals
  - Small multiples layout: 2 columns × 5 rows (fits 10 retailers,
    excluding DTC if filtered)
  - Uniform Y-axis across all multiples for comparability

#### Visual 4 — P&L Summary Table

- Type: Table
- Position: Bottom section, full width
- Columns (in order):
  1. `dim_retailer[retailer_name]`
  2. `Revenue`
  3. `GrossMarginPct`
  4. `StructuralRate`
  5. `OpDedRate`
  6. `NetNetMarginPct`
  7. `SavingsAtTarget`
- Sort: by Revenue descending
- Conditional formatting on `NetNetMarginPct`: Background color →
  Rules:
  - If value < 0.15 → Red (#FF4444)
  - If value >= 0.15 AND <= 0.25 → Yellow (#FFCC00)
  - If value > 0.25 → Green (#44BB44)
- Conditional formatting on `SavingsAtTarget`: Data bars → green
  (#44BB44), show bar only (no values in bar)

#### Visual 5 — Total Savings Card

- Type: Card
- Position: Top-right corner
- Field: `TotalSavingsAtTarget`
- Title: "Portfolio Savings at Target Rate"

#### Visual 6 — Highest Risk Retailer Card

- Type: Card
- Position: Below savings card
- Field: `HighestRiskRetailer`
- Title: "Highest Risk Retailer"
- Font color: Red

#### Slicers

**Target trade rate slicer:**
- Field: `TargetAllInRate[TargetAllInRate Value]`
- Type: Slider
- Format as percentage
- Default: 0.18 (18%)

**Exclude DTC filter:**
- Type: Visual-level filter (not a visible slicer)
- Apply a page-level filter: `dim_retailer[retailer_name]` is not
  "DTC"
- Rationale: DTC has zero trade spend, distorting comparisons

#### Drill-Through Setup

This page is a drill-through TARGET from Page 1's donut chart.
1. Drag `dim_retailer[retailer_name]` into the Drill-through field
   well
2. Set "Keep all filters" to On
3. Now on Page 1, right-clicking a retailer segment in the donut
   shows "Drill through → Retailer Comparison"

Additionally, right-clicking a retailer bar in Visual 1 or 2 should
drill through to Page 2. This cross-page drill-through is already
enabled because Page 2 has `fact_deductions[deduction_type]` in its
drill-through well. To also enable by retailer:
- Go to Page 2 and add `dim_retailer[retailer_name]` to the
  Drill-through field well alongside the existing deduction_type field

---

## 7. Bookmarks and Navigation

### 7.1 Page Navigation Buttons

Already created in Section 6.1. Each page has the same 4-button strip.
To set up consistently:

1. Build the strip on Page 1 with 4 blank buttons
2. For each button:
   - Action → Type = Page navigation
   - Action → Destination = target page
3. Copy the strip (Ctrl+C) and paste onto Pages 2–4
4. On each page, style the "current" button differently (darker fill
   or underline) to indicate active page

### 7.2 Back Buttons

Pages 2–4 already have Back buttons (inserted in their sections
above). The Back button automatically returns to the page the user
navigated from — no bookmark needed.

### 7.3 No Additional Bookmarks

The dashboard uses page navigation and drill-through for all
navigation. No additional bookmark-based navigation is needed.

---

## 8. Final Checklist

Run through before saving the final .pbix:

- [ ] **Page names**: "Executive Overview", "Deduction Deep-Dive",
      "Promo Performance", "Retailer Comparison"
- [ ] **Page order**: Overview first (tab order left to right)
- [ ] **Default page**: File → Options → Current File → Report
      Settings → Default page = "Executive Overview"
- [ ] **Navigation buttons**: all 4 work on all 4 pages; active page
      styled distinctly
- [ ] **Back buttons**: present on Pages 2–4; return correctly
- [ ] **Drill-through paths verified**:
  - Page 1 donut → Page 4 (by retailer_name)
  - Page 1 waste bar → Page 2 (by deduction_type)
  - Page 4 stacked bar → Page 2 (by retailer_name)
- [ ] **Spot-check KPI values** (unfiltered, no slicers active):
  - AllInTradeRate: 21.3%
  - StructuralTradeRate: 17.3%
  - OperationalWasteRate: ~4.0%
  - TotalRevenue: ~$25.6M
  - DoubleDipCount: 3
  - GhostPromoCount: 137
- [ ] **Cross-filter works**: Click "Walmart" in the Page 1 donut —
      all cards, waterfall, and bar chart update for Walmart only.
      Click again to deselect.
- [ ] **What-if parameters work**:
  - Page 3: slide WindowWeeks to 2 — scatter should redraw (if using
    dynamic measures)
  - Page 4: slide TargetAllInRate to 20% — SavingsAtTarget column
    and TotalSavingsAtTarget card update
- [ ] **Conditional formatting visible**:
  - Page 1: OperationalWasteRate card has colored background
  - Page 2: matrix cells have gradient shading
  - Page 2: dispute_outcome column has colored backgrounds
  - Page 3: roi and data_quality columns colored
  - Page 4: NetNetMarginPct column colored, SavingsAtTarget has
    data bars
- [ ] **Hide helper tables** from Report view: In Model view,
      right-click these tables → "Hide in report view":
  - WaterfallSteps
  - WindowWeeks (the table, not the slicer)
  - TargetAllInRate (the table, not the slicer)
- [ ] **Save**: Ctrl+S
