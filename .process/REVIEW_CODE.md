# Code Review

Reviewed: 2026-05-15

Files reviewed:
- `build_workbook.py` — entry point
- `validate_workbook.py` — acceptance test suite (62 checks)
- `workbook/__init__.py` — package init
- `workbook/generator.py` — workbook orchestrator
- `workbook/styles.py` — shared styles
- `workbook/channel_mapping.py` — retailer-to-channel mapping
- `workbook/deduction_taxonomy.py` — deduction taxonomy + addressability
- `workbook/tab_executive_pulse.py` — Tab 1: Executive Pulse
- `workbook/tab_leak_diagnostic.py` — Tab 2: Leak Diagnostic
- `workbook/tab_promo_efficacy.py` — Tab 3: Promo Efficacy
- `workbook/tab_retailer_risk.py` — Tab 4: Retailer Risk
- `workbook/tab_deduction_ledger.py` — Tab 5: Deduction Ledger
- `workbook/tab_code_crosswalk.py` — Tab 6: Deduction Code Crosswalk
- `workbook/tab_methodology.py` — Tab 7: Methodology & Logic
- `scripts/build_db.py` — database acquisition
- `requirements.txt` — dependencies

Not reviewed (demoted to `/dev/`, not shipped per PROJECT_PLAN.md):
- `dev/powerbi/export_data.py`, `dev/powerbi/generate_pbip.py`, `dev/powerbi/generate_pbix_model.py`
- `scripts/explore_db.py` (utility, not part of build pipeline)

## Summary

The codebase is well-structured and functionally correct — 62/62 validation checks pass and the workbook renders clean in Excel. The architecture (one module per tab, shared styles, centralized mappings) is sound. Two BLOCKING issues need attention: a hardcoded absolute path that breaks reproducibility on any machine other than the operator's, and a circular recovery rate calculation that hardcodes 14.3% instead of computing it from data. Several ADVISORY items around dependency hygiene, code deduplication, and edge cases.

## Findings

### [BLOCKING] B1: Hardcoded absolute path in `scripts/build_db.py`

- **File:** `scripts/build_db.py`
- **Line(s):** 15
- **Issue:** `ACTIVE_DB = Path(r"C:\Users\mssha\projects\active\cinderhaven-data\data\cinderhaven_product_master.db")` — this is an operator-specific Windows path baked into the fallback logic.
- **Impact:** On any machine other than the operator's, if the submodule DB doesn't exist and the submodule build fails, the script crashes with `FileNotFoundError` instead of producing a useful error. A cold clone by a portfolio viewer follows this path: submodule clone → submodule build fails (deduction scripts not pushed per FAILURES.md) → looks for `C:\Users\mssha\...` → crashes. This directly violates the reproducibility requirement.
- **Suggested fix:** Replace with an environment variable fallback: `ACTIVE_DB = Path(os.environ.get("CINDERHAVEN_DB_PATH", ""))` and document in README. Or remove the fallback entirely and require the submodule DB to exist (since `build_db.py` already copies it successfully when the active repo is present — the copy is the DB that ships).

### [BLOCKING] B2: Recovery rate calculation is circular — always returns 14.3%

- **File:** `workbook/tab_executive_pulse.py`
- **Line(s):** 173
- **Issue:** `recovery_rate = metrics["total_recovered"] / (metrics["total_recovered"] / 0.143) if metrics["total_recovered"] else 0` — this back-calculates the denominator from the hardcoded constant 0.143, then divides by it, producing 0.143 every time regardless of actual data.
- **Impact:** The "Current recovery rate" line in the Addressable Improvement table on Executive Pulse always displays 14.3%. If the database is rebuilt (known to have ±$1,500 variance per PROJECT_PLAN.md risk notes) or dispute outcomes change, the displayed rate doesn't update. A CEO is reading a hardcoded number presented as a computed metric.
- **Suggested fix:** Query total disputed dollars from the database:
  ```python
  total_disputed = conn.execute("""
      SELECT SUM(d.amount) FROM deductions d
      JOIN disputes dis ON dis.deduction_id = d.deduction_id
  """).fetchone()[0]
  ```
  Then compute: `recovery_rate = total_recovered / total_disputed if total_disputed else 0`. Add `total_disputed` to the metrics dict.

## Advisory Findings

### [ADVISORY] A1: Unused dependencies in `requirements.txt`

- **File:** `requirements.txt`
- **Lines:** 2-3
- **Issue:** `pandas` and `rapidfuzz` are listed but never imported in any shipped code file. `pandas` was likely from an earlier iteration. `rapidfuzz` was mentioned in PROJECT_PLAN.md for "fuzzy code matching" but doesn't appear in any import.
- **Impact:** Cold clones install unnecessary packages (pandas is ~50 MB). Not functionally broken, but misleading about actual dependencies.
- **Suggested fix:** Remove `pandas` and `rapidfuzz` from requirements.txt, or add a comment explaining if they're needed for `dev/` scripts.

### [ADVISORY] A2: Dependencies not pinned in `requirements.txt`

- **File:** `requirements.txt`
- **Lines:** 1-3
- **Issue:** `openpyxl`, `pandas`, `rapidfuzz` are listed without version constraints. Given the known openpyxl chart rendering issue (documented in FAILURES.md with openpyxl 3.1.5), different versions could produce different formatting behavior.
- **Impact:** Future installs may get a different openpyxl version that changes formatting, table, or conditional formatting output.
- **Suggested fix:** Pin at minimum: `openpyxl>=3.1.5,<4.0`. Remove unused deps rather than pinning them.

### [ADVISORY] A3: `TABLE_STYLE` defined identically in 4 files

- **Files:** `tab_executive_pulse.py` (L57-60), `tab_leak_diagnostic.py` (L39-42), `tab_promo_efficacy.py` (L30-33), `tab_retailer_risk.py` (L33-36)
- **Issue:** The same `TableStyleInfo(name="TableStyleMedium2", ...)` is copy-pasted in 4 tab modules. `tab_deduction_ledger.py` and `tab_code_crosswalk.py` also define it inline.
- **Impact:** If the style needs to change (e.g., different stripe pattern), it must be changed in 6 places.
- **Suggested fix:** Move to `workbook/styles.py` as `TABLE_STYLE` and import it in each tab module, matching the pattern already used for fonts and alignments.

### [ADVISORY] A4: `bisect` imported inside function body

- **File:** `workbook/tab_promo_efficacy.py`
- **Line:** 120
- **Issue:** `import bisect` is inside the `_query_promo_data` function rather than at module top level.
- **Impact:** Works correctly but violates PEP 8 convention (imports at top of file). Makes dependencies less visible when scanning the module.
- **Suggested fix:** Move to the top-level imports.

### [ADVISORY] A5: Fragile date-distance heuristic in promo matching

- **File:** `workbook/tab_promo_efficacy.py`
- **Lines:** 128-130
- **Issue:** `_find_nearest_week_idx` compares single character ordinals (`ord(all_weeks[idx][8])`) to pick the nearest week, rather than computing actual date distances. For ISO dates, position 8 is the first digit of the day. This is a rough heuristic that breaks at month/year boundaries (e.g., "2025-12-31" vs "2026-01-07").
- **Impact:** With weekly scan data (7-day intervals), bisect already narrows to two adjacent candidates, so the heuristic is correct in practice for this dataset. But it would silently produce wrong matches if applied to daily or irregular data.
- **Suggested fix:** Replace with proper date parsing: `abs((datetime.strptime(all_weeks[idx], '%Y-%m-%d') - datetime.strptime(target_date, '%Y-%m-%d')).days)`. Or accept the limitation with a comment.

### [ADVISORY] A6: Methodology tab says window range is "1-8", code allows 1-12

- **File:** `workbook/tab_methodology.py` (line ~124: "default 4, range 1-8") vs `workbook/tab_promo_efficacy.py` (line 248: `formula2="12"`, line 28: `_MAX_WINDOW = 12`)
- **Issue:** The methodology documentation and the actual data validation / helper column range disagree on the maximum window size.
- **Impact:** A user entering 9-12 in the window cell gets valid results (the hidden helper columns support up to 12 weeks), but the methodology says the range is 1-8.
- **Suggested fix:** Update methodology to say "range 1-12" or tighten the data validation to match documentation.

### [ADVISORY] A7: SQLite connections don't use context managers

- **Files:** All tab modules (`tab_executive_pulse.py`, `tab_leak_diagnostic.py`, `tab_promo_efficacy.py`, `tab_retailer_risk.py`, `tab_deduction_ledger.py`, `tab_code_crosswalk.py`), `validate_workbook.py`
- **Issue:** All database connections use `conn = sqlite3.connect(...)` followed by explicit `conn.close()`, rather than `with sqlite3.connect(...) as conn:`.
- **Impact:** If an exception occurs between `connect()` and `close()`, the connection leaks. SQLite handles this gracefully (read-only access, file-level locks released on process exit), so it's unlikely to cause real problems, but context managers are the Pythonic pattern.
- **Suggested fix:** Wrap in `with` blocks. Low priority — all current `close()` calls are correctly placed.

### [ADVISORY] A8: Division-by-zero unguarded in promo coverage calculation

- **File:** `workbook/tab_promo_efficacy.py`
- **Line:** 265
- **Issue:** `covered_cost/total_cost*100` — if all promotions have `None` or `0` for `planned_cost`, `total_cost` would be 0, causing `ZeroDivisionError`.
- **Impact:** Extremely unlikely with the current dataset (188 promo rows), but unguarded.
- **Suggested fix:** `covered_cost / total_cost * 100 if total_cost else 0`.

### [ADVISORY] A9: `sys.path.insert` in entry point

- **File:** `build_workbook.py`
- **Line:** 12
- **Issue:** `sys.path.insert(0, str(Path(__file__).resolve().parent))` modifies the import path at runtime. This is a common pattern for script entry points but can cause import confusion if the project is installed as a package.
- **Impact:** Works correctly for direct script execution (`python build_workbook.py`). Would be fragile if the project were ever pip-installed.
- **Suggested fix:** Low priority. If packaging ever becomes relevant, add a `pyproject.toml` with proper entry points. For now, this is fine.

### [ADVISORY] A10: f-string SQL column interpolation

- **Files:** `workbook/tab_executive_pulse.py` (L87), `workbook/tab_retailer_risk.py` (L59, L65-66)
- **Issue:** SQL queries use f-string interpolation for column names: `f"SELECT AVG({col}) FROM sku_costs"`. The column names come from the trusted `CHANNEL_RATE_COLS` dict, not user input.
- **Impact:** Not a security vulnerability (values are hardcoded constants). But it establishes a pattern that could be dangerous if extended to dynamic inputs. Parameterized queries can't bind column names, so this is a common SQLite pattern.
- **Suggested fix:** Add a comment noting that `col` comes from a trusted constant dict. Or validate against an allowlist: `assert col in VALID_COLUMNS`.

## Checklist Results

### Reproducibility
- [x] Dependencies are declared (`requirements.txt`)
- [ ] **No hardcoded absolute paths** — FAIL: `scripts/build_db.py` line 15 (see B1)
- [x] A clear entry point exists (`build_workbook.py`)
- [x] Running the entry point produces the expected outputs (62/62 checks pass)
- [x] Random seeds are set where randomness is involved (N/A — no randomness)
- [x] Environment-specific configuration is separated from logic — PASS with exception of B1. Constants are at module top level. DB path is parameterized in the main flow.

### Code Quality
- [x] Functions are used for repeated logic — clean architecture: one query function + one build function per tab
- [x] Variable and function names are descriptive and consistent
- [x] No dead code — no commented-out blocks or orphan files in shipped code (dev/ is intentionally separate)
- [x] Complex logic has comments explaining why — promo ROI methodology, two-bucket framing, and taxonomy are well-documented
- [x] File organization follows a logical structure — `workbook/` package with shared styles, per-tab modules, centralized mappings

### Error Handling & Robustness
- [x] File reads check that the file exists or fail with a clear message — `build_db.py` raises `FileNotFoundError` with context
- [x] Data operations have validation — data validation on input cells, taxonomy fallback for unknown types
- [ ] **Edge cases considered** — PARTIAL: recovery rate edge case (B2), division-by-zero in promo coverage (A8)
- [x] Warnings and messages are not silently suppressed

### Output Quality
- [x] Outputs write to a defined output directory (`output/`)
- [x] File names are clear and consistent
- [x] Intermediate artifacts are separated from final deliverables (`dev/` vs shipped)
- [x] Outputs are not overwriting inputs

### Performance
- [x] No unnecessary full-dataset operations inside loops
- [x] Large data operations use appropriate approaches — SQL aggregation in the database, minimal Python-side iteration
- [x] No redundant re-reads of the same data source — each tab opens its own connection and runs targeted queries (acceptable for SQLite; no connection pooling needed)
