# PLAN — cinderhaven-data

**Tier:** Quick
**Status:** Complete (minor WARN on deduction volume)
**Current focus:** None — dataset rewrite shipped, build passing

---

## Goal: Extract `scripts/shared.py`
**Source:** Audit Phase 4 (2026-05-16)
**Category:** Foundational
**Priority:** 1

### Objective
Create a shared module with `DB_PATH`, `gtin_invalid`, `upc_missing`, and `REGIONAL_CHAIN_NAMES`. Update all 17 scripts to import from it instead of defining their own copies.

### Success Criteria
- `scripts/shared.py` exists with all four shared definitions
- Zero duplicate definitions of `DB_PATH`, `gtin_invalid`, `upc_missing`, or regional chain names remain in individual scripts
- `python scripts/build_db.py --force` still completes successfully
- Validation scripts still pass

### Context
Phase 2 findings #1 (3 copies of defect functions), #2 (5 copies of chain names), #3 (17 copies of DB_PATH). Highest-leverage single change in the audit.

### Decomposition: Extract `scripts/shared.py`

Goal: Eliminate all duplicated constants and utility functions across 17 scripts by centralizing them in one shared module.

Steps:
- [x] A1: Create `scripts/shared.py` with `DB_PATH` and `REGIONAL_CHAIN_NAMES`
    - Depends on: none
    - Done when: `python -c "from scripts.shared import DB_PATH, REGIONAL_CHAIN_NAMES; print(DB_PATH); print(REGIONAL_CHAIN_NAMES)"` prints the expected path and all 5 chain names
- [x] A2: Add `gtin_invalid` and `upc_missing` to `scripts/shared.py`
    - Depends on: A1
    - Done when: `python -c "from scripts.shared import gtin_invalid, upc_missing; assert gtin_invalid('bad'); assert upc_missing(None); print('OK')"` prints OK
- [x] A3: Migrate all 17 scripts to import `DB_PATH` from `shared`; remove local definitions
    - Depends on: A1
    - Done when: `grep -r "DB_PATH = Path" scripts/ --include="*.py"` returns only `shared.py`
- [x] A4: Migrate 5 scripts to import `REGIONAL_CHAIN_NAMES` from `shared`; remove local definitions
    - Depends on: A1
    - Done when: `grep -rE "REGIONAL_CHAIN|REGIONAL_CHAINS" scripts/ --include="*.py"` returns only `shared.py` (plus any usage-site imports)
- [x] A5: Migrate 3 scripts to import `gtin_invalid`/`upc_missing` from `shared`; remove local definitions
    - Depends on: A2
    - Done when: `grep -rE "def gtin_invalid|def upc_missing" scripts/ --include="*.py"` returns only `shared.py`
- [x] A6: Full pipeline verification
    - Depends on: A3, A4, A5
    - Done when: `python scripts/build_db.py --force` completes successfully and both validation scripts pass

---

## Goal: Update README to reflect seed role
**Source:** Audit Phase 4 (2026-05-16)
**Category:** Close gap
**Priority:** 2

### Objective
Update README.md to accurately describe this repo's current role as a seed source for `cinderhaven-data-platform`, rather than the primary data backbone for three downstream repos.

### Success Criteria
- README intro reflects seed role
- Downstream repo references updated or reframed
- No misleading claims about being the "single source of truth" if that's now the platform

### Context
Phase 1 gap analysis: role has narrowed from primary data source to seed generator. README still describes the old role.

---

## Goal: Add `pyproject.toml` + ruff config
**Source:** Audit Phase 4 (2026-05-16)
**Category:** Close gap
**Priority:** 3

### Objective
Add a minimal `pyproject.toml` with ruff configuration. Run ruff and fix any issues. No runtime dependencies added — ruff is dev-only.

### Success Criteria
- `pyproject.toml` exists with `[tool.ruff]` section
- `ruff check scripts/` passes clean
- No third-party runtime dependencies introduced

### Context
Phase 1: no linting config exists. Phase 4: every maintained project should have this. Easy win.
