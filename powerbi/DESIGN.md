# Power BI Dashboard — Design Specification

---

## Design Philosophy

The Excel workbook and the Power BI dashboard serve different jobs.
The workbook is the interactive deliverable — seven tabs of detail,
adjustable inputs, auto-filtered ledgers. A prospect opens it after
the meeting, drills into their data, adjusts parameters, builds
conviction. The workbook is where analysis happens.

The dashboard is the presentation layer. It is what you show in the
meeting. It answers four questions in four pages, with the answer
stated on-screen in plain English so no one has to derive it from a
chart. Each page has one hero visual, one or two supporting elements,
and enough white space to focus attention. If someone wants the
underlying table, that's what the workbook is for.

This separation follows the decision in DECISIONS.md: Power BI adds
value only where it does something Excel cannot — cross-filtering,
scatter distributions, side-by-side comparison at a glance. Every
visual in this spec justifies the interactive medium. Nothing is
here because "dashboards should have charts."

### Design rules

1. **One takeaway per page.** The answer is a sentence, not a chart.
   The chart is evidence.
2. **Maximum 3 visuals per page.** One hero (large, center), one or
   two supporting (smaller, flanking). No tables unless the table IS
   the insight.
3. **White space is a feature.** A page with one chart, two KPIs, and
   a sentence of text in a well-balanced layout looks more professional
   than six packed visuals.
4. **Narrative text boxes.** Each page gets a 1–2 sentence takeaway —
   a finding, not a title. Declarative, specific, data-forward.
5. **Color encodes meaning.** Blue (`#2E5090`) = revenue/neutral data.
   Red (`#C44E52`) = waste/loss. Green (`#4C9A6E`) = positive outcome.
   Gray (`#8C8C8C`) = reference/context. No gradients, no 3D, no
   decoration.
6. **KPI cards: fewer, bigger.** 2–3 per page maximum. Large enough to
   read from across a conference table.

---

## Page 1: "The Gap"

**Question answered:** How much is Cinderhaven spending on trade, and
how much of that is unplanned?

### Takeaway text

> Cinderhaven budgets 17.3% of revenue for trade spend — $4.4 million
> in negotiated rate-card allowances. Actual all-in cost is 21.3%.
> The 4-point gap is $1 million in annual operational waste: retailer
> deductions beyond the rate card, largely uncontested.

Position: top of page, below the title strip. Full width. Segoe UI,
12pt, `#333333`. This is the first thing someone reads.

### Hero visual — Margin Erosion Waterfall

The single most important chart in the dashboard. It shows $25.6M in
revenue eroding through two layers of trade cost to a net position.

| Property | Value |
|----------|-------|
| Type | Waterfall chart |
| Position | Center, below takeaway text. Full width, ~60% of page height |
| Category axis | `WaterfallSteps[Step]` — "Revenue", "Structural Trade", "Operational Waste" |
| Values | Measure: `WaterfallValue` |
| Sort | By `WaterfallSteps[SortOrder]` ascending |
| Colors | Increase (Revenue): `#2E5090`. Decrease (Structural, Operational): `#C44E52`. Total bar: `#4C9A6E` |
| Data labels | ON, Segoe UI 10pt, `$#,##0` format |
| Legend | OFF (single series) |
| Gridlines | OFF or `#F0F0F0` |

### Supporting — KPI cards (3)

Three cards in a row below the waterfall, right-aligned or centered.
Large format: 28pt values, 10pt labels.

| Card | Measure | Display value | Purpose |
|------|---------|---------------|---------|
| 1 | `AllInTradeRate` | 21.3% | The headline rate — the number that should be 17.3% |
| 2 | `OperationalWasteAmount` | ~$1,012,455 | The dollar cost of the gap |
| 3 | `RecoveryRate` | 14.3% | How much is being recovered today |

### What was removed (vs. prior design)

| Visual | Reason | Where it lives now |
|--------|--------|--------------------|
| Revenue by Retailer column chart | Revenue breakdown is context, not the takeaway. Distracts from the gap story | Workbook Tab 1 (revenue column), Dashboard Page 4 (revenue share) |
| Retailer Summary table (6 columns) | Tables are workbook territory. This page answers one question — the gap | Workbook Tab 1 (responsibility matrix), Tab 4 (full P&L) |
| KPI cards for TotalRevenue, StructuralTradeRate | Revenue is visible in the waterfall. Structural rate is stated in the takeaway text | Workbook Tab 1 |

### Slicers

None. This page presents the portfolio-level punchline. Filtering
by retailer is Page 4's job.

---

## Page 2: "Where the Waste Goes"

**Question answered:** What categories of deductions make up the $1M
in operational waste?

### Takeaway text

> Three categories account for two-thirds of operational waste: vague
> deductions ($294K), label fines ($197K), and short-ship charges
> ($184K). Three deductions totaling $19,306 are confirmed
> double-payments — the same promotion billed twice through different
> mechanisms.

Position: top of page, below title strip. Full width.

### Hero visual — Waste Category Ranking

A single horizontal bar chart showing all 8 deduction categories,
largest to smallest. The shape of the distribution — dominated by
three categories — is the insight.

| Property | Value |
|----------|-------|
| Type | Horizontal bar chart (barChart) |
| Position | Center, below takeaway text. Full width, ~55% of page height |
| Y-axis (category) | `fact_deductions[standardized_category]` |
| X-axis (value) | Measure: `WasteAmount` |
| Sort | Descending by `WasteAmount` |
| Bar color | `#C44E52` (waste = red) |
| Data labels | ON, outside end, Segoe UI 9pt, `$#,##0` format |
| X-axis labels | `#666666`, Segoe UI 9pt |
| Gridlines | OFF |
| Legend | OFF |
| Visual filter | `fact_deductions[deduction_type] <> "promo_billback"` (operational waste only) |

### Supporting — KPI cards (3)

Three cards in a row below the bar chart.

| Card | Measure | Display value | Purpose |
|------|---------|---------------|---------|
| 1 | `OperationalWasteAmount` | ~$1,012,455 | Total operational waste (anchors the bar chart) |
| 2 | `DoubleDipTotal` | $19,306 | Double-payment finding — small dollars, significant process gap |
| 3 | `UnmappedCodeCount` | 292 | Data quality — deductions with no crosswalk translation |

### What was removed (vs. prior design)

| Visual | Reason | Where it lives now |
|--------|--------|--------------------|
| Deductions by Retailer bar chart | Which retailers generate waste is Page 4's story. This page answers where, not who | Dashboard Page 4 (deduction share), Workbook Tab 2 |
| Deduction Detail by Retailer table | Detailed breakdowns belong in the workbook. This page has one chart | Workbook Tab 2 (leak diagnostic matrix), Tab 5 (full ledger) |
| DeductionCount KPI card | Count is less meaningful than dollars in a presentation. The 2,374 number is in the workbook | Workbook Tab 2 |
| AvgDaysToResolve KPI card | Resolution speed is an operational metric, not a presentation insight | Workbook Tab 5 (ledger, sortable by days_outstanding) |

### Slicers

None. The waste breakdown is a portfolio-level finding. Per-retailer
filtering lives on Page 4.

---

## Page 3: "Which Promos Work"

**Question answered:** What share of promotions generate positive ROI,
and how much promotional spend is unaccounted for?

### Takeaway text

> Of 160 measurable promotions, 104 destroyed value — the cost
> exceeded the incremental revenue. 137 promo-billback deductions
> totaling $95,826 reference promotions that don't appear in the
> planning calendar.

Position: top of page, below title strip. Full width.

### Hero visual — Promo Cost vs. Incremental Revenue Scatter

This is the visual that justifies Power BI over Excel. 160 data
points on a cost-vs-lift plane, with a diagonal breakeven line
separating winners from losers. The clustering pattern — most
promotions in the low-cost/negative-lift quadrant — is invisible
in a 188-row spreadsheet.

| Property | Value |
|----------|-------|
| Type | Scatter chart |
| Position | Center-left, below takeaway text. ~65% width, ~55% height |
| X-axis | Measure: `PromoCost` |
| Y-axis | Measure: `IncrementalRevenue` |
| Detail | `dim_promo[promo_id]` (one dot per promo) |
| Legend | `dim_promo[promo_type]` (TPR, Feature, Display, BOGO) |
| Size | `dim_promo[duration_weeks]` |
| Analytics | Constant line at Y=0. Trend line optional |
| Visual filter | Exclude rows where IncrementalRevenue is blank |
| Dot colors | By promo_type: TPR `#2E5090`, Feature `#8C8C8C`, Display `#4C9A6E`, BOGO `#F4A940` |
| Gridlines | Light, `#F0F0F0` |
| Axis labels | Segoe UI 9pt, `#666666` |

### Supporting — KPI cards (3)

Right side of the scatter or below it. Stacked vertically if right-
side, horizontal if below.

| Card | Measure | Display value | Purpose |
|------|---------|---------------|---------|
| 1 | `AvgROI` | ~0.85 | Portfolio average ROI — below breakeven |
| 2 | `GhostPromoCount` | 137 | Unmatched promo deductions — process gap indicator |
| 3 | `GhostPromoTotal` | $95,826 | Dollar exposure from ghost promos |

### Supporting — Data Quality Donut

Small donut chart showing how many promotions have sufficient data
for ROI measurement.

| Property | Value |
|----------|-------|
| Type | Donut chart |
| Position | Below KPI cards or bottom-right. Small (~250×200px) |
| Category | `dim_promo[data_quality]` |
| Values | Measure: `PromoCount` |
| Slice colors | Full: `#4C9A6E`, Partial: `#F4A940`, No POS: `#C44E52` |
| Labels | Category name + percentage |
| Inner radius | 50% |
| Title | "POS Data Coverage" |

### What was removed (vs. prior design)

| Visual | Reason | Where it lives now |
|--------|--------|--------------------|
| Promo Spend by Retailer bar chart | Redundant with Page 4's retailer-level view. This page is about promo quality, not retailer allocation | Workbook Tab 3 (promo table, sortable by retailer) |
| Promo Performance table (6 columns) | 188-row tables belong in the workbook. The scatter shows the distribution; the table adds nothing in a presentation | Workbook Tab 3 (full promo table with ROI, data quality, cost source) |
| ROI histogram | The scatter already shows the distribution. Two distribution charts on one page is redundant | Workbook Tab 3 (sortable ROI column) |
| WindowWeeks slicer | What-if baseline adjustment is a workbook feature. The dashboard uses the default 4-week baseline | Workbook Tab 3 (adjustable window parameter cell) |

### Slicers

None. The scatter shows the full portfolio. Filtering by retailer or
promo type is available via cross-filtering (click a legend entry to
highlight that promo type).

---

## Page 4: "The Retailer Problem"

**Question answered:** Which retailers generate the most margin
erosion, and where does revenue concentration create risk?

### Takeaway text

> Net-net margin ranges from 33.8% (Mountain Pantry Co) to 12.5%
> (Walmart). Walmart contributes 51% of revenue but its 21.5%
> structural rate compresses margin to less than half the portfolio
> average.

Position: top of page, below title strip. Full width.

### Hero visual — Net-Net Margin by Retailer

A single vertical bar chart showing every retailer's effective
margin after all trade costs. Sorted descending, colored by margin
tier. The shape — DTC at 62.5%, regionals clustered at 28–34%,
Walmart at the bottom — tells the story.

| Property | Value |
|----------|-------|
| Type | Clustered column chart |
| Position | Center, below takeaway text. Full width, ~50% of page height |
| X-axis (category) | `dim_retailer[retailer_name]` |
| Y-axis (value) | Measure: `NetNetMarginPct` |
| Sort | Descending by `NetNetMarginPct` |
| Data labels | ON, outside end, format `0.0%` |
| Conditional colors | > 30%: `#4C9A6E` (green). 15–30%: `#2E5090` (blue). < 15%: `#C44E52` (red) |
| Gridlines | OFF |
| Legend | OFF |
| Axis labels | Segoe UI 9pt, `#666666` |
| Analytics | Constant line at portfolio average margin, dashed, `#8C8C8C` |

### Supporting — Concentration Risk Bars

Revenue share vs. deduction share for the top retailers. The
mismatch — when a retailer's share of deductions exceeds its share
of revenue — is the concentration risk insight.

| Property | Value |
|----------|-------|
| Type | Clustered bar chart (horizontal) |
| Position | Bottom-left, ~55% width, ~30% height |
| Y-axis | `dim_retailer[retailer_name]` (top 5–6 retailers by revenue) |
| X-axis | Measures: `RevenueShare`, `DeductionShare` |
| Colors | Revenue: `#2E5090`, Deductions: `#C44E52` |
| Sort | Descending by `RevenueShare` |
| Data labels | ON, format `0.0%` |
| Legend | Top, Segoe UI 9pt |
| Visual filter | Top N = 6 by TotalRevenue (reduces noise from small retailers) |

### Supporting — KPI card (1)

| Card | Measure | Display value | Purpose |
|------|---------|---------------|---------|
| 1 | `HighestRiskRetailer` | (retailer name) | Names the retailer with the lowest net-net margin. Red text (`#C44E52`), prominent position |

Position: bottom-right, large card. Callout value in `#C44E52`
(red) at 28pt. Category label "Highest Risk Retailer" in 10pt
`#666666`.

### What was removed (vs. prior design)

| Visual | Reason | Where it lives now |
|--------|--------|--------------------|
| Retailer Margin Comparison table (8 columns) | This is the workbook's centerpiece (Tab 4). Duplicating it here adds visual noise without adding insight — the bar chart shows the ranking | Workbook Tab 4 (full P&L with all rate columns) |
| TargetAllInRate what-if slicer | What-if scenario modeling is a workbook feature. The dashboard presents findings, not tools | Workbook Tab 4 (yellow input cells for per-retailer target rates) |
| SavingsAtTarget / TotalSavingsAtTarget cards | Depends on the removed what-if slicer. The savings calculation is in the workbook | Workbook Tab 4 (savings column, updates with target rate input) |
| Per-Retailer Waterfall (small multiples) | Visually impressive but requires explanation. The margin bar chart delivers the same ranking more clearly | Could be added back as a drill-through detail page if needed |
| 100% Stacked bar (margin composition) | Shows the same data as the margin bar chart but harder to read. One view is enough | Workbook Tab 4 (margin composition columns) |

### Slicers

None. This page presents the full portfolio comparison. The workbook
is where per-retailer drill-in happens.

---

## What Moved to the Workbook

Every visual and table removed from the dashboard exists in the
workbook. This is by design — the dashboard presents findings, the
workbook supports investigation.

| Removed visual | Was on page | Workbook location |
|----------------|-------------|-------------------|
| Revenue by Retailer column chart | Page 1 | Tab 1: revenue column in responsibility matrix |
| Retailer Summary table | Page 1 | Tab 1: responsibility matrix; Tab 4: full P&L |
| Deductions by Retailer bar chart | Page 2 | Tab 2: retailer rows in leak diagnostic |
| Deduction Detail table | Page 2 | Tab 5: full 2,374-row ledger with auto-filters |
| Promo Spend by Retailer bar chart | Page 3 | Tab 3: promo table, sortable by retailer |
| Promo Performance table | Page 3 | Tab 3: full 188-row promo table |
| ROI histogram | Page 3 | Tab 3: sortable ROI column |
| Retailer Margin Comparison table | Page 4 | Tab 4: full P&L with 8 columns per retailer |
| What-if slicer + savings cards | Page 4 | Tab 4: yellow input cells for target trade rates |
| Per-retailer waterfall (small multiples) | Page 4 | No direct equivalent — margin bar chart replaces |
| Margin composition stacked bar | Page 4 | Tab 4: rate breakdown columns |

---

## DAX Measures — Dashboard Usage

Measures are retained in `generate_pbix_model.py` for compatibility
with the workbook and future use. The following are **no longer
directly visualized** in the dashboard but remain in the model.

### Still used on the dashboard

| Measure | Page | Visual |
|---------|------|--------|
| `WaterfallValue` | 1 | Waterfall (hero) |
| `AllInTradeRate` | 1 | KPI card |
| `OperationalWasteAmount` | 1, 2 | KPI card |
| `RecoveryRate` | 1 | KPI card |
| `TotalRevenue` | — | Dependency of WaterfallValue, AllInTradeRate |
| `StructuralTradeAmount` | — | Dependency of WaterfallValue, AllInTradeCost |
| `AllInTradeCost` | — | Dependency of AllInTradeRate |
| `WasteAmount` | 2 | Bar chart (hero) |
| `DoubleDipTotal` | 2 | KPI card |
| `DoubleDipCount` | 2 | KPI card (secondary) |
| `UnmappedCodeCount` | 2 | KPI card |
| `PromoCost` | 3 | Scatter X-axis |
| `IncrementalRevenue` | 3 | Scatter Y-axis |
| `AvgROI` | 3 | KPI card |
| `GhostPromoCount` | 3 | KPI card |
| `GhostPromoTotal` | 3 | KPI card |
| `PromoCount` | 3 | Donut values |
| `FullDataCount` | 3 | Donut (data quality) |
| `PartialDataCount` | 3 | Donut (data quality) |
| `NoPOSCount` | 3 | Donut (data quality) |
| `NetNetMarginPct` | 4 | Bar chart (hero) |
| `NetNetMargin` | — | Dependency of NetNetMarginPct |
| `GrossMarginPct` | — | Dependency of NetNetMargin |
| `StructuralRate` | — | Dependency of NetNetMargin |
| `OpDedRate` | — | Dependency of NetNetMargin |
| `PromoBBRate` | — | Dependency of NetNetMargin |
| `RevenueShare` | 4 | Concentration risk bars |
| `DeductionShare` | 4 | Concentration risk bars |
| `HighestRiskRetailer` | 4 | KPI card |

### Not visualized in dashboard (retained for workbook / future use)

| Measure | Was on | Reason removed |
|---------|--------|----------------|
| `RetailerRevenue` | Page 1 | Revenue by Retailer chart removed |
| `StructuralTradeRate` | Page 1 | KPI removed — rate is in takeaway text |
| `OperationalWasteRate` | Page 1 | KPI removed — dollar amount used instead |
| `DeductionCount` | Page 2 | KPI removed — dollars more meaningful than counts |
| `DeductionAmount` | Page 2 | Replaced by WasteAmount (excludes promo_billback) |
| `DisputeCount` | Page 1 | Multi-row card removed |
| `TotalRecovered` | Page 1 | Multi-row card removed |
| `AvgDaysToResolve` | Page 2 | Operational detail, not presentation insight |
| `PromoROI` | Page 3 | Histogram removed — scatter shows distribution |
| `PromoROIDynamic` | Page 3 | Dynamic measures removed with what-if slicer |
| `BaselineVolume` | Page 3 | Detail metric, not visualized |
| `BaselineVolumeDynamic` | Page 3 | Dynamic measures removed with what-if slicer |
| `IncrementalRevenueDynamic` | Page 3 | Dynamic measures removed with what-if slicer |
| `Revenue` (Page 4) | Page 4 | Table removed |
| `SavingsAtTarget` | Page 4 | What-if slicer removed |
| `TotalSavingsAtTarget` | Page 4 | What-if slicer removed |
| `RetailerWaterfallValue` | Page 4 | Small multiples waterfall removed |
| `WindowWeeks Value` | Page 3 | What-if slicer removed |
| `TargetAllInRate Value` | Page 4 | What-if slicer removed |

### Calculated tables — dashboard usage

| Table | Status |
|-------|--------|
| `WaterfallSteps` | **Used** — Page 1 waterfall category axis |
| `dim_date` | **Used** — model relationships |
| `WindowWeeks` | **Not visualized** — what-if slicer removed |
| `TargetAllInRate` | **Not visualized** — what-if slicer removed |

---

## Visual Count Summary

| Page | Title | Hero | Supporting | KPIs | Total visuals |
|------|-------|------|------------|------|---------------|
| 1 | The Gap | 1 waterfall | — | 3 | 4 |
| 2 | Where the Waste Goes | 1 bar chart | — | 3 | 4 |
| 3 | Which Promos Work | 1 scatter | 1 donut | 3 | 5 |
| 4 | The Retailer Problem | 1 column chart | 1 bar chart | 1 | 3 |
| **Total** | | **4** | **2** | **10** | **16** |

Prior design: 28 visuals across 4 pages. New design: 16 visuals
(plus 4 text boxes for takeaway text). The reduction is intentional.
