# Power BI Dashboard — Design Specification

4 pages. Every visual must justify the interactive medium — no
replicated Excel charts.

---

## Page 1: Executive Overview

**Purpose:** The same two-bucket punchline as Tab 1, but with
cross-filtering that lets a CEO click a retailer and instantly see
how the waterfall, waste breakdown, and KPIs change for that retailer
alone.

**Corresponding workbook tab:** Tab 1 (Executive Pulse) — static KPI
trio, static waterfall chart, static responsibility matrix. All values
are portfolio-wide with no ability to filter.

**Power BI value-add:** Cross-filter the waterfall by clicking a
retailer in the bar chart. In Excel, the waterfall shows one fixed
portfolio view. In Power BI, clicking "Walmart" redraws the waterfall
for Walmart's revenue → structural trade → operational waste → net
after trade. This is impossible in Excel without VBA or separate
worksheets per retailer.

### Visuals

| # | Visual type | Fields | Purpose |
|---|-------------|--------|---------|
| 1 | KPI card | Measure: `AllInTradeRate` (21.3%) | Headline metric — all-in trade rate |
| 2 | KPI card | Measure: `StructuralTradeRate` (17.3%) | Planned trade rate |
| 3 | KPI card | Measure: `OperationalWasteRate` (4.0%) | Waste rate |
| 4 | KPI card | Measure: `TotalRevenue` ($25.6M) | Revenue context |
| 5 | Waterfall chart | Categories: [Revenue, Structural Trade, Operational Waste, Net After Trade]; Values: measure `WaterfallValue` | Shows margin erosion; redraws when retailer slicer is active |
| 6 | Clustered bar chart | Axis: `deductions[deduction_type]`; Values: measure `WasteAmount`; Legend: none | Waste breakdown — clicking a bar cross-filters the waterfall and KPIs to show that category's contribution |
| 7 | Donut chart | Legend: `dim_retailer[retailer]`; Values: measure `RetailerRevenue` | Revenue share — clicking a segment cross-filters everything on the page |
| 8 | Multi-row card | Measures: `RecoveryRate`, `DisputeCount`, `TotalRecovered` | Recovery snapshot — updates when filtered by retailer |

### Slicers

| Slicer | Field | Type | Default |
|--------|-------|------|---------|
| Retailer | `dim_retailer[retailer]` | Dropdown multi-select | All selected |
| Date range | `dim_date[date]` | Between slider | Trailing 365 days |

### Drill-through

- Right-click any retailer segment in the donut → drills to **Page 4:
  Retailer Comparison**, pre-filtered to that retailer.
- Right-click any deduction type bar → drills to **Page 2: Deduction
  Deep-Dive**, pre-filtered to that category.

### Conditional formatting

- KPI cards: `OperationalWasteRate` uses red background when > 5%,
  yellow when 3–5%, green when < 3%.
- Waterfall chart: "Structural Trade" and "Operational Waste" segments
  use red fill; "Revenue" and "Net After Trade" use blue.

---

## Page 2: Deduction Deep-Dive

**Purpose:** Investigate deductions by time, retailer, category, and
individual record — with drill-through to the specific deduction rows
that drove a spike.

**Corresponding workbook tabs:** Tab 2 (Leak Diagnostic) — static
category table with totals; Tab 5 (Deduction Ledger) — flat 2,374-row
table with auto-filters; Tab 6 (Deduction Code Crosswalk) — static
reference. In Excel, you can filter the ledger but you cannot see
time trends, cannot click a category to see only its deductions, and
cannot visualize spikes.

**Power BI value-add:** Time-series line chart of deductions by month
with category overlay. Excel Tab 2 shows totals only — no time
dimension. In Power BI, an analyst can spot a spike in "short_ship"
deductions in November, click that data point, and the table below
instantly filters to show only November short-ship deductions with
full detail. This exploratory pattern is impossible in a static Excel
table.

### Visuals

| # | Visual type | Fields | Purpose |
|---|-------------|--------|---------|
| 1 | Area chart (stacked) | Axis: `dim_date[year_month]`; Values: measure `DeductionAmount`; Legend: `deductions[deduction_type]` | Time trend of deductions by category — shows seasonal patterns and spikes that the workbook totals hide |
| 2 | Treemap | Group: `deductions[deduction_type]`; Values: measure `DeductionAmount` | Proportional category breakdown — clicking a block filters the page |
| 3 | Matrix | Rows: `deductions[deduction_type]`; Columns: `dim_retailer[retailer]`; Values: measure `DeductionAmount` | Cross-tab: which retailers generate which types of waste. Heat-map conditional formatting shows concentrations |
| 4 | Table (detail) | Columns: `deduction_id`, `deduction_date`, `retailer`, `translated_code`, `deduction_type`, `amount`, `dispute_outcome`, `recovered_amount` | Drill-through target — shows individual deduction records filtered by page context |
| 5 | KPI card | Measure: `DoubleDipCount` (3) and `DoubleDipTotal` ($19,306) | Double-dip alert — persistent callout |
| 6 | Card | Measure: `UnmappedCodeCount` (292) | Data quality indicator — deductions missing crosswalk translation |

### Slicers

| Slicer | Field | Type | Default |
|--------|-------|------|---------|
| Retailer | `dim_retailer[retailer]` | Dropdown multi-select | All |
| Deduction type | `deductions[deduction_type]` | Checkbox list | All |
| Date range | `dim_date[date]` | Between slider | Trailing 365 days |
| Vague flag | `deductions[is_vague]` | Single-select (Yes/No/All) | All |

### Drill-through

- This page IS the drill-through target from Page 1's category bar
  chart. Arriving here pre-filters to the selected `deduction_type`.
- Right-click a row in the detail table → drills to a tooltip page
  showing full deduction metadata (remittance description, order ref,
  shipment ref, crosswalk translation).

### Conditional formatting

- Matrix cells: 3-color gradient (white → yellow → red) based on
  `DeductionAmount` value.
- Detail table `dispute_outcome` column: green for `won_full`,
  yellow for `won_partial`, red for `lost`, gray for `pending`.
- Area chart: each deduction type uses a consistent color across all
  pages (defined in theme JSON).

---

## Page 3: Promo Performance

**Purpose:** Evaluate which promotions created value and which
destroyed it, with the ability to filter by retailer, promo type,
and funding mechanism — and drill through to individual promo detail.

**Corresponding workbook tab:** Tab 3 (Promo Efficacy) — 188-row table
with formula-based ROI, adjustable window parameter, ghost promo
section. In Excel, you can sort and filter the table, but you cannot
visualize the portfolio distribution, cannot see cost-vs-lift
relationships, and cannot compare across retailers simultaneously.

**Power BI value-add:** Scatter plot of promo cost vs. incremental
revenue, with quadrant reference lines. In Excel, 188 rows of numbers
hide the distribution — you can't see at a glance that most promotions
cluster in the low-cost/low-lift quadrant while 5 outliers drive
disproportionate value. The scatter makes portfolio-level patterns
visible and clickable. Additionally, a parameter slicer for the
pre-period window (1–8 weeks) lets an analyst adjust the baseline
calculation and watch the scatter redraw — something the workbook does
with a single input cell that requires manual inspection of each row.

### Visuals

| # | Visual type | Fields | Purpose |
|---|-------------|--------|---------|
| 1 | Scatter chart | X-axis: measure `PromoCost` (actual or planned); Y-axis: measure `IncrementalRevenue`; Size: `promotions[duration_weeks]`; Color: `promotions[promo_type]`; Detail: `promotions[promo_id]` | Cost vs. value — quadrant lines at ROI = 1.0 separate winners from losers |
| 2 | Histogram | Axis: bins of measure `PromoROI` (width 0.5); Values: count of promos | ROI distribution — shows how many promos are above/below breakeven |
| 3 | Clustered bar | Axis: `promotions[promo_type]`; Values: measure `AvgROI`, measure `PromoCount` | Average ROI by promo type — identifies which promotion strategies work |
| 4 | Card cluster | Measures: `GhostPromoCount` (137), `GhostPromoTotal` ($95,826) | Ghost promo callout — persistent warning about unmatched deductions |
| 5 | Table (detail) | Columns: `promo_id`, `retailer`, `sku`, `promo_type`, `start_week`, `planned_cost`, `actual_cost`, `incremental_revenue`, `roi`, `data_quality` | Drill-through target — individual promo detail |
| 6 | Card | Measures: `FullDataCount`, `PartialDataCount`, `NoPOSCount` | Data coverage summary |

### Slicers

| Slicer | Field | Type | Default |
|--------|-------|------|---------|
| Retailer | `dim_retailer[retailer]` | Dropdown multi-select | All |
| Promo type | `promotions[promo_type]` | Checkbox list | All |
| Funding mechanism | `promotions[funding_mechanism]` | Checkbox list | All |
| Data quality | `promo_detail[data_quality]` | Single-select (Full/Partial/No POS/All) | All |
| Pre-period window | What-if parameter `WindowWeeks` (1–8) | Numeric slider | 4 |

### Drill-through

- Right-click any dot in the scatter → drills to the detail table
  showing that promo's full record plus the weekly volume profile
  (pre, during, post).
- Right-click a promo_type bar → filters the scatter to show only
  that type.

### Conditional formatting

- Scatter: quadrant shading — green fill behind top-right (ROI > 1,
  revenue > median), red fill behind bottom-left (ROI < 1, low revenue).
- Detail table `roi` column: green > 1.5, yellow 0.8–1.5, red < 0.8.
- Detail table `data_quality`: green "Full", yellow "Partial", red "No POS".

---

## Page 4: Retailer Comparison

**Purpose:** Compare retailers side-by-side on margin erosion, trade
cost composition, and what-if scenarios — with a what-if parameter
that Power BI handles natively but Excel requires formula gymnastics.

**Corresponding workbook tab:** Tab 4 (Retailer Risk) — static P&L
table, two bar charts (concentration risk, margin erosion), what-if
section with yellow input cells. In Excel, what-if requires manually
changing each input cell and eyeballing the result. You cannot compare
two different target scenarios simultaneously.

**Power BI value-add:** What-if parameter slider for target all-in
trade rate, with a calculated measure showing savings at the selected
rate across all retailers simultaneously. In Excel, each retailer has
its own yellow input cell — you can't batch-change them or see the
portfolio savings at a uniform target. Power BI's what-if parameter
applies one target rate and instantly shows which retailers generate
the most savings at that rate, sorted dynamically. Also: small
multiples — one mini-chart per retailer showing their margin waterfall
— which would require 10 separate Excel charts.

### Visuals

| # | Visual type | Fields | Purpose |
|---|-------------|--------|---------|
| 1 | Stacked bar (100%) | Axis: `dim_retailer[retailer]`; Values: measures `StructuralRate`, `OpDedRate`, `PromoBBRate`, `NetNetMargin` | Margin composition — shows how each retailer's gross margin erodes through trade layers. 100% stacking makes proportions comparable regardless of revenue size |
| 2 | Clustered bar | Axis: `dim_retailer[retailer]`; Values: measures `RevenueShare`, `DeductionShare` | Concentration risk — retailers taking more deduction share than revenue share are overrepresented risks |
| 3 | Waterfall chart (small multiples) | One waterfall per retailer; Steps: Gross Margin → After Structural → Net-Net | Margin erosion per retailer — small multiples layout impossible in Excel |
| 4 | Table | Rows: `dim_retailer[retailer]`; Values: `Revenue`, `GrossMarginPct`, `StructuralRate`, `OpDedRate`, `NetNetMarginPct`, `SavingsAtTarget` | P&L summary with dynamic savings column |
| 5 | Card | Measure: `TotalSavingsAtTarget` | Portfolio savings at the selected target rate |
| 6 | Card | Measure: `HighestRiskRetailer` (retailer with lowest net-net margin) | Risk callout |

### Slicers

| Slicer | Field | Type | Default |
|--------|-------|------|---------|
| Target trade rate | What-if parameter `TargetAllInRate` (0%–50%) | Percentage slider | 18% |
| Exclude DTC | `dim_retailer[retailer]` | Pre-filter removing DTC (zero-trade benchmark) | DTC excluded |

### Drill-through

- This page IS the drill-through target from Page 1's donut chart.
  Arriving here pre-filters to the selected retailer.
- Right-click any retailer in the stacked bar → drills to **Page 2:
  Deduction Deep-Dive** filtered to that retailer's deductions.

### Conditional formatting

- Stacked bar: consistent colors per layer (blue = gross, yellow =
  structural trade, orange = operational, red = promo billback,
  green = remaining net-net).
- Table `NetNetMarginPct` column: red < 15%, yellow 15–25%, green > 25%.
- Table `SavingsAtTarget` column: data bars showing relative magnitude.
- Concentration risk bars: red outline on retailers where
  `DeductionShare` > `RevenueShare` (overrepresented risk).

---

## Cross-Page Navigation

- Page tab strip at the bottom (standard Power BI).
- Bookmark buttons in a top navigation strip: "Overview", "Deductions",
  "Promos", "Retailers" — styled as tab-like buttons for the CEO
  audience who expects workbook-like navigation.
- "Back to Overview" button on Pages 2–4 for returning from drill-through.

---

## Value-Add Summary (vs. Excel)

| # | Feature | Page | Why Excel can't do this |
|---|---------|------|------------------------|
| 1 | Cross-filter waterfall by retailer | Page 1 | Excel waterfall is static; separate worksheets per retailer would be needed |
| 2 | Time-series deduction trend with click-to-filter | Page 2 | Excel Tab 2 shows totals only, no time axis; Tab 5 is a flat table with no visualization |
| 3 | Scatter plot with quadrant lines + click-through | Page 3 | 188 rows of numbers hide distribution patterns; Excel scatter exists but can't filter the page on click |
| 4 | What-if parameter slider applied to all retailers simultaneously | Page 4 | Excel requires one input cell per retailer; batch comparison is manual |
| 5 | Small multiples (per-retailer waterfall) | Page 4 | Would require 10 separate Excel charts with no linked scaling |
| 6 | Drill-through from summary to detail | Pages 1→2, 1→4, 3→detail, 4→2 | Excel hyperlinks can navigate but can't pre-filter the destination to the clicked context |

---

## Data Model Requirements (for `powerbi/data/` export task)

Tables needed:

| Table | Source | Key columns for visuals |
|-------|--------|------------------------|
| `fact_scan_data` | scan_data (trailing 52w) | week_ending, store_id, sku, dollars_sold, units_sold |
| `fact_deductions` | deductions (trailing 365d) + deduction_codes join | deduction_id, deduction_date, retailer_id, deduction_type, amount, translated_code, is_vague, is_double_dip, dispute_outcome, recovered_amount |
| `fact_promotions` | promotions + promo performance calc | promo_id, sku, retailer, promo_type, start_week, end_week, planned_cost, actual_cost, incremental_revenue, roi, data_quality, funding_mechanism |
| `dim_retailer` | stores (distinct retailers) + sku_costs rates + computed margins | retailer, channel_type, trade_rate, gross_margin, structural_trade_dollars, op_deductions, net_net_margin |
| `dim_date` | generated calendar | date, year, month, year_month, week_ending, is_trailing_52w, is_trailing_365d |
| `dim_sku` | sku_costs | sku, brand, category, cogs_per_unit |
| `crosswalk` | deduction_codes | retailer_id, code, name, deduction_type, status |

Relationships:
- `fact_scan_data[store_id]` → join via stores to `dim_retailer[retailer]`
- `fact_scan_data[week_ending]` → `dim_date[week_ending]`
- `fact_scan_data[sku]` → `dim_sku[sku]`
- `fact_deductions[retailer_id]` → `dim_retailer[retailer]` (via slug normalization)
- `fact_deductions[deduction_date]` → `dim_date[date]`
- `fact_promotions[retailer]` → `dim_retailer[retailer]`
- `fact_promotions[sku]` → `dim_sku[sku]`
