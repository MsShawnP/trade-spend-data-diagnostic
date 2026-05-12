# Power BI Dashboard — Build Guide

Step-by-step instructions to assemble the Cinderhaven Trade Spend
dashboard. Sections 1–3 cover automated setup (data model, measures
via pbi-tools). Section 4 covers manual visual assembly.

---

## 0. Quick Start (Automated Pipeline)

```bash
# 1. Export data from SQLite to CSV
python powerbi/export_data.py

# 2. Generate the .pbip project (semantic model + report with visuals)
python powerbi/generate_pbip.py

# 3. Open in Power BI Desktop
#    Double-click powerbi/CinderhavenDashboard.pbip
```

Both scripts are idempotent — re-run them in order after any changes.

---

## 0.1 Manual Configuration After Opening .pbip

### Waterfall Chart Sort Order

The `WaterfallSteps` calculated table has a `SortOrder` column, and
the semantic model sets `sortByColumn` on the `Step` column so Power BI
sorts automatically. If the waterfall chart shows steps alphabetically
instead of Revenue → Structural Trade → Operational Waste:

1. Click the waterfall chart to select it
2. Click **...** (more options) on the visual header
3. Select **Sort axis** → **SortOrder**
4. Ensure direction is **Ascending**

### TargetAllInRate Slicer Style (if using interactive layout)

> **Note:** The presentation layout (§ 4) has no slicers. These
> instructions apply only if you add slicers for interactive use.

The `TargetAllInRate` slicer is backed by `GENERATESERIES(0,
0.50, 0.01)` — 51 values. By default Power BI renders this as a list
of checkboxes. Configure as a slider:

1. Click the slicer to select it
2. Open **Format visual** → **Slicer settings**
3. Change **Style** from **Vertical list** to **Between**
4. The slicer now renders as a numeric range slider

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
| fact_deductions | ~2,461 |
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

## 4. Page-by-Page Assembly (Presentation Layout)

The dashboard uses a presentation-first design: each page has one
hero visual, 1–3 KPI cards, and a narrative takeaway text box. No
tables, no slicers, no packed layouts. See `DESIGN.md` for the full
design philosophy.

All measures are available in the Fields pane under `_Measures`.

### 4.1 Page 1: "The Gap"

Rename Page 1 to **"The Gap"**.

#### Takeaway Text Box

Insert → Text box → full width below title strip. Text (verbatim):

> Cinderhaven budgets 17.3% of revenue for trade spend — $4.4
> million in negotiated rate-card allowances. Actual all-in cost is
> 21.3%. The 4-point gap is $1 million in annual operational waste:
> retailer deductions beyond the rate card, largely uncontested.

Font: Segoe UI, 12pt, `#333333`.

#### Hero — Margin Erosion Waterfall

- Type: Waterfall chart, full width, ~60% of remaining page height
- Category: `WaterfallSteps[Step]`, Y-axis: `WaterfallValue`
- Sort by `WaterfallSteps[SortOrder]` ascending
- Increase = `#2E5090`, Decrease = `#C44E52`, Total = `#4C9A6E`
- Data labels: ON, `$#,##0` format

#### KPI Cards (3)

Row below the waterfall, equal width:

| Measure | Title |
|---------|-------|
| AllInTradeRate | All-In Trade Rate |
| OperationalWasteAmount | Operational Waste |
| RecoveryRate | Recovery Rate |

No conditional formatting on this page. The waterfall is the story.

---

### 4.2 Page 2: "Where the Waste Goes"

New page → rename to **"Where the Waste Goes"**.

#### Takeaway Text Box

> Three categories account for two-thirds of operational waste:
> vague deductions ($294K), label fines ($197K), and short-ship
> charges ($184K). Three deductions totaling $19,306 are confirmed
> double-payments — the same promotion billed twice through
> different mechanisms.

#### Hero — Waste Category Bar Chart

- Type: Horizontal bar chart, full width
- Y-axis: `fact_deductions[standardized_category]`
- X-axis: measure `WasteAmount`
- Visual-level filter: `deduction_type` ≠ `"promo_billback"`
- Sort: descending by WasteAmount
- Bar color: `#C44E52` (waste = red)
- Data labels: ON, outside end, `$#,##0`

#### KPI Cards (3)

Row below the bar chart:

| Measure | Title |
|---------|-------|
| OperationalWasteAmount | Total Waste |
| DoubleDipTotal | Double-Dip Total |
| UnmappedCodeCount | Unmapped Codes |

---

### 4.3 Page 3: "Which Promos Work"

New page → rename to **"Which Promos Work"**.

#### Takeaway Text Box

> Of 160 measurable promotions, 104 destroyed value — the cost
> exceeded the incremental revenue. 137 promo-billback deductions
> totaling $95,826 reference promotions that don't appear in the
> planning calendar.

#### Hero — Cost vs. Value Scatter

- Type: Scatter chart, ~65% width
- X-axis: `PromoCost`, Y-axis: `IncrementalRevenue`
- Size: `dim_promo[duration_weeks]`
- Legend: `dim_promo[promo_type]`
- Detail: `dim_promo[promo_id]`
- Analytics: constant line at Y=0 (breakeven)
- Visual filter: exclude blank IncrementalRevenue

#### Supporting — Data Quality Donut

- Type: Donut, right side, small (~250×200px)
- Category: `dim_promo[data_quality]`, Values: `PromoCount`
- Colors: Full `#4C9A6E`, Partial `#F4A940`, No POS `#C44E52`
- Title: "POS Data Coverage"

#### KPI Cards (3)

Stacked vertically right of the scatter, or in a row below:

| Measure | Title |
|---------|-------|
| AvgROI | Avg Promo ROI |
| GhostPromoCount | Ghost Promos |
| GhostPromoTotal | Ghost Promo Exposure |

---

### 4.4 Page 4: "The Retailer Problem"

New page → rename to **"The Retailer Problem"**.

#### Takeaway Text Box

> Net-net margin ranges from 33.8% (Mountain Pantry Co) to 12.5%
> (Walmart). Walmart contributes 51% of revenue but its 21.5%
> structural rate compresses margin to less than half the portfolio
> average.

#### Hero — Net-Net Margin by Retailer

- Type: Clustered column chart, full width
- X-axis: `dim_retailer[retailer_name]`
- Y-axis: `NetNetMarginPct`
- Sort: descending by NetNetMarginPct
- Data labels: ON, `0.0%` format
- Conditional coloring: > 30% green, 15–30% blue, < 15% red
- Analytics: constant line at portfolio average margin, dashed

#### Supporting — Concentration Risk Bars

- Type: Clustered bar (horizontal), bottom-left
- Y-axis: `dim_retailer[retailer_name]`
- X-axis: `RevenueShare`, `DeductionShare`
- Colors: Revenue `#2E5090`, Deductions `#C44E52`
- Visual filter: Top N = 6 by TotalRevenue
- Sort: descending by RevenueShare

#### KPI Card (1)

- Measure: `HighestRiskRetailer`, bottom-right, large format
- Callout value in `#C44E52` (red), 32pt
- Title: "Highest Risk Retailer"

---

## 5. Navigation

The presentation layout uses Power BI's page tab strip for
navigation. No bookmarks, no navigation buttons, no drill-through
configuration needed.

The page tabs show: The Gap | Where the Waste Goes | Which Promos
Work | The Retailer Problem.

This is intentional. The dashboard is a presentation — the audience
moves through it linearly or clicks a tab. Drill-through and
interactive filtering are workbook features.

---

## 6. Final Checklist

- [ ] **Page names**: "The Gap", "Where the Waste Goes",
      "Which Promos Work", "The Retailer Problem"
- [ ] **Page order**: The Gap first (tab order left to right)
- [ ] **Default page**: File → Options → Current File → Report
      Settings → Default page = "The Gap"
- [ ] **Takeaway text**: all 4 pages have the narrative text box
      with the exact wording from § 7.2
- [ ] **Visual count**: Page 1 = 4, Page 2 = 4, Page 3 = 5,
      Page 4 = 3 (16 total — no tables, no slicers)
- [ ] **KPI spot-check**:
  - AllInTradeRate: 21.3%
  - OperationalWasteAmount: ~$1,012,455
  - RecoveryRate: 13.7%
  - DoubleDipTotal: $19,306
  - GhostPromoCount: 137
  - HighestRiskRetailer: displays a retailer name in red
- [ ] **Conditional formatting**: Page 4 margin bars colored by
      threshold (green > 30%, blue 15–30%, red < 15%)
- [ ] **Hide helper tables**: right-click WaterfallSteps, WindowWeeks,
      TargetAllInRate, _Measures → Hide in report view
- [ ] **Save**: Ctrl+S

---

## 7. Visual Polish — Formatting Guide

This section turns the functional dashboard into a professional-looking
deliverable. All instructions are performed in Power BI Desktop's
Format pane. No DAX or data model changes.

**Time estimate:** 30–45 minutes.

---

### 7.1 Color Palette

Use these 6 colors consistently across all pages.

| Role | Hex | Where used |
|------|-----|------------|
| Primary (revenue, positive bars) | `#2E5090` | Waterfall increase bars, column/bar chart bars, table headers, page titles |
| Negative (waste, decrease) | `#C44E52` | Waterfall decrease bars, Double-Dip card accent, Highest Risk Retailer text |
| Neutral (structural) | `#8C8C8C` | Secondary axis labels, gridlines, borders |
| Accent (positive outcome) | `#4C9A6E` | Waterfall total bar, conditional green (ROI > 1, margin > 30%) |
| Background | `#FFFFFF` | Page canvas, card backgrounds |
| Text | `#333333` | All body text, chart data labels, axis labels |

Secondary colors for specific uses:

| Color | Hex | Use |
|-------|-----|-----|
| Partial/warning | `#F4A940` | Donut "Partial" segment, yellow conditional formatting |
| Subtext/labels | `#666666` | KPI category labels, axis tick labels |
| Alt row | `#F5F7FA` | Table alternating row background |
| Light grid | `#F0F0F0` | Chart gridlines (when visible) |
| Table grid | `#E0E0E0` | Table cell borders, slicer borders |
| Total row bg | `#EEEEEE` | Table total/subtotal row background |

---

### 7.2 Page Background, Title Strip & Takeaway Text

Apply to **every page** before formatting individual visuals.

**Page background:**
1. Click empty canvas → Format → Canvas background
2. Color: `#FFFFFF`, Transparency: 0%

**Page title (repeat per page):**
1. Insert → Text box → position at top: x=10, y=5, width=1260, height=40
2. Text: page name (see table below)
3. Font: Segoe UI Semibold, 16pt, color `#2E5090`
4. Alignment: left
5. No background fill

| Page | Title text |
|------|-----------|
| 1 | The Gap |
| 2 | Where the Waste Goes |
| 3 | Which Promos Work |
| 4 | The Retailer Problem |

**Divider line:**
1. Insert → Shapes → Line
2. Position: x=10, y=42, width=1260, height=0
3. Line color: `#E0E0E0`, weight: 1px
4. No shadow

**Takeaway text box (repeat per page):**
1. Insert → Text box → position: x=10, y=48, width=1260, height=55
2. Font: Segoe UI, 12pt, color `#333333`
3. Line spacing: 1.3
4. No background fill, no border
5. Text: the exact takeaway from the table below

| Page | Takeaway text |
|------|--------------|
| 1 | Cinderhaven budgets 17.3% of revenue for trade spend — $4.4 million in negotiated rate-card allowances. Actual all-in cost is 21.3%. The 4-point gap is $1 million in annual operational waste: retailer deductions beyond the rate card, largely uncontested. |
| 2 | Three categories account for two-thirds of operational waste: vague deductions ($294K), label fines ($197K), and short-ship charges ($184K). Three deductions totaling $19,306 are confirmed double-payments — the same promotion billed twice through different mechanisms. |
| 3 | Of 160 measurable promotions, 104 destroyed value — the cost exceeded the incremental revenue. 137 promo-billback deductions totaling $95,826 reference promotions that don't appear in the planning calendar. |
| 4 | Net-net margin ranges from 33.8% (Mountain Pantry Co) to 12.5% (Walmart). Walmart contributes 51% of revenue but its 21.5% structural rate compresses margin to less than half the portfolio average. |

**Layout zones after title + takeaway:**
- y=0 to y=42: Title strip
- y=48 to y=105: Takeaway text
- y=110 and below: Visuals (hero chart, KPI cards)

---

### 7.3 KPI Card Formatting (Global)

The presentation layout uses 2–3 large KPI cards per page, not
5 small ones. Cards are wider and taller than the prior layout.

**Format visual → Callout value:**
- Font: Segoe UI Semibold
- Size: 32pt (larger than prior — cards are wider now)
- Color: `#333333`

**Format visual → Category label:**
- Font: Segoe UI
- Size: 11pt
- Color: `#666666`

**Format visual → Card background:**
- Toggle OFF (no fill)

**Format visual → Border:**
- Toggle OFF

**Format visual → Shadow:**
- Toggle OFF

**Format visual → Visual container → Title:**
- Show: ON
- Font: Segoe UI, 11pt, `#666666`
- Left-aligned

**Card inventory** (presentation layout — 10 cards total):

| Page | Card | Title | Measure | Width |
|------|------|-------|---------|-------|
| 1 | 1 | All-In Trade Rate | AllInTradeRate | ~400px |
| 1 | 2 | Operational Waste | OperationalWasteAmount | ~400px |
| 1 | 3 | Recovery Rate | RecoveryRate | ~400px |
| 2 | 1 | Total Waste | OperationalWasteAmount | ~400px |
| 2 | 2 | Double-Dip Total | DoubleDipTotal | ~400px |
| 2 | 3 | Unmapped Codes | UnmappedCodeCount | ~400px |
| 3 | 1 | Avg Promo ROI | AvgROI | ~250px |
| 3 | 2 | Ghost Promos | GhostPromoCount | ~250px |
| 3 | 3 | Ghost Promo Exposure | GhostPromoTotal | ~250px |
| 4 | 1 | Highest Risk Retailer | HighestRiskRetailer | ~400px |

All titles fit at 400px width — no truncation expected. Verify after
placing. To rename: Format visual → Visual container → Title → Title
text.

---

### 7.4 Chart Formatting (Global)

Apply to **every bar chart, column chart, waterfall, scatter, and
donut**.

**Gridlines:**
1. Format visual → X axis / Y axis → Gridlines
2. Toggle OFF entirely (presentation style — data labels carry the
   numbers)
3. If gridlines are needed for the scatter plot, use `#F0F0F0`

**Data labels:**
1. Format visual → Data labels → ON
2. Font: Segoe UI, 9pt (10pt for hero charts)
3. Color: `#333333`
4. Position: Outside end (bar/column), or auto (scatter)

**Axis labels:**
1. Font: Segoe UI, 9pt
2. Color: `#666666`

**Chart title:**
1. Font: Segoe UI Semibold, 12pt
2. Color: `#333333`
3. Alignment: left

**Legend:**
- OFF for single-series charts (waterfall, single-color bars)
- ON for scatter (by promo_type) and donut (by data_quality)
- When visible: Segoe UI, 9pt, position: Top

**General:**
- Border: OFF
- Shadow: OFF
- Background: none (transparent)

---

### 7.5 Page 1 — "The Gap"

Visual count: 1 hero chart + 3 KPI cards + 1 takeaway text box.

**Takeaway text box:** see § 7.2 (y=48, full width).

**Hero — Waterfall chart:**
- Position: centered, x=40, y=110, w=1200, h=380
- This chart occupies most of the page. It is the story.
- Format visual → Columns:
  - Increase: `#2E5090` (Revenue bar)
  - Decrease: `#C44E52` (Structural Trade, Operational Waste)
  - Total: `#4C9A6E` (net result auto-bar)
- Sort: by SortOrder ascending (should work automatically via
  prefixed names). If not: **... → Sort axis → SortOrder → Ascending**
- Category axis labels: the "01 ", "02 ", "03 " prefixes appear on
  the axis. Leave them — they're unobtrusive and guarantee correct
  order. (Power BI does not offer per-label renaming on waterfall.)
- Data labels: ON, Segoe UI 10pt, `$#,##0` format, above/below bars
- Y-axis title: OFF
- X-axis title: OFF
- Legend: OFF (single series)
- Gridlines: OFF

**KPI cards (3):**
- Position: row below waterfall, y=500
- Layout: 3 cards, equal width (~400px each), 10px gaps
- Card 1 (x=30): AllInTradeRate — title "All-In Trade Rate"
- Card 2 (x=440): OperationalWasteAmount — title "Operational Waste"
- Card 3 (x=850): RecoveryRate — title "Recovery Rate"
- Apply § 7.3 formatting

**What is NOT on this page:** No revenue-by-retailer chart, no
retailer summary table, no 5-card row. One chart, three numbers,
one sentence.

---

### 7.6 Page 2 — "Where the Waste Goes"

Visual count: 1 hero chart + 3 KPI cards + 1 takeaway text box.

**Takeaway text box:** see § 7.2.

**Hero — Waste Category Bar Chart (horizontal):**
- Position: x=40, y=110, w=1200, h=360
- Type: barChart (horizontal bars)
- Y-axis: `fact_deductions[standardized_category]`
- X-axis: measure `WasteAmount`
- Sort: descending by WasteAmount
- Bar color: `#C44E52` (all waste = red)
- Data labels: ON, outside end, Segoe UI 10pt, `$#,##0` format
- Y-axis labels: Segoe UI 10pt, `#333333` (category names should be
  large enough to read — this is the insight)
- X-axis: OFF or minimal (data labels carry the numbers)
- Gridlines: OFF
- Legend: OFF
- Visual-level filter: add `fact_deductions[deduction_type]` ≠
  `"promo_billback"` to exclude promo billbacks from the operational
  waste view

**KPI cards (3):**
- Position: row below bar chart, y=480
- Layout: 3 cards, ~400px each
- Card 1 (x=30): OperationalWasteAmount — title "Total Waste"
- Card 2 (x=440): DoubleDipTotal — title "Double-Dip Total"
  - Verify displays "$19,306" with $ symbol
  - If amount shows as 0, check that fact_deductions includes the
    out-of-window double-dip rows (in_trailing_window = 0)
- Card 3 (x=850): UnmappedCodeCount — title "Unmapped Codes"
- Apply § 7.3 formatting

---

### 7.7 Page 3 — "Which Promos Work"

Visual count: 1 hero scatter + 1 donut + 3 KPI cards + 1 takeaway
text box (5 visuals total — the most on any page).

**Takeaway text box:** see § 7.2.

**Hero — Promo Cost vs. Revenue Scatter:**
- Position: x=20, y=110, w=820, h=380
- Type: Scatter chart
- X-axis: measure `PromoCost`
- Y-axis: measure `IncrementalRevenue`
- Detail: `dim_promo[promo_id]` (one dot per promo)
- Legend: `dim_promo[promo_type]` (colors by promo type)
- Size: `dim_promo[duration_weeks]`
- Dot colors by promo_type:
  - TPR: `#2E5090`
  - Feature: `#8C8C8C`
  - Display: `#4C9A6E`
  - BOGO: `#F4A940`
- Analytics: add a constant line at Y=0 (breakeven reference),
  dashed, `#8C8C8C`
- Visual filter: exclude rows where IncrementalRevenue is blank
- Gridlines: `#F0F0F0` (light — scatter needs reference grid)
- Axis labels: Segoe UI 9pt, `#666666`
- Legend: ON, position Top, Segoe UI 9pt
- Data labels: OFF (too many dots — would overlap)

**Supporting — Data Quality Donut:**
- Position: x=870, y=110, w=380, h=200
- Category: `dim_promo[data_quality]`
- Values: measure `PromoCount`
- Slice colors:
  - Full: `#4C9A6E` (green)
  - Partial: `#F4A940` (amber)
  - No POS: `#C44E52` (red)
- Labels: category name + percentage, Segoe UI 9pt
- Inner radius: 50%
- Title: "POS Data Coverage"
- Legend: OFF (labels show category names)

**KPI cards (3):**
- Position: stacked vertically to the right of the scatter, or in a
  row below it
- Option A — stacked right (x=870, y=330 / y=400 / y=470, w=380):
  - Card 1: AvgROI — title "Avg Promo ROI"
  - Card 2: GhostPromoCount — title "Ghost Promos"
  - Card 3: GhostPromoTotal — title "Ghost Promo Exposure"
- Option B — horizontal row (y=510, 3 cards at ~400px each):
  use if vertical stacking feels cramped
- Apply § 7.3 formatting
- For the stacked layout, reduce callout font to 28pt to fit the
  narrower card width

---

### 7.8 Page 4 — "The Retailer Problem"

Visual count: 1 hero column chart + 1 supporting bar chart + 1 KPI
card + 1 takeaway text box (3 visuals + text).

**Takeaway text box:** see § 7.2.

**Hero — Net-Net Margin by Retailer:**
- Position: x=20, y=110, w=1240, h=320
- Type: clusteredColumnChart
- X-axis: `dim_retailer[retailer_name]`
- Y-axis: measure `NetNetMarginPct`
- Sort: descending by NetNetMarginPct
- Data labels: ON, outside end, format `0.0%`, Segoe UI 10pt
- Gridlines: OFF
- Legend: OFF

**Conditional bar coloring:**
1. Click the chart → Format visual → Columns → Color
2. Click **fx** (conditional formatting)
3. Style: Rules, Based on: field `NetNetMarginPct`
   - value > 0.30 → `#4C9A6E` (green — healthy margin)
   - value >= 0.15 AND <= 0.30 → `#2E5090` (blue — acceptable)
   - value < 0.15 → `#C44E52` (red — margin risk)

**Analytics: portfolio average line:**
1. Format visual → Analytics → Constant line → Add
2. Value: type the portfolio average net-net margin (calculate from
   the data — approximately 24%)
3. Style: dashed, `#8C8C8C`, 1px
4. Label: "Portfolio avg", position Above

**Supporting — Concentration Risk Bars:**
- Position: bottom-left, x=20, y=450, w=780, h=250
- Type: clusteredBarChart (horizontal)
- Y-axis: `dim_retailer[retailer_name]`
- X-axis: measures `RevenueShare`, `DeductionShare`
- Colors: Revenue `#2E5090`, Deductions `#C44E52`
- Sort: descending by `RevenueShare`
- Data labels: ON, format `0.0%`, Segoe UI 9pt
- Legend: ON, position Top, Segoe UI 9pt
- Visual filter: Top N = 6 by TotalRevenue (show only the largest
  retailers — reduces noise)
- Gridlines: OFF

**KPI card (1):**
- Position: bottom-right, x=830, y=450, w=430, h=250
- Measure: HighestRiskRetailer
- Title: "Highest Risk Retailer"
- Callout value font: Segoe UI Semibold, 32pt, color `#C44E52` (red)
- Category label: Segoe UI, 11pt, `#666666`
- No background fill, no border
- This card is intentionally large — the red retailer name should
  be visually prominent

---

### 7.9 Final Visual Polish Checklist

After applying all formatting, run through this verification:

- [ ] **Title strips**: all 4 pages have title text box + divider line
- [ ] **Takeaway text**: all 4 pages have the narrative text box with
      the correct wording (§ 7.2)
- [ ] **White space**: no page feels crowded — each has <=3 visuals
      plus KPI cards
- [ ] **No truncation**: every KPI card label and value displays fully
      at the card width
- [ ] **Waterfall colors**: increase=`#2E5090`, decrease=`#C44E52`,
      total=`#4C9A6E`
- [ ] **Waste bars**: all red (`#C44E52`) on Page 2
- [ ] **Scatter legend**: shows 4 promo types in distinct colors
- [ ] **Donut colors**: Full=green, Partial=amber, No POS=red
- [ ] **Margin bars**: green > 30%, blue 15–30%, red < 15%
- [ ] **Concentration risk**: Revenue blue, Deductions red, only
      top 6 retailers shown
- [ ] **Highest Risk Retailer**: red text (`#C44E52`), large font
- [ ] **Data labels**: ON for all bar/column/waterfall charts
- [ ] **Gridlines**: OFF everywhere except scatter (light `#F0F0F0`)
- [ ] **No default blue**: none of the Power BI default #4472C4 theme
      color remains
- [ ] **Shadows off**: no box shadows on any visual
- [ ] **Borders off**: no borders on any visual
- [ ] **No slicers**: presentation layout has no slicers (what-if
      interaction lives in the workbook)
- [ ] **No tables**: no table or matrix visuals on any page (data
      detail lives in the workbook)
- [ ] **Page background**: white on all 4 pages
- [ ] **Font consistency**: all text is Segoe UI family, no Arial
      or Calibri
- [ ] **Visual count**: Page 1 = 4, Page 2 = 4, Page 3 = 5,
      Page 4 = 3 (16 total)
- [ ] **Save**: Ctrl+S
