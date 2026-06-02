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

## [2026-06-02] P2 ALTER TABLE fix was throwaway — full recalibration replaced it
**What happened:** Added Kroger/Sprouts columns to the live database via ALTER TABLE + UPDATE, rebuilt the workbook, and reported "corrected" figures. Then the user requested a full seed recalibration, which ran build_db.py --force and regenerated the entire database from scratch — discarding the ALTER TABLE changes.
**Why it failed:** Treated P2 as an incremental fix (add two columns) when the underlying problem was structural (3-line seed producing $33M, flat unrealistic trade rates). The incremental fix was correct in isolation but was immediately superseded by the larger scope.
**What we learned:** Before patching a dataset, ask whether the dataset itself is about to be regenerated. If a recalibration is on the horizon, skip the incremental fix and go straight to the redesign. The ~15 minutes spent on ALTER TABLE + workbook rebuild + reporting was wasted.

## [2026-06-02] build_db.py --force destroyed the 5-line product_master
**What happened:** Ran `build_db.py --force` expecting it to regenerate all 5 product lines. It deleted the existing DB and re-seeded from `seed_product_master.sql`, which only had 3 product lines (AS=22, SC=16, PS=12). Dried Goods and Snack Bites disappeared. The first build produced $22.4M revenue from only 3 lines.
**Why it failed:** The 5-line product master came from the platform Postgres database, not the seed SQL. The seed SQL was never updated when the 5th line was added. Running --force from the seed SQL reverted to the 3-line version.
**What we learned:** Before running a destructive regeneration (--force), verify the seed files match the expected state. Specifically: check that seed_product_master.sql has the right product line count and SKU distribution. The seed SQL is the source of truth for build_db.py, not the previously-generated DB.
**Resolution:** Updated seed_product_master.sql with DG/SB product definitions (UPDATE statements for 20 reassigned SKUs) and broadened active_retailers. Took one extra build cycle to discover and fix.

## [2026-05-22] "Make everything dynamic" pass missed hardcoded numbers in Section 5
**What happened:** After making Tab 7 fully dynamic (25+ metrics queried from DB), Section 5 (Recovery Rate) still had `$987,798`, `$4,989,889`, and `19.8%` hardcoded as string literals — leftover from the Postgres era.
**Why it failed:** The dynamic-numbers refactor focused on Sections 1-2 (the heaviest hardcoding) and the data lineage section, but didn't audit every prose string in the file for embedded dollar figures. Manual review missed it; the 3-agent code review caught it.
**What we learned:** After a "make it dynamic" pass, always run the code review before committing. Automated reviewers catch literal-vs-computed inconsistencies that manual scanning misses, especially in long prose strings where numbers blend into text.
