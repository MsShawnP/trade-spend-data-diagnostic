# Power BI Dashboard — Cinderhaven Trade Spend

Interactive companion to the Excel diagnostic workbook. Same data,
different medium: cross-filtering, drill-through, time-series trends,
and what-if parameters that Excel can't do well. 4 pages covering the
full diagnostic narrative — executive overview, deduction deep-dive,
promo performance, and retailer comparison.

---

## Data Model

Star schema with 7 exported tables plus 4 calculated tables created
in Power BI.

### Exported Tables (from `powerbi/data/`)

| Table | Rows | Purpose |
|-------|------|---------|
| dim_retailer | 11 | Retailer attributes, pre-computed trade rates and margins |
| dim_product | 90 | SKU attributes and per-channel wholesale prices |
| dim_promo | 188 | Promotions with pre-computed ROI, lift, and data quality |
| fact_deductions | 2,374 | Trailing-365-day deductions with code translations and dispute status |
| fact_structural_trade | 10 | Per-retailer structural trade using channel-average rates |
| fact_scan_data | 601,341 | Weekly POS data tagged with promo period (pre/during/post) |
| fact_disputes | 1,410 | Dispute records with outcomes and resolution metrics |

### Calculated Tables (created in Power BI)

| Table | Purpose |
|-------|---------|
| dim_date | Calendar dimension for date slicers and time-series grouping |
| WaterfallSteps | Category labels for waterfall charts |
| WindowWeeks | What-if parameter (1–8) for promo baseline window |
| TargetAllInRate | What-if parameter (0–50%) for trade rate target |

Full column definitions: [`DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).
Relationship diagram and setup: [`BUILD_GUIDE.md`](BUILD_GUIDE.md) § 4.

---

## Value-Add Over Excel

Six features that justify the interactive medium — each one is
impossible or impractical in the static workbook.

1. **Cross-filter waterfall by retailer** (Page 1). Click a retailer
   in the donut chart and the margin erosion waterfall redraws for
   that retailer alone. The workbook shows one fixed portfolio view.

2. **Time-series deduction trend with click-to-filter** (Page 2).
   Stacked area chart of deductions by month and category. Spot a
   spike, click it, and the detail table filters to those exact
   records. The workbook has totals only — no time axis.

3. **Scatter plot with quadrant lines** (Page 3). 188 promotions
   plotted by cost vs. incremental revenue. Quadrant reference lines
   separate winners from losers. Click a dot to drill through to the
   promo detail. The workbook is a flat table that hides distribution
   patterns.

4. **What-if parameter slider for all retailers** (Page 4). Set a
   target all-in trade rate and instantly see savings across every
   retailer. The workbook requires manually changing one input cell
   per retailer.

5. **Small multiples waterfall** (Page 4). One mini-waterfall per
   retailer showing margin erosion side by side with linked scaling.
   Would require 10 separate Excel charts.

6. **Drill-through from summary to detail** (Pages 1→2, 1→4, 4→2).
   Right-click any visual element and navigate to the detail page
   pre-filtered to that context. Excel hyperlinks can navigate but
   can't pre-filter.

---

## How to Refresh Data

When the underlying SQLite database is updated:

```
python powerbi/export_data.py
```

This re-exports all 7 CSVs from the current database state. Then
in Power BI Desktop: Home → Refresh. All data and calculated tables
update automatically.

The export script validates against locked numbers on every run
(revenue, structural trade, operational waste, deduction count,
dispute count, recovered amount).

---

## Key Measures

34 DAX measures organized by page. Summary below; full formulas in
[`DAX_MEASURES.md`](DAX_MEASURES.md).

### Global

| Measure | What it calculates |
|---------|--------------------|
| TotalRevenue | Sum of scan data dollars ($25.6M) |
| StructuralTradeAmount | Planned trade spend ($4.4M) |
| StructuralTradeRate | Structural trade as % of revenue (17.3%) |
| OperationalWasteAmount | Deductions excl. promo billback (~$1.0M) |
| OperationalWasteRate | Waste as % of revenue (~4.0%) |
| AllInTradeRate | All trade costs as % of revenue (21.3%) |
| RecoveryRate | Disputed dollars recovered (~13.7%) |

### Page 1: Executive Overview

| Measure | What it calculates |
|---------|--------------------|
| WaterfallValue | Step values for margin erosion waterfall |
| WasteAmount | Waste dollars per deduction category |
| RetailerRevenue | Revenue per retailer (donut chart) |

### Page 2: Deduction Deep-Dive

| Measure | What it calculates |
|---------|--------------------|
| DeductionAmount | Sum of deductions in filter context |
| DoubleDipCount / Total | Double-payment events (3 / $19K) |
| UnmappedCodeCount | Deductions missing crosswalk translation (292) |

### Page 3: Promo Performance

| Measure | What it calculates |
|---------|--------------------|
| PromoCost | Actual cost if available, planned as fallback |
| IncrementalRevenue | Lift revenue per promo |
| PromoROI | Return on investment per promo |
| AvgROI | Average ROI by promo type |
| GhostPromoCount / Total | Unmatched billback deductions (137 / $96K) |

### Page 4: Retailer Comparison

| Measure | What it calculates |
|---------|--------------------|
| NetNetMargin | Effective margin after all trade costs |
| RevenueShare / DeductionShare | Concentration risk comparison |
| SavingsAtTarget | Savings at the what-if target rate |
| HighestRiskRetailer | Retailer with lowest net-net margin |

---

## File Inventory

```
powerbi/
├── README.md               ← This file
├── DESIGN.md               ← Page layouts, visual specs, value-add rationale
├── DAX_MEASURES.md          ← All 34 measures with DAX formulas
├── BUILD_GUIDE.md           ← Step-by-step .pbix assembly instructions
├── export_data.py           ← Python script to export CSVs from SQLite
└── data/
    ├── DATA_DICTIONARY.md   ← Column definitions, types, relationships
    ├── dim_retailer.csv     ← 11 retailers with rates and margins
    ├── dim_product.csv      ← 90 SKUs with costs and prices
    ├── dim_promo.csv        ← 188 promotions with pre-computed ROI
    ├── fact_deductions.csv  ← 2,374 deductions with translations
    ├── fact_structural_trade.csv ← 10 retailer-level trade amounts
    ├── fact_scan_data.csv   ← 601K weekly POS records
    └── fact_disputes.csv    ← 1,410 dispute records
```
