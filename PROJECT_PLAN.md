# Project Plan: Trade Spend Data Diagnostic
Created: 2026-05-14
Updated: 2026-05-14 (post-Gemini scope review)

## Objective

A trade-spend diagnostic that delivers real value to a hands-on CPG CEO — a portfolio piece that doubles as a real-engagement wedge for a prospect. The bar is not "the tool runs." The bar is "the CEO sees something on Monday morning that makes them call a meeting." The diagnostic must answer three things in this order: (1) what is actually being spent on trade, with retailer/channel/SKU specificity *and an external yardstick*; (2) whether to keep doing that, given the gap to benchmark and the addressable dollars; (3) where to start plugging the leak — concrete, prioritized, defensible against the CEO's own VP of Sales.

The current build was assembled through Claude-Chat-led brainstorming without an independent spec. It is technically complete (59/59 validation checks pass) but Gemini's cross-model scope review verdict is sharp: **70% toolchain / 30% value**. This phase is a review-and-remediate pass that closes that gap — by adding analytical depth (channel, addressability, benchmark, trend), tightening narrative (executive memo first, scaffolding second), and pre-empting defensibility challenges (VP of Sales rebuttal log).

## Deliverables

The deliverable set is narrowing. Power BI and the SQL query library are demoted from "shipped deliverables" to "exploratory work in `/dev/`" — both were originally included to demonstrate tool-chain breadth (Claude Chat told the operator she "HAD to prove SQL" and Power BI dashboards). The operator's actual goal is a value-deliverable for a CEO, not a competency demo. The four things below are what ships.

1. **Excel workbook** (`build_workbook.py` → `output/trade_spend_diagnostic.xlsx`) — primary CEO-facing artifact
   - Tabs (post-remediation): **Executive Pulse** (must stand alone — leads with the controversial finding), **Leak Diagnostic** (with new Addressability column), **Promo Efficacy**, **Retailer Risk** (with new Channel rollup: Grocery / Mass / Club / Natural / Distributor / DTC), **Deduction Ledger** (with taxonomy bucket per row), **Code Crosswalk**, **Methodology**
   - Adds: sparkline trends within trailing-365 window, external benchmark band on Executive Pulse, deduction taxonomy (Probable Waste / Contractual / Unknown) replacing raw "unmapped codes" count
   - Format: `.xlsx` with named ranges, Excel Tables, data validation, conditional formatting, in-cell data bars, sparklines
   - Status: Generates clean, 59/59 validation checks pass, **never opened in Excel for visual QA** (now a blocking audit prereq)

2. **Walkthrough narrative** (`walkthrough.md`) — cold-reader story
   - Structure: punchline → controversial finding → methodology → defensibility → engagement upsell
   - Adds: one-page Executive Memo condensation (if walkthrough doesn't fit one page when stripped, narrative is too bloated)
   - Status: 2,276 words, drafted, numbers verified; needs reframing around the Monday-morning finding

3. **Project README** (`README.md`) — first-60-seconds visitor orientation
   - First line: the punchline (e.g., "Cinderhaven Provisions is leaking $1M of margin to operational waste — here's where"). Not "how to run the script."
   - Status: Drafted, needs punchline-first rewrite

4. **Defensibility log** (`DEFENSIBILITY.md`) — **new deliverable**
   - Every "waste" / "leak" claim gets a one-line defense: why this is not a standard fee, not a contractual obligation, not a misunderstanding. Pre-empts the "VP of Sales rebuttal" (the salesperson saying "the consultant doesn't get it, that's just slotting").
   - Defines the rules for the deduction taxonomy buckets.
   - Status: Does not exist; create during remediation.

**Demoted to `/dev/` (exploratory, not shipped):**

- **`/dev/powerbi/`** — design docs, CSVs, DAX measures. Reference for future implementation. `.pbix` not assembled (operator decision: no value in proving Power BI competency). README and walkthrough do NOT claim there is a clickable dashboard.
- **`/dev/sql/`** — 25 standalone queries. Reference for analysts/controllers reproducing findings. Not a CEO-facing artifact. README mentions for reproducibility, not as a primary deliverable.

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

3. **External category benchmark** (new — source to be selected during remediation)
   - Target: a defensible "natural / specialty CPG trade rate" band to place 17.3% structural and 21.3% all-in against
   - Candidate sources: public NielsenIQ / Cadent / Acosta benchmark reports, peer 10-Ks, trade-association data, or transparent operator-generated estimate with methodology note
   - Without a yardstick, the headline numbers are decoration

## Scope Boundaries

**Scope discipline.** This is a remediation pass, not a rebuild. The locked data, two-bucket framing, and 59 validation checks stay. The "anything can change" framing from the clarify interview was too broad — Gemini correctly flagged it as dangerous. The actual rule: **anything that fails the value test changes; anything that passes stays.**

**In scope — existing:**
- Excel workbook (primary CEO-facing deliverable)
- Walkthrough and README
- Cinderhaven Provisions as worked example
- Two-bucket framing (structural trade + operational waste)
- Single-snapshot trailing-365 (now with within-window sparkline trend)
- Both audiences: prospect CPG CEO + public portfolio viewer

**In scope — additions from this review:**
- **Channel layer** — Grocery / Mass / Club / Natural / Distributor / DTC rollup on Retailer Risk + Executive Pulse
- **Addressability column** — every Leak Diagnostic row tagged Contractual / Disputable / Unknown; "total addressable $" = sum of Disputable, surfaced on Executive Pulse
- **External category benchmark** — sourced or estimated trade-rate band; placed against 17.3% / 21.3% on Executive Pulse
- **Sparkline / trend within trailing-365** — weekly waste run-rate; shows accelerating / stable / fading
- **Deduction taxonomy** — 292 unmapped codes bucketed into Probable Waste / Contractual / Unknown (not left as a raw count)
- **Defensibility log** (new deliverable, `DEFENSIBILITY.md`)
- **Executive Memo** — one-page condensation derived from walkthrough
- **README punchline rewrite** — controversial finding leads, not "how to run"
- **Operator visual QA of workbook in Excel** — blocking audit prereq

**Out of scope as shipped deliverables (now in `/dev/`):**
- Power BI `.pbix` — operator has used PBI before, no competency to prove. Lives in `/dev/powerbi/` as reference design.
- SQL query library — included originally on misplaced Claude-Chat advice. Lives in `/dev/sql/` as reproducibility reference.

**Out of scope (hard):**
- Real client data connectors or live integrations
- Multi-tenant / multi-company analysis
- Causal inference, seasonality adjustment beyond the within-window sparkline
- Three-bucket trade framing (Arc 1 decision, not relitigating)
- Promo ROI baseline modeling beyond pre/during/post stands

## Technical Approach

- **Language:** Python 3.10+
- **Key libraries:** openpyxl (workbook), pandas (transforms), rapidfuzz (fuzzy code matching), sqlite3 (DB access)
- **Database:** SQLite, single-file, consumed via git submodule
- **Visualization:** openpyxl in-cell data bars, sparklines, Excel Tables, conditional formatting
- **Orchestration:** `build_workbook.py` (build) and `validate_workbook.py` (verify) at project root; `scripts/build_db.py` for DB acquisition
- **Project layout (post-remediation):**
  ```
  trade-spend-data-diagnostic/
  ├── build_workbook.py        # entry point
  ├── validate_workbook.py     # acceptance suite (will grow past 59 checks)
  ├── workbook/                # one module per tab + shared styles
  ├── cinderhaven-data/        # submodule (data + build pipeline)
  ├── scripts/                 # build_db.py fallback
  ├── dev/
  │   ├── sql/                 # 25 standalone queries (was at /sql)
  │   └── powerbi/             # design + measures (was at /powerbi)
  ├── output/                  # generated .xlsx (.gitignored)
  ├── PROJECT_PLAN.md          # this file (v2)
  ├── DEFENSIBILITY.md         # new — claim defenses
  ├── walkthrough.md           # cold-reader narrative
  ├── EXECUTIVE_MEMO.md        # new — one-page condensation
  ├── README.md                # punchline-first
  └── [v1 tracking: PLAN.md, HANDOFF.md, DECISIONS.md, FAILURES.md, CLAUDE.md]
  ```
- **Dependencies:** `requirements.txt` pins openpyxl, pandas, rapidfuzz
- **Workflow:** v1 and v2 coexist. v1 handles session continuity — `/log` and `/wrap` against `PLAN.md`, `HANDOFF.md`, `DECISIONS.md`, `FAILURES.md`. v2 handles phase-gated review — this plan → code/data/prose review → remediation → audit → commit, with agents in `.claude/agents/` and artifacts at project root (`PROJECT_PLAN.md`, `REVIEW_*.md`, `REMEDIATION.md`, `AUDIT.md`). Both sets of files stay in place.

## Success Criteria

The diagnostic ships when both a prospect CPG CEO and a cold portfolio viewer pass every one of these:

1. **10-second punchline test.** README first line and walkthrough opener state the controversial finding in plain English with the dollar magnitude. No methodology, no caveats, no toolchain. A CEO reading on their phone in line at Starbucks must get the point in 10 seconds.

2. **Monday morning test.** At least one finding in the analysis is surprising or pointed enough that the CEO would call a meeting about it on Monday morning. "Trade spend is high" fails. "Retailer X is hitting us with $200K of unauthorized billbacks on SKUs we don't even sell there" passes. The data-science review's job is to find this; the prose review's job is to make sure it lands first.

3. **VP of Sales rebuttal test.** Every claim in the "waste" bucket has a documented defense in `DEFENSIBILITY.md`. When the CEO walks the diagnostic to their VP of Sales and the VP says "that's just slotting, the consultant doesn't get it," the document already answers. Without this, every finding is one rebuttal away from being dismissed.

4. **Plug-the-leak test.** Concrete next actions, prioritized. Channel rollup identifies WHERE the leak concentrates. Addressability column identifies HOW MUCH is recoverable. Retailer Risk identifies WHO. Deduction taxonomy identifies WHICH categories. The engagement upsell is the path if the CEO wants help executing — earned by the prior analysis being airtight.

5. **Benchmark grounding.** 17.3% structural and 21.3% all-in are placed against a defensible category benchmark band on Executive Pulse. Without a yardstick, the numbers are decoration.

**v2 audit acceptance:**
- This PROJECT_PLAN.md matches reality (no aspirational claims about what's shipped)
- All BLOCKING items in `REMEDIATION.md` resolved
- Workbook visually QA'd in Excel by the operator (every tab opened, formulas inspected, formatting verified)
- Cold operator can clone, run, and reproduce locked numbers within tolerance

## Open Questions

Most of the original open questions are closed by the Gemini review and operator decisions. Remaining live questions:

1. **Defensibility log granularity.** Category-level defenses (one entry per deduction-code bucket) or line-item-level (one entry per top finding)? Probably category-level for v1; line-level if specific findings provoke specific challenges during build.

2. **External benchmark sourcing.** Public industry report (NielsenIQ, Cadent, Acosta), peer 10-K triangulation, operator-generated estimate with methodology note, or punted with an explicit limitation acknowledgment? Pick one and defend the choice.

3. **Visual QA timing and depth.** Operator opens the workbook in Excel during remediation (find issues, fix, re-verify) or during audit (final sign-off only)? Recommend during remediation so issues land in the tracker.

4. **`/dev/` vs deletion for Power BI / SQL.** Move to `/dev/` (preserved as reference) or remove from the repo entirely? `/dev/` shows the work was considered; deletion makes the repo lean. Default to `/dev/`.

5. **Workflow plumbing stubs.** `CLAUDE.md` Project Overview and Conventions sections are empty; `.claude-project-url` is the placeholder `PASTE-YOUR-PROJECT-ID-HERE`. Fill in during remediation, or leave as personal-workflow files that don't ship to a client?

## Risk Notes

- **Hollowness risk** (operator's stated concern, Gemini-confirmed at 70/30 toolchain/value). The additions captured above are the fix. If they're skipped or implemented half-heartedly, the project ships as toolchain.

- **VP of Sales rebuttal risk.** Without `DEFENSIBILITY.md`, every finding is one explanation-by-insider away from being dismissed. The defensibility log is not optional decoration.

- **Synthetic data "uncanny valley."** Gemini flagged that 292 unmapped codes is suspiciously clean. Real controller data is messier and more irregular. The data review must check whether the simulated quality issues feel real or engineered; if engineered, either accept the limitation explicitly in Methodology or add controlled irregularity.

- **Seasonality blindness.** Single trailing-365 is a death certificate, not a health monitor. The within-window sparkline mitigates partially. The Methodology tab must explicitly acknowledge the limitation: "this is a point-in-time diagnostic; a quarterly cadence would surface direction."

- **Verification gap (now a hard gate).** Workbook never opened in Excel. Audit cannot pass until operator has opened, navigated, and signed off on every tab.

- **Benchmark defensibility.** A weak external benchmark is a new attack surface. Method must be transparent and the band conservative. If the only available source is operator estimate, label it clearly and explain the basis.

- **DB rebuild nondeterminism.** Waste rate varies ±$1,500 and dispute count ±1 between fresh DB builds. Validation tolerates this; locked walkthrough/README numbers must reconcile to ranges, not points. Otherwise a fresh clone produces different numbers than the narrative claims.

- **Audience tension.** Prospect CEO vs public portfolio viewer. Post-remediation framing: punchline-first README + Executive Memo + workbook serves the prospect; the same artifacts serve the portfolio viewer because both audiences want "what's the point in 10 seconds" before "how was this done."

- **Post-arc creep defense.** v2 audit gate is explicit. After audit pass, ship. Do not start a sixth post-arc to add "one more thing."

## Change Log

- **2026-05-14** — Initial PROJECT_PLAN.md written from operator clarify interview. Framed as review-and-remediate pass against existing build.
- **2026-05-14** — Workflow note corrected: v1 and v2 coexist (do not migrate).
- **2026-05-14** — Gemini cross-model scope review folded in:
  - Power BI demoted from deliverable to `/dev/powerbi/` reference (operator: no interest in proving PBI competency)
  - SQL query library demoted from deliverable to `/dev/sql/` (operator: included on misplaced Claude-Chat advice)
  - Added Defensibility log as new 4th shipped deliverable
  - Added Executive Memo (one-page condensation) as deliverable extension
  - Added 4 analytical additions to scope: channel layer, addressability column, external benchmark, within-window sparkline trend
  - Added deduction taxonomy requirement (bucket the 292 unmapped codes)
  - Reframed Success Criteria around: 10-second punchline, Monday morning, VP of Sales rebuttal, plug-the-leak, benchmark grounding (replacing the prior "2-minute workbook open" framing — CEOs don't open 7-tab workbooks)
  - Reframed scope discipline: "additions that serve the value test, not arbitrary rebuilds"
  - Added new risks: VP rebuttal, uncanny valley, seasonality blindness, benchmark defensibility
  - Visual QA in Excel promoted to a hard audit gate
