# Remediation Tracker

Created: 2026-05-15
Last updated: 2026-05-15 (blocking items resolved)

## Summary

- Total findings: 22 (some consolidated from overlapping review findings)
- Blocking: 4 (4 resolved, 0 remaining)
- Advisory: 18 (0 resolved, 18 remaining)

## Blocking Items

### 1. Recovery rate is wrong everywhere — circular code, stale text, cross-document contradiction

- **Source:** Code Review (B2), Data Review (D2), Prose Review (P1)
- **Status:** ☑ RESOLVED
- **Issue:** Three compounding problems: (a) `tab_executive_pulse.py` line 173 hardcodes 0.143 and back-calculates, always producing 14.3% regardless of data; (b) Methodology tab claims "$687,210" denominator — actual is $716,082; (c) walkthrough says 13.7%/1,410 but memo, defensibility, and methodology say 14.3%/1,409. Actual rate per current DB: 13.7% (all-time) or 11.7% (trailing-365). Fix requires: query actual disputed dollars, pick a scope (all-time or trailing-365), update code + all four prose documents.
- **Fix applied:** Added `total_disputed` query to `_query_metrics()`. Replaced circular calculation with `total_recovered / total_disputed`. Chose all-time scope (13.7%). Updated methodology tab ($716,082, 13.7%, scope note). Updated EXECUTIVE_MEMO.md (1,410 disputes, 13.7%). Updated DEFENSIBILITY.md (13.7%). Workbook now shows 13.7% computed from data. 62/62 validation passes.

### 2. Hardcoded absolute path breaks reproducibility

- **Source:** Code Review (B1)
- **Status:** ☑ RESOLVED
- **Issue:** `scripts/build_db.py` line 15: `ACTIVE_DB = Path(r"C:\Users\mssha\...")` — fails on any other machine. Replace with env var fallback or remove.
- **Fix applied:** Replaced hardcoded path with `os.environ.get("CINDERHAVEN_DB_PATH")`. `ACTIVE_DB` is now `None` if env var is unset. Updated `find_database()` and `build()` to guard against `None`. Error messages now tell the user what to do.

### 3. Partial month biases trend indicator — reports +20% when actual is +38%

- **Source:** Data Review (D1)
- **Status:** ☑ RESOLVED
- **Issue:** May 2026 has 2 days of data (8 deductions, $5,068) but is included as a full month in the H2 average, halving the reported trend severity. Exclude months with <20 days of data, or truncate to complete months.
- **Fix applied:** Monthly waste query now includes `COUNT(DISTINCT deduction_date) as active_days`. Months with <20 active days are excluded from the trend calculation. Trend text now reads "rising at $83,949/mo avg. H2 up 38% vs H1." — accurately reflecting the waste acceleration.

### 4. Vague deduction framing contradicts itself across deliverables

- **Source:** Prose Review (P2)
- **Status:** ☑ RESOLVED
- **Issue:** Walkthrough: "burden shifts to manufacturer." Defensibility: "retailer bears the burden." Memo: "no contractual standing." Three different legal positions on the $294K #1 priority category. Pick one framing and apply consistently.
- **Fix applied:** Aligned all three documents to a neutral framing: "Deductions without a specific, documented basis are disputable — the absence of clear justification is itself the dispute grounds." Avoids claiming either party bears a legal burden (which depends on contract terms). Updated walkthrough (reframed as "highest priority for investigation"), memo (removed "no contractual standing"), and defensibility log (removed "retailer bears the burden").

## Advisory Items

### 1. Unused dependencies + phantom references (rapidfuzz, pandas)

- **Source:** Code Review (A1), Prose Review (P3, P4)
- **Status:** ☐ OPEN
- **Issue:** requirements.txt lists pandas and rapidfuzz; neither is imported. README lists both in "Stack." Walkthrough claims "Fuzzy matching (via rapidfuzz)" — no fuzzy matching in shipped code. Remove from requirements.txt, README, and walkthrough (or clarify upstream usage).
- **Fix applied:**

### 2. Dependencies not pinned in requirements.txt

- **Source:** Code Review (A2)
- **Status:** ☐ OPEN
- **Issue:** openpyxl not version-pinned despite known rendering issues with charts. Pin `openpyxl>=3.1.5,<4.0` at minimum.
- **Fix applied:**

### 3. TABLE_STYLE copy-pasted in 6 files

- **Source:** Code Review (A3)
- **Status:** ☐ OPEN
- **Issue:** Identical `TableStyleInfo(name="TableStyleMedium2", ...)` in 6 tab modules. Move to `workbook/styles.py`.
- **Fix applied:**

### 4. bisect imported inside function body

- **Source:** Code Review (A4)
- **Status:** ☐ OPEN
- **Issue:** `import bisect` at line 120 of `tab_promo_efficacy.py` instead of module top level. Minor PEP 8 violation.
- **Fix applied:**

### 5. Fragile date-distance heuristic in promo week matching

- **Source:** Code Review (A5)
- **Status:** ☐ OPEN
- **Issue:** `_find_nearest_week_idx` compares single character ordinals instead of date distances. Works for weekly data but fragile. Add comment or replace with date parsing.
- **Fix applied:**

### 6. Window range mismatch — docs say 1-8, code allows 1-12

- **Source:** Code Review (A6), Prose Review (P7)
- **Status:** ☐ OPEN
- **Issue:** Methodology tab and walkthrough say "range 1-8." Tab 3 validation allows 1-12 and helper columns support 12. Update docs to say 1-12.
- **Fix applied:**

### 7. SQLite connections don't use context managers

- **Source:** Code Review (A7)
- **Status:** ☐ OPEN
- **Issue:** All 7 query functions use `conn = sqlite3.connect()` + explicit `close()` instead of `with`. Low risk (read-only SQLite), but not Pythonic.
- **Fix applied:**

### 8. Division-by-zero unguarded in promo coverage calculation

- **Source:** Code Review (A8)
- **Status:** ☐ OPEN
- **Issue:** `tab_promo_efficacy.py` line 265: `covered_cost/total_cost*100` could divide by zero if all promos have None/0 planned_cost. Guard with `if total_cost`.
- **Fix applied:**

### 9. Slotting in waste bucket inconsistent with methodology description

- **Source:** Data Review (D3)
- **Status:** ☐ OPEN
- **Issue:** $79K slotting is contractual but included in the "operational waste" bucket described as "unplanned cash outflows from compliance failures." Either exclude slotting from waste query or update the methodology description to drop the "unplanned/compliance" qualifier.
- **Fix applied:**

### 10. Structural trade uses simple avg rate, not volume-weighted

- **Source:** Data Review (D4)
- **Status:** ☐ OPEN
- **Issue:** `AVG(trade_spend_pct_*)` across all 90 SKUs regardless of volume. Document the limitation in Methodology tab.
- **Fix applied:**

### 11. April 2026 waste spike ($152K) not surfaced in any narrative

- **Source:** Data Review (D5)
- **Status:** ☐ OPEN
- **Issue:** April 2026 is nearly 2x the monthly average — a potential "Monday morning finding" that's not mentioned in the trend text, memo, or walkthrough. Call it out or note it.
- **Fix applied:**

### 12. Stale numbers hardcoded in Methodology tab

- **Source:** Data Review (D6), Prose Review (P8)
- **Status:** ☐ OPEN
- **Issue:** Methodology tab says "1,409 dispute records" (DB: 1,410) and "$211,513" promo billback (DB: $213,017). Derive at build time or use approximate language.
- **Fix applied:**

### 13. Promo ROI uses stored duration_weeks, not actual scan-data weeks

- **Source:** Data Review (D7)
- **Status:** ☐ OPEN
- **Issue:** Incremental volume multiplied by `duration_weeks` from promotions table, not count of actual scan-data weeks in window. Can inflate ROI by ~50% when weeks don't align. Document the choice or use actual week count.
- **Fix applied:**

### 14. Walkthrough says "trend chart" — it's a text indicator

- **Source:** Prose Review (P5)
- **Status:** ☐ OPEN
- **Issue:** Walkthrough section 4: "A 12-month waste trend chart shows..." — no chart exists (abandoned per FAILURES.md). Change "chart" to "trend indicator."
- **Fix applied:**

### 15. Walkthrough POS record count is misleading

- **Source:** Prose Review (P6)
- **Status:** ☐ OPEN
- **Issue:** Claims "601,341 weekly point-of-sale records" — this is the trailing-52w subset. Full table is 1,118,009 rows (104 weeks). Promo analysis uses the full table. Clarify scope.
- **Fix applied:**

### 16. Instructional callout buried at bottom of Tab 1

- **Source:** Prose Review (P9)
- **Status:** ☐ OPEN
- **Issue:** Color-coding orientation (green/blue/gray/yellow) appears below navigation links. CEO encounters yellow cells before seeing the explanation. Consider moving up or adding cell comments.
- **Fix applied:**

### 17. sys.path.insert in entry point

- **Source:** Code Review (A9)
- **Status:** ☐ OPEN
- **Issue:** `build_workbook.py` modifies sys.path at import time. Works for script execution but fragile if ever packaged. Low priority.
- **Fix applied:**

### 18. f-string SQL column interpolation

- **Source:** Code Review (A10)
- **Status:** ☐ OPEN
- **Issue:** SQL queries use f-string interpolation for column names from trusted constant dicts. Not a vulnerability but could be dangerous if pattern is extended. Add comment or allowlist validation.
- **Fix applied:**

## Audit Readiness

All blocking items resolved: **YES**
Ready for final audit: **YES** (advisory items remain but are non-blocking)
