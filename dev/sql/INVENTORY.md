# SQL Query Inventory

Queries embedded in the workbook build scripts (`workbook/` modules).
This inventory catalogs every SQL query, notes which tab it feeds,
and assesses whether it's reusable as a standalone diagnostic.

---

## Query Catalog

| # | Query description | Source file | Line(s) | Feeds tab | Reusable as-is? | Cleanup needed |
|---|---|---|---|---|---|---|
| 1 | Trailing 52 distinct week_ending values | tab_executive_pulse.py | 54–56 | Tab 1 | Yes | None — clean parameterless query |
| 2 | Total revenue (trailing 52w) | tab_executive_pulse.py | 59–62 | Tab 1 | Yes | Replace Python `?` param with SQL variable comment |
| 3 | Revenue by retailer/channel | tab_executive_pulse.py | 66–72 | Tab 1, 4 | Yes | Replace Python `?` param with SQL variable comment |
| 4 | Average trade rate per channel | tab_executive_pulse.py | 83 | Tab 1, 4 | No | Python f-string interpolates column name; need 1 query with all 6 columns or 6 standalone queries |
| 5 | Regional trade rate average | tab_executive_pulse.py | 84 | Tab 1, 4 | Yes | None — single clean query |
| 6 | Deductions by type (trailing 365, excl promo_billback) | tab_executive_pulse.py | 93–100 | Tab 1 | Yes | Replace `?` params with date variable comments |
| 7 | Dispute count and total recovered | tab_executive_pulse.py | 105–108 | Tab 1, 2 | Yes | None — clean aggregate |
| 8 | Category breakdown with avg resolution days | tab_leak_diagnostic.py | 51–67 | Tab 2 | Yes | Replace `?` params; standalone diagnostic of waste by category with dispute timeline |
| 9 | Double-dip events | tab_leak_diagnostic.py | 72–77 | Tab 2 | Yes | None — clean flag-based filter |
| 10 | All promotions (full table read) | tab_promo_efficacy.py | 49–55 | Tab 3 | Yes | None — simple SELECT with ORDER BY |
| 11 | ASP per SKU per retailer | tab_promo_efficacy.py | 59–65 | Tab 3 | Yes | None — useful standalone reference query |
| 12 | Weekly volumes per SKU per retailer | tab_promo_efficacy.py | 70–76 | Tab 3 | Yes | Large result set; add optional WHERE filters for practical use |
| 13 | Matched promo_billback deductions to promotions | tab_promo_efficacy.py | 84–93 | Tab 3 | Yes | Clean JOIN with date-window matching; good standalone diagnostic |
| 14 | Ghost promos (top 20 unmatched promo_billback) | tab_promo_efficacy.py | 97–109 | Tab 3 | Yes | Remove `LIMIT 20` for full diagnostic; parameterize limit |
| 15 | Ghost promo summary (count + total) | tab_promo_efficacy.py | 111–121 | Tab 3 | Yes | None — aggregate version of #14 |
| 16 | Revenue by retailer (duplicate of #3) | tab_retailer_risk.py | 53–58 | Tab 4 | — | Duplicate; consolidate with #3 |
| 17 | Gross margin by channel (COGS vs wholesale) | tab_retailer_risk.py | 70–74 | Tab 4 | No | Python f-string interpolates column name; runs in loop for 6 channels. Combine into single query returning all channels |
| 18 | Operational deductions by retailer | tab_retailer_risk.py | 77–83 | Tab 4 | Yes | Replace `?` params with date variable comments |
| 19 | Promo billback by retailer | tab_retailer_risk.py | 86–93 | Tab 4 | Yes | Replace `?` params with date variable comments |
| 20 | Full deduction ledger (20-column JOIN) | tab_deduction_ledger.py | 57–90 | Tab 5 | Yes | Replace `?` params; the most complex query — 3-way JOIN (deductions, deduction_codes, disputes) |
| 21 | Deduction code crosswalk | tab_code_crosswalk.py | 32–41 | Tab 6 | Yes | None — clean standalone reference query |
| 22 | All distinct weeks (full range, ascending) | tab_promo_efficacy.py | 43–45 | Tab 3 | Yes | None — variant of #1 without LIMIT |

---

## Summary

| Metric | Count |
|--------|-------|
| Total distinct queries | 22 |
| Reusable as-is | 17 |
| Needs cleanup | 3 (#4, #12, #17) |
| Duplicates to consolidate | 2 (#16 = #3, #22 ≈ #1) |

### Cleanup breakdown

| # | What needs to happen |
|---|---|
| 4 | Replace Python f-string column interpolation with a single query that returns AVG for all 6 trade_spend_pct columns in one SELECT |
| 12 | Add optional WHERE clause for SKU/retailer filter; result set is 104 weeks × 90 SKUs × 11 retailers — needs scoping for practical standalone use |
| 17 | Same pattern as #4 — f-string column interpolation for 6 wholesale price columns. Combine into single query returning all channels |

### Gaps — diagnostics answered by Python logic, not SQL

These calculations are done in Python after the SQL results come back.
They need new standalone queries to be useful in the SQL library:

| Gap | Description | Derives from |
|-----|-------------|--------------|
| Structural trade dollar amount | `SUM(channel_revenue × channel_avg_trade_rate)` — currently computed in Python loop pairing query #3 results with query #4/#5 results | #3 + #4 + #5 |
| All-in trade rate | `(structural_trade + operational_waste) / revenue` — Python arithmetic | #2 + #6 + structural trade |
| Net-net effective margin per retailer | `gross_margin - structural_rate - (op_deductions + pb_deductions) / revenue` — Python arithmetic combining queries #17, #4, #18, #19 | Multiple |
| Promo ROI per promotion | Baseline/during/post volume comparison — done via Python list operations on query #12 results, then converted to Excel formulas | #10 + #11 + #12 |
| Recovery rate | `total_recovered / total_disputed_dollars` — Python arithmetic on query #7 | #7 + unstated total disputed amount |
| Addressable improvement | `operational_waste × target_rate - current_recovered` — Python arithmetic | #6 + #7 |

### Suggested extraction plan (for task 2)

**Category groupings for the `dev/sql/` directory:**

- `trade_rate/` — #1, #2, #3, #4 (unified), #5 + new structural trade query
- `deductions/` — #6, #8, #9, #18, #19 + new all-in trade query
- `promo_roi/` — #10, #11, #12, #13, #14, #15 + new ROI calculation query
- `retailer/` — #3 (shared), #17 (unified) + new net-net margin query
- `crosswalk/` — #21
- `reconciliation/` — #7, #20 + new recovery rate query

**Unique standalone queries to extract:** 18 (22 total minus 2 duplicates, minus 2 that merge into unified versions)

**New queries to write:** 6 (filling the Python-logic gaps above)
