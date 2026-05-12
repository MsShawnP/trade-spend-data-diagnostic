# Trade Spend Data Diagnostic — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-05-09 — Adopt solo-dev workflow with /log, /wrap, /init slash commands
- **Why:** Project needs session continuity across multiple work sessions.
  The solo-dev workflow (from claude-solo-dev-workflow repo) provides
  structured handoff via five tracking files (CLAUDE.md, PLAN.md,
  HANDOFF.md, DECISIONS.md, FAILURES.md) and three slash commands
  (/log for mid-session entries, /wrap for end-of-session summaries,
  /init for new project scaffolding). Keeps context recoverable without
  relying on conversation history.
- **Scope:** Global — project process, all sessions
- **Do not:** Skip /wrap at end of session. The handoff log is what
  makes the next session productive immediately.

### 2026-05-09 — Use openpyxl for Excel workbook generation, not xlsxwriter
- **Why:** Brief specifies openpyxl. Both are viable — xlsxwriter is
  faster for write-only workbooks but openpyxl supports read/write,
  which matters if the workbook needs to be modified after generation.
  openpyxl also handles data validation and conditional formatting well.
  Decision may be revisited if openpyxl proves too slow for the 13-tab
  workbook.
- **Scope:** Excel workbook generation
- **Do not:** Use xlsxwriter unless openpyxl hits a blocking limitation.

### 2026-05-09 — Use SQLite as the project database, not PostgreSQL or DuckDB
- **Why:** Brief specifies SQLite. The dataset is small (~thousands of
  rows across all tables). SQLite is zero-config, ships with Python,
  and the .db file can live in the repo. No need for a server.
- **Scope:** Global
- **Do not:** Over-engineer the schema for a dataset this size.

### 2026-05-12 — Single computation layer (compute.py → CSVs → both outputs)
- **Why:** The workbook and dashboard independently computing from SQLite produced drift (recovery rate denominator, data quality thresholds, ghost promo context). Moving all business logic into compute.py and having both outputs read the same CSVs makes drift structurally impossible. 82 validation checks (10 compute + 59 workbook + 13 sync) confirm alignment.
- **Scope:** Global — pipeline architecture
- **Do not:** Add SQLite queries to the workbook package. Do not add independent business logic to DAX measures. All computation lives in compute.py.

### 2026-05-10 — Validate deliverables with a separate verification script, not inline assertions
- **Why:** `validate_workbook.py` reopens the generated .xlsx and checks it
  as a reader would — locked numbers, cross-tab consistency, tab structure,
  no formula errors. Separate from the build so validation runs against the
  actual output file, not in-memory state. Also serves as living documentation
  of acceptance criteria. Tolerances (±$2,000 on dollar amounts, ±2 on counts)
  handle DB rebuild nondeterminism.
- **Scope:** Workbook generation, future deliverables (dashboard, SQL queries)
- **Do not:** Embed validation in the build script. Keep build and verify as
  separate steps.

### 2026-05-10 — Use rapidfuzz, not fuzzywuzzy, for fuzzy matching
- **Why:** Faster, MIT-licensed (fuzzywuzzy is GPL), drop-in compatible API.
  No reason to use fuzzywuzzy unless rapidfuzz hits a blocking issue.
- **Scope:** requirements.txt, any fuzzy matching code
- **Do not:** Use fuzzywuzzy unless rapidfuzz has a specific incompatibility.

### 2026-05-09 — Consume cinderhaven-data via git submodule, do not duplicate data
- **Why:** cinderhaven-data is the single source of truth (21 tables,
  unified build pipeline). Three downstream repos consume it via
  submodule. Duplicating data creates drift. This project builds the
  database by running cinderhaven-data's build_db.py, then adds its
  own analysis/workbook layers on top.
- **Scope:** Global — project setup, CI, build scripts
- **Do not:** Copy data files or generation scripts into this repo.
  All data generation lives in cinderhaven-data.

### 2026-05-09 — Use two-bucket executive framing, not three-bucket
- **Why:** The 95% confidence investigation found that "off-invoice"
  is a funding mechanism, not a separate category — putting it in its
  own bucket double-counts. The promotions table's promo_cost sum
  ($20K) is too small to be a meaningful standalone bucket. The data
  supports two clean buckets:
  - Structural/planned trade: $4.4M (17.3%) — the negotiated rate-card
  - Operational/compliance: $1.0M (4.0%) — deductions beyond planned trade
  All-in: $5.4M (21.3%). CEO takeaway: "You budgeted 17%. You're
  spending 21%. The extra 4 points is operational waste."
- **Scope:** Executive summary tab, dashboard, walkthrough
- **Do not:** Use a three-bucket model unless the data is extended to
  support it. The detail tabs can break out deduction types and
  funding mechanisms — the executive summary stays two-bucket.

### 2026-05-09 — Audience is a hands-on CEO, not a controller
- **Why:** The immediate prospect's CEO likes Excel, vlookups, playing
  with data — but also wants quick answers. The workbook needs a
  dashboard/summary tab up front with the punchline, then detail tabs
  structured for self-service exploration. Both levels must work.
- **Scope:** Excel workbook tab ordering, README tab, summary tab design
- **Do not:** Bury the headline in tab 7. Lead with the answer.

---

## Data & Schema

### ~~2026-05-09 — Simulated data must hit specific target numbers from the brief~~
~~Original targets: 19.2% true trade rate, 16.8% deduction-only, ~$340K
off-invoice, $4.5M total trade, 42/38/20 category split.~~
**Superseded by 2026-05-09 entry below — verified numbers replace brief targets.**

### 2026-05-09 — Use verified numbers from unified cinderhaven-data build, not original brief targets
- **Why:** The 95% confidence session and Code investigation revealed the
  original brief's numbers were internally inconsistent. The cinderhaven-data
  repo now produces all trade spend and deduction data via a unified build
  pipeline (21 tables). Verified numbers from TRADE_SPEND_VERIFICATION.md:
  - Revenue: $25,593,052
  - Structural trade (sku_costs rate-card): $4,435,052 (17.3%)
  - Operational/compliance deductions (trailing-365, excl promo_billback): $1,010,940 (4.0%)
  - Promo_billback deductions (trailing-365): $211,513
  - All-in trade cost: $5,445,992 (21.3%)
  - Double-dips: 3 events, $19,306
  - Disputes: 1,409 filed, $98,216 recovered, 14.3% recovery rate
  The three-way split (contractual/promotional/operational) from the brief
  was not derivable and had a double-counting error ("off-invoice" is a
  funding mechanism, not a category). Replaced with a two-bucket executive
  framing: structural/planned trade (17.3%) + operational waste (4.0%).
- **Scope:** All deliverables — workbook, dashboard, walkthrough, SQL queries
- **Do not:** Reference the original brief's 19.2%, 16.8%, $340K, $4.5M,
  or 42/38/20 numbers. Use verified actuals only.

### 2026-05-09 — Build realistic quirks into simulated data sources
- **Why:** The credibility of the diagnostic depends on the data looking
  like what a controller actually deals with — inconsistent naming
  ("WFM" vs. "Whole Foods"), missing reason codes, date format
  mismatches, deduction dates lagging promo dates by 30–90 days. Clean
  data would make the matching trivial and the diagnostic pointless.
- **Scope:** All data generation scripts
- **Do not:** Make the quirks so extreme that matching becomes impossible.
  Target: ~68% clean match, ~23% internal inconsistency rate.

---

## Visualization

### 2026-05-10 — Automate DAX measure injection via pbi-tools, keep visual layout manual
- **Why:** The dashboard has 49 measures — entering them by hand is
  tedious and error-prone. pbi-tools can extract a .pbix into a folder
  structure, inject measure JSON files, and recompile. This automates
  the data model layer. Visual layout (positioning, slicers, formatting)
  cannot be reliably automated via pbi-tools — the report page JSON
  is undocumented and brittle. Honest split: measures automated,
  visuals manual.
- **Scope:** Power BI dashboard build workflow
- **Do not:** Attempt to generate visual layout JSON via pbi-tools.
  If pbi-tools is unavailable, measures can be created manually using
  `DAX_MEASURES.md` formulas.

---

## Output Formats

### 2026-05-09 — Excel workbook uses color-coded tabs: blue for input, green for output, gray for reference
- **Why:** Brief specifies clear input/output/reference tab separation.
  Color-coding is the fastest visual signal for a controller opening
  the workbook cold. Standard convention in financial workbooks.
- **Scope:** Excel workbook
- **Do not:** Use decorative colors or brand colors. Function over
  aesthetics.

### 2026-05-09 — Promo ROI uses simple pre/during/post methodology, not baseline modeling
- **Why:** Brief explicitly scopes this. Baseline modeling (seasonality
  adjustment, causal inference) is engagement-level work. Simple
  comparison with a stated assumption is sufficient for the portfolio
  piece and honest about its limitations.
- **Scope:** Promo ROI calculator tab and any ROI-related analysis
- **Do not:** Build sophisticated baseline models. Acknowledge the
  limitation in the documentation.

### 2026-05-12 — Workbook is the data tool, dashboard is the presentation layer
- **Why:** openpyxl charts can't compete with Power BI for visualization, and Power BI tables/slicers can't compete with Excel for data exploration. Each medium does what it's best at. The workbook has Excel Tables (pivot-ready), interactive input cells, and named ranges. The dashboard has narrative titles, KPI cards, charts, and text boxes.
- **Scope:** Both deliverables — workbook generation and Power BI PBIP generation
- **Do not:** Add openpyxl charts back to the workbook. Do not add tables or slicers to the Power BI dashboard.

### 2026-05-11 — Workbook is a data tool, not a dashboard. No openpyxl charts.
- **Why:** openpyxl charts are basic and send mixed signals next to
  controller-grade data. Power BI handles visualization. The workbook
  handles exploration — Excel Tables (pivot-ready), interactive input
  cells, named ranges. A CEO who right-clicks and gets "Summarize with
  PivotTable" trusts the tool.
- **Scope:** Excel workbook generation, all tabs
- **Do not:** Add openpyxl chart objects back. The one visual element
  is the in-cell data bar waterfall on Tab 1.

---

## Writing & Voice

[No entries yet — will be populated when walkthrough arc begins]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
