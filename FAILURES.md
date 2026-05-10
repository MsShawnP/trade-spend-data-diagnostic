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

## [2026-05-10] DB numbers don't match locked verification
**What happened:** The pre-built DB copied from the active
cinderhaven-data repo produces different numbers than the locked
values in TRADE_SPEND_VERIFICATION.md. Revenue is $26.1M vs locked
$25.6M (+$496K, ~2%). Other metrics shifted proportionally.
**Why it failed:** The cinderhaven-data build pipeline uses random
seeds for data generation. The DB was rebuilt after the verification
was done on 2026-05-09, producing a new random draw.
**What we learned:** Lock the random seed in the build pipeline, or
preserve the verified DB snapshot. Random data generation without
fixed seeds means verification is ephemeral.
**Action items:**
- Either rebuild DB with the original seed to restore exact match,
  or update TRADE_SPEND_VERIFICATION.md with current DB numbers
- Consider adding a `--seed` flag to cinderhaven-data's build_db.py
- The workbook is internally consistent (all numbers come from the
  same DB) — the mismatch is cosmetic, not structural

## [2026-05-10] Double-dip total inflated by LEFT JOIN duplicates
**What happened:** The Leak Diagnostic tab showed a double-dip
exposure total of $907K instead of the correct $19K. The LEFT JOIN
between deductions and promotions produced multiple rows per
deduction (one per matching promo row), and the sum iterated over
all rows rather than deduplicating.
**Why it failed:** Generator code used
`sum(d['amount'] for d in dd if d['deduction_id'] in seen)` which
sums all JOIN result rows, not just unique deductions.
**What we learned:** When summing amounts from a JOIN that can
produce 1:N results, accumulate the total during the deduplication
loop rather than summing the raw result set.
**Action items:** Fixed in same session — `dd_total` accumulator
added inside the `seen` deduplication loop
