# Trade Spend Data Diagnostic — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

---

## [2026-05-10] Session Wrap-Up — Full workbook build and validation
**Session focus:** Build all 7 tabs of the trade spend diagnostic
workbook, add workbook-level features, and validate end-to-end.

**Completed:**
- Copied pre-built DB (164 MB) from active cinderhaven-data repo into
  worktree (submodule data path)
- Verified locked numbers against DB — discovered DB was rebuilt since
  original verification; numbers shifted slightly (revenue $26.1M vs
  locked $25.6M) but structural story is identical
- Built `scripts/generate_workbook.py` — single-file generator that
  reads the SQLite DB and produces a 7-tab .xlsx workbook
- Built all 7 tabs in order: Methodology & Logic → Code Crosswalk →
  Deduction Ledger → Retailer Risk → Promo Efficacy → Leak Diagnostic
  → Executive Pulse
- Fixed schema mismatches discovered during build: `sku` vs `sku_id`,
  title-case retailer names in stores vs slugs in deductions,
  promotions uses `retailer`/`start_week`/`end_week` not
  `retailer_id`/`start_date`/`end_date`
- Fixed double-dip exposure total bug (LEFT JOIN produced duplicates,
  inflating total from $19K to $907K)
- Added workbook-level features: 8 named ranges, conditional formatting
  (ROI red/green, high op-rate highlighting, data bars on ledger),
  freeze panes on 4 tabs, auto-filters on 4 tabs, data validation on
  3 input areas, print areas, 6 navigation hyperlinks, 15 cell comments
- Ran 13-point validation suite — all checks passed
- Cross-tab consistency verified: structural/operational/promo amounts
  match exactly between Executive Pulse and DB; deduction ledger row
  count (2,374) matches DB; code crosswalk count (97) matches DB;
  retailer revenue sum matches DB

**Current state:** Workbook is complete and validated at
`output/trade_spend_diagnostic.xlsx`. All PLAN.md tasks for Arc 2 are
done. The workbook generates in ~15 seconds from the DB.

**Key files changed:**
- `scripts/generate_workbook.py` — created (full 7-tab workbook generator,
  ~1,470 lines)
- `output/trade_spend_diagnostic.xlsx` — created (7-tab workbook, ~2.5 MB)

**Key numbers in the generated workbook (from current DB):**
- Revenue: $26,089,284
- Structural trade: $4,467,628 (17.1%)
- Operational waste: $1,012,455 (3.9%)
- Promo billback: $213,017
- All-in trade cost: $5,693,100 (21.8%)
- Addressable improvement: $914,239
- Double-dips: 3 / $19,306 (2024, pre-trailing-365)
- Disputes: 1,410 filed, $98,216 recovered
- 75 promo events with ROI, 10 retailers with net-net margin

**Next steps:**
1. Push the cinderhaven-data deduction pipeline scripts to GitHub
   (still blocking clean submodule builds)
2. Visual review of workbook in Excel — verify chart rendering,
   conditional formatting appearance, print layout
3. Test interactive cells — change what-if trade rates, recovery
   target, promo window and verify recalculation
4. Consider updating TRADE_SPEND_VERIFICATION.md with current DB
   numbers (or rebuild DB to match locked numbers)
5. Begin Arc 3: Power BI dashboard (consumes workbook structure)

**Blockers:**
- DB numbers don't match original locked verification (DB was
  regenerated). Not blocking workbook — numbers are internally
  consistent. May want to rebuild DB from locked seed to restore
  exact match.

**Context for next session:** The workbook is done. The main remaining
work is visual QA in Excel and testing interactive features. The
`scripts/explore_db.py` can be deleted — it was a one-off. The
generator can be re-run anytime with `python scripts/generate_workbook.py`
(requires openpyxl and the DB at
`cinderhaven-data/data/cinderhaven_product_master.db`).

---

## [2026-05-10] Session Wrap-Up — Project setup and database wiring
**Session focus:** Set up project structure (submodule, build script, DB),
explore schema, prepare for workbook generation.

**Completed:**
- Added cinderhaven-data as git submodule (`git submodule add`)
- Created `scripts/build_db.py` — wraps submodule build, falls back to
  pre-built DB from active cinderhaven-data repo when submodule is incomplete
- Created `scripts/` and `output/` directories
- Copied pre-built database (163.7 MB, 22 tables) into submodule data path
- Explored full database schema — all column names mapped for every table
- Created `scripts/explore_db.py` (disposable helper for schema inspection)
- Verified openpyxl 3.1.5 installed and working
- Configured `.claude/settings.local.json` with `bypassPermissions` mode

**Current state:** Project structure is in place. Database is ready at
`cinderhaven-data/data/cinderhaven_product_master.db` with all 22 tables.
No workbook code written yet. The PLAN.md "set up project structure" task
is effectively done — needs locked number verification before marking
formally complete.

**Key files changed:**
- `.gitmodules` — created (cinderhaven-data submodule reference)
- `cinderhaven-data/` — submodule added, DB copied into `data/`
- `scripts/build_db.py` — created (build/locate database)
- `scripts/explore_db.py` — created (schema exploration helper)
- `scripts/` — created (empty dir for workbook generation code)
- `output/` — created (empty dir for generated .xlsx)
- `.claude/settings.local.json` — created (bypassPermissions mode)

**Key schema details for next session:**
- `scan_data`: columns are `week_ending` (not week_start), `dollars_sold`
  (not unit_price × units_sold). Revenue = SUM(dollars_sold).
- `sku_costs`: per-channel columns (`trade_spend_pct_walmart`,
  `trade_spend_pct_costco`, `trade_spend_pct_whole_foods`,
  `trade_spend_pct_regional`, `trade_spend_pct_unfi`, `trade_spend_pct_dtc`).
  Regional chains: Green Basket Market, Southside Grocers, Prairie
  Provisions, Mountain Pantry Co, Harbor Fresh → all use `_regional`.
- `deductions.retailer_id` uses slugs (walmart, costco, whole_foods, etc.)
- `retailers` table: 11 rows with display `name` and dispute portal info
- `promotions`: 188 rows across 75 distinct `promo_id`s; has `promo_cost`
  and `funding_mechanism` columns
- `deduction_codes`: 97 rows — `code_id`, `retailer_id`, `code`, `name`,
  `deduction_type`, `is_published`
- Trailing-365 window: `>= '2025-05-03' AND <= '2026-05-02'`
- Trailing-52w for revenue uses same dates on `week_ending`
- `stores.retailer` maps store_id to channel for scan_data joins

**Next steps:**
1. Verify locked numbers against the copied DB (run SQL checks)
2. Build Tab 7 (Methodology & Logic) — defines all calculations
3. Build Tab 6 → Tab 1 per the task spec
4. Workbook-level features (named ranges, formatting, validation)
5. End-to-end validation

**Blockers:**
- Permission config change (`bypassPermissions`) requires new session
- cinderhaven-data GitHub repo missing deduction scripts 07-15 (workaround
  in place via build_db.py fallback — not blocking workbook build)

**Context for next session:** Start a fresh session so `bypassPermissions`
takes effect. First action: run locked number verification SQL against the
DB. Then begin `generate_workbook.py` with Tab 7 (Methodology & Logic).
The build order is Tab 7 → 6 → 5 → 4 → 3 → 2 → 1 because earlier tabs
depend on calculations defined in later tabs. The `scripts/explore_db.py`
can be deleted — it was a one-off exploration tool.

---

## [2026-05-09] Session Wrap-Up — Workflow scaffolding and git init
**Session focus:** Set up solo-dev workflow infrastructure and project scaffolding

**Completed:**
- Created `.claude/commands/` with `log.md` and `wrap.md` slash commands
- Created `CLAUDE.md` (project overview and conventions template)
- Created `FAILURES.md` (empty, ready for entries)
- Initialized git repo (`git init`)
- Updated claude-solo-dev-workflow reference repo: added `slash-commands/init.md`, replaced `workflow-package/README.md` with version referencing `/init`
- Added trade-spend-data-diagnostic entry to MsShawnP GitHub profile README

**Current state:** All workflow files in place. Git repo initialized but
no commits yet. Data foundation complete from prior session (cinderhaven-data,
21 tables, locked numbers). No workbook code written. PLAN.md Arc 2
(workbook build) defined and ready to start.

**Key files changed:**
- `.claude/commands/log.md` — created (/log slash command)
- `.claude/commands/wrap.md` — created (/wrap slash command)
- `CLAUDE.md` — created (project overview template)
- `FAILURES.md` — created (empty log)
- `DECISIONS.md` — added workflow adoption decision

**Next steps:**
- Set up project structure (submodule, build script, workbook entry point)
- Build Tab 1: Executive Pulse
- Push to GitHub when ready

**Blockers:** None

**Context for next session:** Everything is scaffolded. The first real
task is PLAN.md's first unchecked item: "Set up project structure —
submodule, build script, workbook generation entry point." The
cinderhaven-data submodule needs to be added, and a Python entry point
created that connects to the .db and generates the workbook.

---

## 2026-05-09 — 95% confidence session + data reconciliation

**Started from:** Project initialized, no code written.

**Did:**
- Ran 95% confidence interview: established business question, audience
  (hands-on CEO), unified dataset strategy
- Discovered existing cinderhaven-data repo (90 SKUs, product_master,
  sku_costs, promotions, scan_data, stores) and retailer-deduction-recovery
  repo (full deduction schema, 3,333 deductions, deployed React app)
- Sent Code to investigate both repos — FINDINGS.md revealed original
  brief numbers were internally inconsistent (off-invoice double-count,
  $1.4M operational figure was 18-month not annualized, deduction-only
  rate was 3.6% not 12%)
- Decided: unified dataset in cinderhaven-data, consumed via submodule
- Sent Code to merge recovery project's generation scripts into
  cinderhaven-data, add promo_cost/funding_mechanism to promotions,
  add is_double_dip flag, align date windows
- Fixed DTC double-dips (moved to realistic retailers)
- Sent Code to re-verify — TRADE_SPEND_VERIFICATION.md produced with
  locked numbers
- Updated DECISIONS.md (superseded brief numbers, added 4 new decisions)
- Updated PLAN.md (completed Arc 1, defined Arc 2: workbook)

**State:** Data foundation complete. cinderhaven-data has 21 tables,
three downstream repos updated. Locked numbers verified. PLAN.md
Arc 2 defined (workbook build). No workbook code written yet.

Tab structure designed (7 tabs, down from original 13):
1. Executive Pulse (green) — punchline, waterfall, addressable improvement, responsibility matrix
2. Leak Diagnostic (green) — waste by category, double-dip alert, adjustable recovery rate
3. Promo Efficacy (green) — ROI with adjustable pre/post window, data quality indicators
4. Retailer Risk (green) — concentration, net-net margin, what-if trade rate inputs
5. Deduction Ledger (blue) — full trailing-365 data, auto-filters, freeze panes
6. Deduction Code Crosswalk (gray) — retailer codes → plain English
7. Methodology & Logic (gray) — definitions, data lineage, build date

Brief reviewed through 3 rounds of external critique. Interactive
elements defined (adjustable recovery rate, promo window, what-if
trade rates). Addressable improvement number to be calculated and
displayed on Tab 1.

**Next:** Set up project structure (submodule, build script, entry
point), then build Tab 1.

**Open items:**
- Recovery rate (14.3%) is above the 5–10% spec target from recovery
  project — cosmetic, not blocking
- Project repo structure not yet set up
- Addressable improvement $ needs calculation during build
- "Trade Spend Leakage" from brainstorm list unresolved — may just
  be this project by another name

---
