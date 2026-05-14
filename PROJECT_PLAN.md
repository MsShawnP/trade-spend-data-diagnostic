# Project Plan: Trade Spend Data Diagnostic
Created: 2026-05-14

## Objective

A trade-spend diagnostic delivered as a portfolio piece that doubles as a real-engagement wedge for a prospect CPG CEO. For a hands-on CEO, it must answer three things in this order: (1) what is actually being spent on trade, with retailer/SKU specificity; (2) whether to keep doing that, given the gap between budgeted and actual rates; (3) where to start plugging the leak.

The current build was assembled through Claude-assisted brainstorming without a thorough spec or independent ideation. It is technically complete but its analytical and narrative substance has not been independently validated. This phase is a v2 review-and-remediate pass to confirm the project delivers real value, not just a toolchain demo (Python + openpyxl + SQL + Power BI). Anything can change.

## Deliverables

All deliverables are subject to review. Anything can be dropped, rewritten, or restructured based on whether it serves the value test in Success Criteria.

1. **Excel workbook** (`build_workbook.py` → `output/trade_spend_diagnostic.xlsx`)
   - 7 tabs: Executive Pulse, Leak Diagnostic, Promo Efficacy, Retailer Risk, Deduction Ledger, Code Crosswalk, Methodology
   - Format: .xlsx with named ranges, Excel Tables, data validation, conditional formatting; in-cell data bars (no openpyxl chart objects)
   - Consumer: CEO (self-serve exploration), analyst (drill-down)
   - Status: Generates clean, 59/59 validation checks pass, **never visually verified in Excel**

2. **SQL query library** (`sql/` — 25 .sql files across 6 categories)
   - Standalone diagnostic queries extracted from workbook generation scripts
   - Consumer: analyst or controller reproducing or extending the findings
   - Status: All queries execute; 36/36 verification checks pass

3. **Power BI dashboard** (`powerbi/` — design docs, 7 CSVs, 49 DAX measures, build guide)
   - 4-page interactive companion (presentation layer, not analysis tool)
   - Consumer: CEO and team in meeting context; referenced from walkthrough
   - Status: Data model and measures pre-generated; **.pbix has not been assembled in Power BI Desktop**

4. **Walkthrough narrative** (`walkthrough.md` — 2,276 words)
   - Problem → methodology → findings → engagement upsell, 5 sections
   - Consumer: cold reader (recruiter, prospect, GitHub visitor)
   - Status: Drafted, all numbers verified against live DB queries

5. **Project README** (`README.md` — 76 lines)
   - Cold-visitor orientation: punchline, directory map, quick start
   - Consumer: GitHub visitor in the first 60 seconds
   - Status: Drafted

## Data Sources

1. **Cinderhaven Provisions simulated dataset** (`cinderhaven-data/` — git submodule)
   - SQLite database: `cinderhaven_product_master.db`, 22 tables, ~163 MB
   - Trailing-365 window: 2025-05-03 to 2026-05-02
   - Key tables: `scan_data`, `sku_costs`, `deductions`, `promotions`, `retailers`, `stores`, `deduction_codes`, `deduction_lifecycle`
   - Intentional quality issues (mirror real controller data): retailer-naming inconsistencies ("WFM" vs "Whole Foods"), 30–90 day deduction-to-promo lag, 292 unmapped deduction codes
   - Grain: one `deductions` row = single deduction event; one `scan_data` row = SKU × store × week_ending
   - **Infrastructure gap:** deduction pipeline (`07_*` → `15_*` scripts, `seed_deduction_*.sql`) committed locally to `cinderhaven-data` but never pushed to remote. Fresh clones rely on `scripts/build_db.py` fallback (copies pre-built DB from active local repo).

2. **Locked verified numbers** (`cinderhaven-data/TRADE_SPEND_VERIFICATION.md`)
   - Revenue: $25,593,052
   - Structural trade (rate-card): $4,435,052 (17.3%)
   - Operational/compliance waste (trailing-365, excl. promo_billback): $1,010,940 (4.0%)
   - All-in trade cost: $5,445,992 (21.3%)
   - Double-dips: 3 events, $19,306
   - Disputes: 1,409 filed, $98,216 recovered, 14.3% recovery rate

## Scope Boundaries

**In scope:**
- All five existing deliverables under review
- Two-bucket executive framing (structural trade + operational waste)
- Cinderhaven Provisions as the worked example
- Single-snapshot diagnostic (trailing-365 view only)
- Both audiences: prospect CPG CEO + public portfolio viewer

**Out of scope:**
- Real client data connectors or live integrations
- Multi-tenant or multi-company analysis
- Baseline modeling for promo ROI (simple pre/during/post stands per existing decision)
- Three-bucket trade framing (rejected during Arc 1; data does not support a meaningful third bucket)
- Causal inference or seasonality adjustment
- Time-series tracking (single trailing-365 snapshot only)

**Open pending review:**
- Whether Power BI adds value beyond the workbook given .pbix has never been assembled
- Whether the SQL query library is portfolio-worthy or scaffolding that should be de-emphasized
- Whether the walkthrough should be reframed for portfolio-first vs prospect-first audience

## Technical Approach

- **Language:** Python 3.10+
- **Key libraries:** openpyxl (workbook), pandas (transforms), rapidfuzz (fuzzy code matching), sqlite3 (DB access)
- **Database:** SQLite, single-file, consumed via git submodule
- **Visualization:** openpyxl in-cell data bars and Excel Tables in the workbook; Power BI Desktop for the interactive companion
- **Orchestration:** `build_workbook.py` (build) and `validate_workbook.py` (verify) at project root; `scripts/build_db.py` for DB acquisition
- **Project layout:**
  ```
  trade-spend-data-diagnostic/
  ├── build_workbook.py        # entry point
  ├── validate_workbook.py     # 59-check acceptance suite
  ├── workbook/                # one module per tab + shared styles
  ├── sql/                     # 25 standalone queries (6 categories)
  ├── powerbi/                 # design, CSVs, DAX measures, build guide
  ├── cinderhaven-data/        # submodule (data + build pipeline)
  ├── scripts/                 # build_db.py fallback
  └── output/                  # generated .xlsx (.gitignored)
  ```
- **Dependencies:** `requirements.txt` pins openpyxl, pandas, rapidfuzz
- **Workflow:** v1 and v2 run together. v1 handles session continuity — `/log` and `/wrap` against `PLAN.md`, `HANDOFF.md`, `DECISIONS.md`, `FAILURES.md`. v2 handles phase-gated review — this plan → code/data/prose review → remediation → audit → commit, with agents in `.claude/agents/` and artifacts at project root (`PROJECT_PLAN.md`, `REVIEW_*.md`, `REMEDIATION.md`, `AUDIT.md`). Both sets of files stay in place.

## Success Criteria

The project ships when a prospect CPG CEO and a public portfolio viewer can each do all three of these without further help:

1. **Understand what is actually being spent.** Within 2 minutes of opening the workbook or skimming the walkthrough, the reader knows the company spends 21.3% all-in on trade against a 17.3% structural budget, and that the 4-point gap is roughly $1M of operational waste. The numbers must be defensible: methodology stated, two-bucket framing justified, edge cases (double-dips, ghost promos, unmapped codes) accounted for.

2. **Decide whether to keep doing it.** The diagnostic makes the gap legible enough that the CEO can form a judgment — "this is the cost of doing business" vs "this needs to stop." That requires more than a number: it requires context (what should it be, what is addressable, how big is the prize in dollars).

3. **Have a path to plug the leak.** Concrete next actions: retailer-level P&L identifies WHO; deduction code crosswalk identifies WHICH categories of deductions; ghost-promo flag identifies UNAUTHORIZED hits; recovery rate identifies how much disputed money is being left on the table. The engagement upsell is the path if the CEO wants help executing — but only if the prior analysis is airtight.

**Plus v2 audit acceptance:**
- This PROJECT_PLAN.md matches reality
- All BLOCKING items in REMEDIATION.md are resolved
- Deliverables render or run end-to-end without manual fixes
- A cold operator can clone, run, and reproduce the locked numbers within ±tolerance

## Open Questions

1. **Power BI .pbix not assembled.** The Power BI deliverable exists as design + pre-generated measures + CSV data exports, but the .pbix file has never been compiled. Is this a real deliverable for v2 (operator must assemble) or scaffolding to drop and let the workbook stand alone?

2. **Submodule remote gap.** `cinderhaven-data` deduction pipeline scripts (07–15) and seed SQL never pushed to GitHub. A fresh `git clone --recurse-submodules` fails without the local DB-copy fallback. Push and verify, or document the fallback as the official path?

3. **Recovery rate above spec.** Recovered $98,216 of $686K disputed = 14.3%, vs an Arc 1 spec target of 5–10%. Cosmetic mismatch the data review can resolve, or analytically meaningful (e.g., does it undermine the "uncontested deductions" framing)?

4. **Two-bucket vs three-bucket framing.** Two-bucket was the Arc 1 decision. Has anything changed in the data or framing that would justify revisiting? Or is it still right for the portfolio's audience?

5. **Audience tension.** Prospect CEO (warm, action-oriented) and public portfolio viewer (cold, analytical) want different framing. README leans portfolio; walkthrough leans prospect. Resolve into one voice, or accept the split?

6. **Workflow plumbing leftovers.** `CLAUDE.md` at project root has empty Project Overview and Conventions sections; `.claude-project-url` is the placeholder `PASTE-YOUR-PROJECT-ID-HERE`. These are v1 scaffolding stubs that never got filled in. Fill in or leave?

## Risk Notes

- **Hollowness risk** (the operator's stated concern). The build is technically clean but may be analytically thin. Data and prose reviews must check whether conclusions actually follow from the analysis, not just whether arithmetic is correct.

- **Verification gap.** Workbook never opened in Excel; .pbix never compiled. Anything claimed in `HANDOFF.md` as "complete" past 2026-05-09 is software-claimed, not human-verified.

- **DB rebuild nondeterminism.** Waste rate varies ±$1,500 and dispute count ±1 between fresh DB builds. Validation tolerances accept this, but if locked numbers in the walkthrough or README drift from what a fresh rebuild produces, the portfolio piece will contradict itself.

- **Two audiences in one set of deliverables.** Prospect CEO and public portfolio viewer want different things. Trying to serve both without an explicit resolution risks mediocrity for both.

- **Post-arc creep.** Original 5 arcs are "complete," but 2+ post-arc sessions of bug fixes and redesign happened after. The v2 audit gate is the defense — define done, audit done, ship. Don't backslide into post-audit sprawl.

- **Engagement-wedge framing dilutes the diagnostic if substance is thin.** The walkthrough's upsell paragraph reads as bait if the prior 2,000 words aren't airtight.
