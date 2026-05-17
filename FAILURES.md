# Failures & Lessons Learned

<!-- Entries are appended by /log when something fails or is abandoned. -->
<!-- Format: ## [YYYY-MM-DD] What Failed -->

## [2026-05-10] Submodule build_db.py fails — missing deduction pipeline scripts
**What happened:** Running `python cinderhaven-data/scripts/build_db.py`
built the first 8 tables (scan_data, product_master, sku_costs, etc.) but
crashed at step 9 (`07_seed_deduction_tables.py`) because the deduction
pipeline scripts (07 through 15) and SQL seeds (`seed_deduction_schema.sql`,
`seed_deduction_static.sql`) were never pushed to the GitHub repo. The
local active copy at `C:\Users\mssha\projects\active\cinderhaven-data` has
all scripts, but the remote only has the base pipeline.
**Why it failed:** The deduction pipeline was merged into cinderhaven-data
locally during the 2026-05-09 session but the changes were committed
locally without being pushed to GitHub. The submodule clone pulls from
the remote, which is behind.
**What we learned:** Always verify that submodule changes are pushed to
the remote before depending on them in downstream repos. The build script
should handle partial builds gracefully.
**Action items:**
- Push the deduction pipeline scripts from the active cinderhaven-data
  repo to GitHub (separate task, not blocking workbook)
- The `scripts/build_db.py` fallback (copy pre-built DB) works for now

## [2026-05-17] Merge failed — master had silently migrated to Postgres
**What happened:** Attempted `git merge` of worktree branch (SQLite, updated numbers) into master. Got 100+ conflicts: every SQL query used different table names (`disputes` vs `stg_disputes`), different parameter markers (`?` vs `%s`), and different connection methods. Master had fully migrated to Postgres in a prior session (commits `4b97729` and `e22acfb`) despite DECISIONS.md explicitly stating "SQLite stays."
**Why it failed:** Two sessions made contradicting architectural choices without checking the decision log. The Postgres session didn't read or update DECISIONS.md before migrating. No guard existed to prevent architectural drift between concurrent worktrees/sessions.
**What we learned:** Before making architectural changes, always check DECISIONS.md for existing rulings. The decision log exists precisely to prevent this — but only works if every session reads it first. Worktrees that diverge significantly from main should be merged early or abandoned, not left to accumulate drift.
**Resolution:** Reset master to the SQLite branch (the user-approved architecture), preserved old master as `backup/master-before-reset`, selectively recovered writing artifacts. The reset approach was faster and safer than resolving 100+ conflicts across incompatible architectures.
