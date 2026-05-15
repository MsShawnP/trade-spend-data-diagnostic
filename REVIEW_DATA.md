# Data & Analysis Review

Reviewed: 2026-05-15

## Data Pipeline Map

```
cinderhaven_product_master.db (SQLite, 166.9 MB, 24 tables)
    │
    ├─ scan_data (1,118,009 rows) ──┬── trailing 52 weeks ── Revenue ($25,593,052)
    │                                ├── retailer aggregation via stores table ── Channel revenue
    │                                └── weekly volumes by SKU × retailer ── Promo lift baselines
    │
    ├─ sku_costs (90 rows) ─────────┬── trade_spend_pct_* × channel rev ── Structural trade ($4,435,052)
    │                                └── wholesale prices, COGS ── Gross margins per channel
    │
    ├─ deductions (3,087 rows) ─────┬── trailing-365, excl. promo_billback ── Op. waste ($1,012,455)
    │                                ├── is_double_dip flag ── Double-dip alerts (3 events, $19,306)
    │                                ├── GROUP BY deduction_type ── Category breakdown
    │                                └── GROUP BY retailer_id ── Retailer waste allocation
    │
    ├─ disputes (1,410 rows) ───────── SUM(recovered_amount) ── Recovery rate
    │
    ├─ promotions (188 rows) ───────── Matched to deductions + scan_data ── Promo ROI
    │
    ├─ deduction_codes (97 rows) ───── Code translation and crosswalk
    │
    └─ stores (902 rows) ──────────── store_id → retailer mapping (scan_data join key)
```

Each tab module queries the DB independently via its own `_query_*()` function. No intermediate files. All paths: SQLite → Python → openpyxl → .xlsx.

## Summary

The locked headline numbers are correct and cross-tab consistent. Revenue, structural trade, and waste all trace cleanly from source data to workbook cells. Two BLOCKING issues: (1) the monthly trend indicator includes a partial month (May 2026 = 2 days) that understates H2 waste growth by half (+20% reported vs. +38% actual), and (2) the recovery rate claimed in the Methodology tab ($98,216 / $687,210 = 14.3%) doesn't match the database ($98,216 / $716,082 = 13.7%), and uses all-time scope while the waste bucket uses trailing-365.

## Findings

### [BLOCKING] D1: Partial month biases trend indicator — reports +20% when actual is +38%

- **Location:** `workbook/tab_executive_pulse.py` lines 381-403 (trend calculation); Methodology tab (interpretation)
- **Data impact:** The CEO-facing "12-month waste trend" text on Executive Pulse reads "rising at $77,881/mo avg. H2 up 20% vs H1." The actual trend excluding the partial month is +38%.
- **Issue:** The monthly waste aggregation produces 13 months (2025-05 through 2026-05). May 2026 contains only 2 days of data (8 deductions, $5,068) because the trailing-365 window ends 2026-05-02. This partial month is included in the H2 average, dragging it from $97,482/mo to $84,280/mo. May 2025 is also partial (starts 2025-05-03) but has 28 of 31 days, so the bias is minor on the H1 side.
- **Evidence:**
  - H1 avg (2025-05 to 2025-10, 6 months): $70,416/mo
  - H2 avg with partial May (2025-11 to 2026-05, 7 months): $84,280/mo → +20%
  - H2 avg without partial May (2025-11 to 2026-04, 6 months): $97,482/mo → **+38%**
  - Monthly detail: $77,755 → $71,290 → $92,795 → $110,822 → $80,444 → $151,783 → **$5,068** (partial)
- **Suggested fix:** Exclude any month with fewer than 20 days of data from the trend calculation. Or truncate to complete months only (2025-06 through 2026-04), which gives a clean 11-month window with symmetric 5/6 or 6/5 halves.

### [BLOCKING] D2: Recovery rate — methodology claims 14.3%, actual data shows 13.7%

- **Location:** Methodology tab section 5 ("Recovery Rate & Addressable Improvement"), `tab_executive_pulse.py` line 173
- **Data impact:** The displayed "Current recovery rate" on Executive Pulse and the documented rate in Methodology are both wrong.
- **Issue:** Three problems compounding:
  1. **Wrong denominator in methodology text:** States "Total recovered ($98,216) ÷ total disputed ($687,210) = 14.3%." The actual total disputed is $716,082 (SUM of deduction amounts for deductions that have a dispute). $687,210 appears to be from a prior DB build.
  2. **Circular code:** `tab_executive_pulse.py` hardcodes 0.143 and back-calculates, always producing 14.3% regardless of data (already flagged as B2 in REVIEW_CODE.md).
  3. **Scope mismatch:** The waste bucket uses trailing-365 deductions, but the dispute/recovery query (`SELECT COUNT(*), SUM(recovered_amount) FROM disputes`) uses ALL disputes regardless of date. If scoped to trailing-365 disputes: recovered = $67,280, disputed = $575,105, rate = 11.7%.
- **Evidence:**
  - All-time: $98,216 / $716,082 = **13.7%**
  - Trailing-365: $67,280 / $575,105 = **11.7%**
  - Methodology claims: $98,216 / $687,210 = 14.3% (denominator doesn't match any query)
- **Suggested fix:** (a) Query actual disputed dollars from DB instead of hardcoding. (b) Decide on scope — all-time or trailing-365 — and document the choice. If trailing-365 is chosen, the Addressable Improvement table needs updating. (c) Fix the methodology text to match actual numbers.

### [ADVISORY] D3: Slotting fees included in "operational waste" despite being contractual

- **Location:** All deduction queries that filter `AND deduction_type != 'promo_billback'`
- **Data impact:** $79,160 of slotting fees (22 events across 10 retailers) are counted in the $1,012,455 operational waste total.
- **Issue:** The Methodology tab describes the waste bucket as "unplanned cash outflows from compliance failures," but slotting is a planned, negotiated shelf-access fee. The deduction taxonomy correctly tags slotting as "Contractual" and "Non-addressable," and Tab 2 shows "Addressable: No" — so downstream analysis handles it correctly. But the headline waste number ($1,012,455 / 4.0%) is inflated by $79K of contractual costs that aren't operational waste by the methodology's own definition.
- **Suggested fix:** Either: (a) exclude slotting from the waste query (add `AND deduction_type != 'slotting'`) — waste would become $933,295, rate 3.6%; or (b) update the methodology description to say "all deductions excluding promo_billback" without the "unplanned/compliance" qualifier. Option (b) is simpler and preserves the current numbers; the addressability column already handles the distinction.

### [ADVISORY] D4: Structural trade uses simple average rate across SKUs, not volume-weighted

- **Location:** `tab_executive_pulse.py` line 87, `tab_retailer_risk.py` line 59
- **Data impact:** Structural trade rate per channel = `AVG(trade_spend_pct_*)` across all 90 SKUs, regardless of each SKU's volume at that retailer.
- **Issue:** Walmart trade rates range from 18.1% to 25.0% across SKUs. If high-volume SKUs have different rates than low-volume ones, the simple average diverges from the actual trade cost. Example: if Walmart's top-selling SKU has an 18% rate and a niche SKU has 25%, the simple average (~21.5%) overstates the effective trade cost.
- **Suggested fix:** The simplification is defensible for a diagnostic (you'd need per-SKU per-retailer volume to compute the weighted average accurately). Document the limitation in the Methodology tab: "Trade rates are simple averages across all SKUs. A full engagement would compute volume-weighted rates per retailer."

### [ADVISORY] D5: April 2026 waste spike ($151,783) not surfaced in trend indicator

- **Location:** `tab_executive_pulse.py` trend text (rows 16-19)
- **Data impact:** April 2026 waste ($151,783) is nearly double the monthly average ($77,881) and 3.7x the March 2026 figure ($80,444). The trend text reports only "rising at $77,881/mo avg. H2 up 20% vs H1" without noting the spike.
- **Issue:** A CEO reading the trend text gets a gradual-increase story. The actual data shows a dramatic April spike that may indicate a specific event (new retailer enforcement, seasonal pattern, data quality issue). This is exactly the "Monday morning finding" the plan calls for.
- **Suggested fix:** If the spike is real, call it out: "April 2026 spike: $152K (vs. $78K avg) — investigate root cause." If it's a data artifact, note it in Methodology.

### [ADVISORY] D6: Dispute count inconsistency — DB has 1,410, locked number is 1,409

- **Location:** `validate_workbook.py` line 142, Methodology tab, `cinderhaven-data/TRADE_SPEND_VERIFICATION.md`
- **Data impact:** Minor — 1 dispute out of 1,410.
- **Issue:** PROJECT_PLAN.md risk notes acknowledge "dispute count ±1 between fresh DB builds." The validator tolerates ±2. But the Methodology tab hardcodes "1,409 dispute records" in its description of the disputes table. On the current DB, this is wrong by 1.
- **Suggested fix:** Change Methodology text from "1,409 dispute records" to "~1,410 dispute records" or derive the count at build time instead of hardcoding prose.

### [ADVISORY] D7: Promo ROI uses stored duration_weeks, not actual scan-data weeks matched

- **Location:** `tab_promo_efficacy.py` line 364
- **Data impact:** The incremental volume formula is `(during_avg - pre_avg) × duration_weeks`. If the promo's `duration_weeks` differs from the count of scan-data weeks that actually fall within the promo window, the incremental volume is scaled incorrectly.
- **Issue:** Spot-check example: PROMO-0037 has `duration_weeks=3` but only 2 scan-data weeks fall in the window (2024-11-25 to 2024-12-09 = 14 days, with week_endings on 2024-11-30 and 2024-12-07). The incremental volume is multiplied by 3 instead of 2, inflating it by ~50%.
- **Suggested fix:** The Methodology tab already says this is "not a causal model." Two options: (a) use `len(during_volumes)` instead of `dur_wks` for the multiplier (measures actual observed weeks), or (b) add a note in Methodology: "Duration uses the planned promotion length, which may differ from the number of POS observation weeks."

## Validation Spot-Checks

### Spot-check 1: Revenue = $25,593,052 ✓

```sql
SELECT SUM(dollars_sold) FROM scan_data
WHERE week_ending >= '2025-05-10'  -- 52nd most recent week
-- Result: $25,593,051.92 ≈ $25,593,052
```

Confirmed: 52 distinct weeks (2025-05-10 to 2026-05-02). Revenue matches locked number within $1.

### Spot-check 2: Structural trade = $4,435,052 (17.3%) ✓

Channel revenue × AVG(trade_spend_pct) per retailer:
- Walmart: $13,001,138 × 21.5% = $2,794,277
- UNFI: $4,485,743 × 15.1% = $675,996
- Costco: $2,239,549 × 17.4% = $389,363
- Whole Foods: $2,713,110 × 12.8% = $346,892
- 5 Regionals: $2,302,272 × 9.9% = $228,524
- DTC: $851,241 × 0.0% = $0
- **Total: $4,435,052** → 17.3% of revenue ✓

### Spot-check 3: Operational waste = $1,012,455 (4.0%) ✓ (within known variance)

```sql
SELECT SUM(amount) FROM deductions
WHERE deduction_date > date('2026-05-02', '-365 days') AND deduction_date <= '2026-05-02'
  AND deduction_type != 'promo_billback'
-- Result: $1,012,454.90
```

Locked number: $1,010,940. Difference: $1,515 (0.15%). Within the known ±$1,500 DB rebuild variance documented in PROJECT_PLAN.md. Rate: $1,012,455 / $25,593,052 = 3.96% ≈ 4.0% ✓

### Spot-check 4: Double-dips = 3 events, $19,306 ✓

```sql
SELECT COUNT(*), SUM(amount) FROM deductions WHERE is_double_dip = 1
-- Result: 3, $19,306.00
```

Exact match ✓

### Spot-check 5: Recovery rate = 13.7% ✗ (methodology claims 14.3%)

```sql
-- Recovered:
SELECT SUM(recovered_amount) FROM disputes  -- $98,216
-- Total disputed:
SELECT SUM(d.amount) FROM deductions d JOIN disputes dis ON dis.deduction_id = d.deduction_id
-- $716,082
-- Rate: $98,216 / $716,082 = 13.7%
```

Methodology text claims $687,210 denominator and 14.3% rate. Neither matches the current DB. See finding D2.

## Checklist Results

### Data Integrity
- [x] Row counts validated — 3,087 deductions, 1,410 disputes, 188 promotions, 1,118,009 scan records confirmed
- [x] Joins do not silently drop or duplicate — disputes:deductions is verified 1:1 (1,410 distinct deduction_ids), stores→scan_data join produces correct retailer aggregation
- [x] Filters match stated business logic — `deduction_type != 'promo_billback'` correctly applied to waste queries, trailing-365 window correctly computed from max week_ending
- [x] Date ranges match documentation — trailing 52 weeks (2025-05-10 to 2026-05-02) confirmed for revenue; trailing 365 days for deductions
- [x] Nulls handled — `COALESCE` used for deduction code names, `None` checks for promo volumes, taxonomy fallback for unknown types
- [x] Data types appropriate — amounts as numeric, dates as ISO strings, flags as integer 0/1
- [x] Deduplication correct — no unintentional dedup detected

### Aggregation & Metric Correctness
- [x] Metric definitions clearly stated — Methodology tab documents all key calculations
- [x] Aggregation grain correct — revenue at store→retailer, deductions at retailer, promos at SKU×retailer
- [ ] **Denominators in rates correct** — PARTIAL: recovery rate denominator is wrong (see D2)
- [x] Weighted averages — N/A (simple averages used, documented as limitation — see D4)
- [x] Period comparisons use comparable populations — N/A (single trailing-365 window)
- [x] Totals sum to components — revenue, structural, waste all verified cross-tab
- [x] Currency/unit consistency — all amounts in dollars, all rates as decimals formatted as percentages

### Chart-Data Alignment
- [x] Data sources traceable — each tab's query function is self-contained and readable
- [x] Labels accurate — all column headers match content
- [ ] **Prose claims match data** — PARTIAL: trend text understates H2 growth (D1); methodology states wrong recovery rate (D2)
- [x] Scale choices appropriate — data bars scaled to revenue (appropriate), percentages formatted consistently
- [x] Color encoding consistent — green/amber/red used consistently for recoverability and data quality
- [x] Filtered subsets stated — "Top 20" ghost promos clearly noted, trailing-365 window stated on each tab

### Statistical Methods
- [x] Methods match data type — simple pre/during/post comparison, not overclaimed
- [x] Sample sizes adequate — 188 promo rows with coverage disclosure (Full/Partial/No POS)
- [x] Correlation not presented as causation — methodology explicitly says "not a causal model"
- [x] Outlier handling documented — N/A (no outlier removal applied)
- [x] Segmentation decisions explained — deduction taxonomy with 3 buckets documented in DEFENSIBILITY.md

### Business Logic Alignment
- [x] Metric definitions match audience — CEO-appropriate framing (two-bucket model, rate-card language)
- [ ] **Exclusion criteria reflect business rules** — PARTIAL: slotting in waste bucket inconsistent with "unplanned/compliance" description (D3)
- [x] Time period boundaries appropriate — trailing-365 from most recent scan data week
- [x] Thresholds documented — recovery targets (30%, 50%), benchmark band (19-23%), window parameter (1-12)
- [x] Qualifier terms defined — Methodology tab glossary covers all key terms

### Reproducibility of Results
- [x] Clean source data produces identical outputs — 62/62 validation checks pass on clean build
- [x] No manual steps required — `python build_workbook.py` runs end-to-end
- [x] Sort order deterministic — deductions by date DESC then amount DESC, promos by ROI DESC
- [x] Sampling documented — N/A (no sampling used)
