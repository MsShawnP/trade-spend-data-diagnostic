# Handoff — cinderhaven-data

**Last updated:** 2026-05-17
**Status:** Build passing (33 PASS / 4 WARN / 0 FAIL). Minor calibration gap on deductions.

## 2026-05-17 17:00

**Started from:** "DO 1" — rewrite generation scripts for 50-SKU, 157-week, 7-channel dataset matching platform export.

**Did:** Rewrote 14/18 scripts. Added KeHE channel. Changed date window to 157 weeks (2024-01-01 → 2027-01-02). Dynamic tier assignment. Calibrated VELOCITY_SCALE (0.66→1.21) and bumped deduction rates. Two commits: structural changes + calibration fixes.

**State:** Build passes at 130 MB. Revenue $24.3M (target $23-27M). Deductions 7,973 (WARN, target 10-16K). Disputes 3,580 (WARN, target 4-8K). Two untracked planning artifacts to clean up. Branch `main`, 2 commits ahead of origin.

**Next:** Either widen deduction/dispute target ranges in `15_validate_deductions.py` to reflect 50-SKU reality, or do a third calibration pass. Clean up untracked files (`cinderhaven-data-consistency-plan.md`, `cinderhaven_product_master.db`).

---

## 2026-05-16

**Started from:** Fresh audit of the repo.

**Did:** Full 4-phase project audit + all 8 remediation moves (PR #2, PR #3 merged).

**State:** All 18 scripts lint-clean, pipeline produces valid 164MB database, 59/59 validation checks pass.

**Next:** Driven by platform schema changes if they arise.
