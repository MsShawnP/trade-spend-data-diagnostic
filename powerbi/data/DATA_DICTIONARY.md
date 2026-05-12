# Power BI Data Dictionary

Data files exported by `powerbi/export_data.py` from the
Cinderhaven SQLite database. All files are UTF-8 CSV with headers.

Re-export: `python powerbi/export_data.py`

---

## dim_retailer.csv (11 rows)

One row per retailer. Pre-computed trade rates, margins, and
deduction totals for the trailing analysis window.

| Column | Type | Description |
|--------|------|-------------|
| retailer_id | text | Internal slug (e.g., `walmart`, `costco`) |
| retailer_name | text | Display name (e.g., `Walmart`, `Costco`) |
| channel_type | text | Channel: Mass, Club, Natural, Distributor, DTC, Regional |
| revenue | numeric | Trailing-52-week wholesale revenue |
| trade_rate | decimal | Channel-average structural trade rate (0–1) |
| gross_margin | decimal | Channel-average gross margin fraction (0–1) |
| structural_trade_dollars | numeric | revenue × trade_rate |
| op_deductions | numeric | Trailing-365-day operational deductions (excl. promo billback) |
| promo_billback | numeric | Trailing-365-day promo billback deductions |
| all_in_trade | numeric | structural_trade + op_deductions + promo_billback |
| all_in_rate | decimal | all_in_trade / revenue |
| net_net_margin | decimal | gross_margin − all_in_rate |

**Key:** `retailer_name` (join to fact tables via retailer name).

---

## dim_product.csv (90 rows)

One row per SKU. Product attributes and per-channel wholesale prices.

| Column | Type | Description |
|--------|------|-------------|
| sku | text | SKU identifier (e.g., `CPP-VAN-24OZ`) |
| product_name | text | Full product name |
| product_line | text | Product line (Yogurt, Kefir, Cheese, etc.) |
| subcategory | text | Subcategory within product line |
| cogs_per_unit | numeric | Cost of goods sold per unit |
| wholesale_price | numeric | Base wholesale price |
| wholesale_walmart | numeric | Walmart wholesale price |
| wholesale_costco | numeric | Costco wholesale price |
| wholesale_whole_foods | numeric | Whole Foods wholesale price |
| wholesale_regional | numeric | Regional retailers wholesale price |
| wholesale_unfi | numeric | UNFI wholesale price |
| wholesale_dtc | numeric | Direct-to-consumer price |

**Key:** `sku` (join to fact_scan_data, dim_promo).

---

## dim_promo.csv (188 rows)

One row per promotion. Includes pre-computed ROI and lift metrics.

| Column | Type | Description |
|--------|------|-------------|
| promo_id | text | Promotion identifier |
| sku | text | Promoted SKU |
| retailer | text | Retailer name |
| store_scope | text | Which stores (all, subset) |
| start_week | date | Promotion start week (YYYY-MM-DD) |
| end_week | date | Promotion end week (YYYY-MM-DD) |
| duration_weeks | int | Number of weeks |
| discount_depth_pct | decimal | Discount depth as fraction |
| promo_type | text | Type: TPR, BOGO, Display, Feature, etc. |
| planned_cost | numeric | Budgeted promotion cost |
| actual_cost | numeric | Matched deduction cost (null if no match) |
| funding_mechanism | text | Scan, Billback, Off-invoice, etc. |
| asp | numeric | Average selling price for this SKU/retailer |
| baseline_avg_volume | numeric | Average weekly units in pre-period |
| during_avg_volume | numeric | Average weekly units during promo |
| incremental_volume | numeric | (during − baseline) × duration |
| incremental_revenue | numeric | incremental_volume × ASP |
| roi | decimal | incremental_revenue / cost |
| cost_source | text | `actual` (from deductions) or `planned` |
| data_quality | text | `Full` (pre+during POS), `Partial` (during only), `No POS` |

**Key:** `promo_id` (unique). **Joins:** `sku` → dim_product, `retailer` → dim_retailer.

---

## fact_deductions.csv (~2,461 rows)

Deductions from the trailing-365-day window, plus out-of-window rows
for risk flags (double-dip, ghost promo). The `in_trailing_window`
column distinguishes them: general measures filter on it; risk flag
measures (DoubleDip, GhostPromo) do not.

| Column | Type | Description |
|--------|------|-------------|
| deduction_id | text | Unique deduction identifier |
| retailer_id | text | Retailer slug |
| deduction_date | date | Date deduction was taken (YYYY-MM-DD) |
| deduction_type | text | Category: short_ship, pricing_error, promo_billback, etc. |
| amount | numeric | Deduction dollar amount |
| code_as_remitted | text | Raw retailer code from remittance |
| translated_code | text | Crosswalk-translated name (or `Unmapped`) |
| standardized_category | text | Standardized category from crosswalk |
| order_id | text | Associated order |
| shipment_id | text | Associated shipment |
| remittance_id | text | Remittance document ID |
| remittance_description | text | Retailer's description text |
| dispute_deadline | date | Deadline to file dispute |
| is_vague | boolean | 1 if retailer description is vague |
| is_post_audit | boolean | 1 if post-audit deduction |
| is_double_dip | boolean | 1 if identified as double-payment |
| dispute_outcome | text | won_full, won_partial, lost, pending, or null |
| recovered_amount | numeric | Dollars recovered (null if no dispute) |
| dispute_filed_date | date | When dispute was filed |
| dispute_closed_date | date | When dispute was resolved |
| days_outstanding | int | Days from deduction to resolution/today |
| in_trailing_window | boolean | 1 if within trailing-365 window, 0 if out-of-window risk flag row |
| is_ghost_promo | boolean | 1 if promo_billback with no matching planned promotion (all-time detection) |

**Key:** `deduction_id` (unique). **Joins:** `retailer_id` → dim_retailer (via slug).

**Row composition:** ~2,374 trailing-window rows + ~87 out-of-window
rows (3 double-dip from 2024 + ghost promo_billbacks outside window,
deduplicated).

---

## fact_structural_trade.csv (10 rows)

One row per retailer. Structural (planned) trade spend using
channel-average rate methodology.

| Column | Type | Description |
|--------|------|-------------|
| retailer_id | text | Retailer name (matches dim_retailer.retailer_name) |
| revenue | numeric | Trailing-52-week revenue for this retailer |
| trade_rate | decimal | Channel-average trade rate (AVG across all SKUs) |
| structural_trade_dollars | numeric | revenue × trade_rate |

**Key:** `retailer_id`. **Note:** Channel-average methodology — one
rate per retailer computed as `AVG(trade_spend_pct_channel)` from
sku_costs, applied to total channel revenue. Matches locked number
$4,435,052.

---

## fact_scan_data.csv (601,341 rows)

Weekly scan data (POS) by store and SKU for the trailing 52 weeks.
Each row is tagged with its promotional context (pre/during/post/none).

| Column | Type | Description |
|--------|------|-------------|
| sku | text | Product SKU |
| retailer | text | Retailer name |
| store_id | text | Individual store identifier |
| week_ending | date | Week-ending date (YYYY-MM-DD) |
| units_sold | int | Units sold that week |
| dollars_sold | numeric | Dollar sales that week |
| promo_id | text | Matched promotion ID (null if none) |
| promo_period | text | `pre`, `during`, `post`, or `none` |

**Key:** (sku, store_id, week_ending) composite.
**Joins:** `sku` → dim_product, `retailer` → dim_retailer, `promo_id` → dim_promo.

---

## fact_disputes.csv (1,410 rows)

One row per dispute filed. Links to the underlying deduction.

| Column | Type | Description |
|--------|------|-------------|
| dispute_id | text | Unique dispute identifier |
| deduction_id | text | Associated deduction |
| retailer_id | text | Retailer slug |
| deduction_type | text | Category of the underlying deduction |
| deduction_amount | numeric | Original deduction amount |
| filed_date | date | When dispute was filed |
| closed_date | date | When resolved (null if pending) |
| filing_method | text | How filed (portal, email, etc.) |
| evidence_quality | text | Quality of supporting evidence |
| submitted_evidence_count | int | Number of evidence documents |
| was_within_deadline | boolean | 1 if filed before dispute deadline |
| outcome | text | won_full, won_partial, lost, pending |
| recovered_amount | numeric | Dollars recovered |
| labor_hours | numeric | Staff hours spent on dispute |
| days_to_resolve | int | Days from filed to closed (null if open) |

**Key:** `dispute_id` (unique).
**Joins:** `deduction_id` → fact_deductions, `retailer_id` → dim_retailer.

---

## Relationships (Star Schema)

```
dim_retailer ──┬── fact_structural_trade (retailer_id = retailer_name)
               ├── fact_deductions (retailer_id = retailer_id slug)
               ├── fact_scan_data (retailer = retailer_name)
               └── fact_disputes (retailer_id = retailer_id slug)

dim_product ───┬── fact_scan_data (sku)
               └── dim_promo (sku)

dim_promo ─────── fact_scan_data (promo_id)

fact_deductions ── fact_disputes (deduction_id)
```

---

## Validation Targets

| Metric | Expected | Tolerance |
|--------|----------|-----------|
| Total revenue (sum of fact_scan_data.dollars_sold) | $25,593,052 | exact |
| Structural trade (sum of fact_structural_trade.structural_trade_dollars) | $4,435,052 | exact |
| Operational waste (fact_deductions where type ≠ promo_billback, in_trailing_window=1) | $1,010,940 | ±$2,000 |
| Deduction count (fact_deductions where in_trailing_window=1) | 2,374 | exact |
| Double-dip count (fact_deductions where is_double_dip=1) | 3 | exact |
| Double-dip total | $19,306 | exact |
| Ghost promo count (fact_deductions where is_ghost_promo=1) | 137 | exact |
| Ghost promo total | $95,826 | exact |
| Dispute count (fact_disputes rows) | 1,409 | ±2 |
| Total recovered (sum of fact_disputes.recovered_amount) | $98,216 | ±$500 |
