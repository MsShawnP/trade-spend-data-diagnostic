# Decisions — cinderhaven-data

## 2026-05-17 — Dataset shape: 50 SKUs, 157 weeks, 7 channels (including KeHE)

- **Why:** Platform (cinderhaven-data-platform) is the source of truth; SQLite seed must match its schema exactly. 50 SKUs is the curated catalog; 157 weeks covers the full Jan 2024 – Jan 2027 window; KeHE added as a distinct distributor channel.
- **Scope:** All generation scripts, validation targets, downstream consumers
- **Do not:** Revert to 90 SKUs or 104-week window. Do not merge KeHE back into UNFI — they have distinct wholesale pricing and order cycles.

---

## 2026-05-16: Completed full project audit and all 8 remediation moves

**Context:** Ran a 4-phase audit (baseline, internal review, landscape scan, differentiation) to retroactively apply quality standards to a pre-workflow codebase.

**Decision:** Executed all 8 ranked moves from the audit rather than cherry-picking. The audit confirmed that all moves were low-effort foundational work, and the "What NOT to Do" list (no API, no CLI config, no ML synthesis, no incremental generation) drew a clear line against scope creep.

**Key choices within the moves:**
- `with sqlite3.connect() as con:` over `contextlib.closing()` — simpler, gives transaction safety
- Instance-based `random.Random(SEED)` over global `random.seed()` — isolates RNG state per-script, protects reproducibility
- Module-level `rng` in scripts 01, 02, 04 (helpers outside main need it) vs local `rng` in scripts with all logic in main()
- Extracted 9 helpers from scan_data.py but left the tightly-coupled main loop intact — avoids 20-parameter function signatures
- Added SIM108, SIM102, SIM114, B905, B007, E741 to ruff ignore — style preferences, not bug indicators in data-heavy scripts

**Outcome:** Two PRs merged. Pipeline passes all 59 validation checks (24 base + 35 deduction). Codebase is now lint-clean, uses consistent patterns, and has project-level documentation.
