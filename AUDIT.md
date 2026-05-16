# Project Audit

## Phase 1: Baseline Assessment
**Date:** 2026-05-16
**Project:** Trade Spend Data Diagnostic (Cinderhaven Provisions)

### What Was Intended

A portfolio piece that doubles as a real-engagement wedge for a CPG
CEO prospect. The diagnostic quantifies how much a mid-market company
overspends on trade spend ($1M/yr operational waste on $25.6M
revenue), classifies every deduction defensibly, and tells the CEO
what to do Monday morning. Four shipped deliverables: Excel workbook,
executive memo, defensibility log, walkthrough narrative.

Power BI dashboard and SQL query library were originally included but
demoted to `/dev/` reference after a cross-model scope review
concluded the project was "70% toolchain / 30% value." The pivot
narrowed scope to CEO-facing value delivery.

### What Exists Today

**Main branch (e6f5379) — the current truth:**
- 7-tab Excel workbook generating from Postgres (Fly.io production)
- 62/62 validation checks passing
- EXECUTIVE_MEMO.md — one-page "Monday morning" condensation
- DEFENSIBILITY.md — deduction taxonomy + rebuttal text
- walkthrough.md — 2,276-word narrative
- README.md — punchline-first ("leaking $1M of margin")
- Power BI and SQL moved to `/dev/` (not shipped)
- Dead code mostly removed; `scripts/build_db.py` still present but unused
- Dependencies slimmed to openpyxl + psycopg2-binary
- Prior audit passed (AUDIT.md, 2026-05-15, verdict: PASS)

**This worktree (trusting-hellman) — stale:**
- Pre-v2 structure (SQLite, powerbi/ and sql/ at top level)
- Does not reflect the shipped state
- Should not be the basis for prospect delivery

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Workbook | openpyxl |
| Database | PostgreSQL (Fly.io, `public_staging` schema) |
| Data | Cinderhaven simulated dataset (21 tables, trailing-365 window) |
| Validation | Custom 62-check acceptance suite |
| Hosting | Git repo (not yet confirmed public on GitHub) |

### Project Health Indicators

- **Activity:** Last commit 2026-05-15 (1 day ago). Active.
- **Documentation:** Extensive — README, walkthrough, exec memo, defensibility log, methodology tab, multiple review artifacts.
- **Test coverage:** 62 automated validation checks on workbook output. No unit tests on individual modules.
- **Dependencies:** Minimal (2 packages). openpyxl unpinned (advisory item).
- **Code quality:** Simplification pass completed. Some dead code remains (`scripts/build_db.py`).

### Gap Analysis (Intended vs. Actual)

The project is **substantially complete** against its stated plan.
All 4 shipped deliverables exist, the audit passed, and the code
runs against production Postgres.

**Gaps relevant to "prospect tries it":**

1. **Delivery format unclear.** Does the prospect receive a pre-built
   .xlsx file, or do they clone a repo and run `build_workbook.py`?
   The latter requires Postgres access (DATABASE_URL). A CEO won't
   do that.

2. **Visual QA status ambiguous.** PROJECT_PLAN.md flagged "workbook
   never opened in Excel" as a blocking gate. The audit says PASS,
   but it's unclear if a human actually opened it in Excel.

3. **GitHub repo status unknown.** Is this repo public? Can the
   prospect access it? Or is delivery via email/shared drive?

4. **Dead file debris.** `scripts/build_db.py`, stale worktrees,
   review artifacts (REVIEW_CODE.md, REVIEW_DATA.md, REVIEW_PROSE.md,
   REMEDIATION.md) — fine for process documentation but noisy for a
   prospect viewing the repo.

5. **No license chosen.** README previously said "Not yet determined."
   Current README doesn't mention one. A LICENSE file exists but
   content not verified.

6. **Stale worktree.** This branch is behind main. Should be cleaned up.

### Audit Motivation

Getting ready for a prospect to try the deliverable. The audit needs
to answer: is this prospect-ready as-is, or what specifically needs
to happen first?

---

## Phase 2: Internal Review
**Date:** 2026-05-16
**Dimensions reviewed:** Code Quality, Architecture, Tests,
Documentation, Performance, Security, UX, DevEx

### Top Opportunities (by leverage)

| # | Finding | Dimension | Impact | Effort | Leverage | Severity |
|---|---------|-----------|--------|--------|----------|----------|
| 1 | README references removed submodule — Quick Start is broken | Docs | 5 | 1 | 5.0 | Critical |
| 2 | No pre-built .xlsx to hand a prospect — requires Postgres to build | DevEx | 5 | 1 | 5.0 | Critical |
| 3 | 10+ internal process files visible in public repo | Docs | 4 | 1 | 4.0 | Important |
| 4 | README says "License: Not yet determined" but MIT LICENSE file exists | Docs | 3 | 1 | 3.0 | Important |
| 5 | `database_url` param passed through call chain but never used | Code | 3 | 1 | 3.0 | Minor |
| 6 | Dead `scripts/build_db.py` (SQLite-era, obsolete after Postgres) | Code | 2 | 1 | 2.0 | Minor |
| 7 | `.claude-project-url` with placeholder "PASTE-YOUR-PROJECT-ID-HERE" | DevEx | 2 | 1 | 2.0 | Minor |
| 8 | 9 stale local worktree branches | DevEx | 2 | 1 | 2.0 | Minor |
| 9 | openpyxl not version-pinned in requirements.txt | Code | 2 | 1 | 2.0 | Minor |
| 10 | `bisect` imported inside function body in tab_promo_efficacy | Code | 1 | 1 | 1.0 | Minor |
| 11 | No unit tests — only output validation (62 checks) | Tests | 2 | 4 | 0.5 | Minor |

### Detailed Findings

#### Documentation (most findings here — this is the prospect-facing surface)

**CRITICAL: README Quick Start is broken.**
The README tells users to `git clone --recurse-submodules` and
references `cinderhaven-data/` as a submodule. But `.gitmodules` was
removed during the Postgres migration. The submodule does not exist in
HEAD. A prospect following the Quick Start gets a confusing error.
The README needs a rewrite: remove all submodule references, update
the directory listing (remove `cinderhaven-data/`), and rewrite Quick
Start for the Postgres-based workflow — or, more likely, remove the
"build it yourself" instructions entirely and just link to the
pre-built .xlsx.

**IMPORTANT: Internal process files clutter the public repo.**
The repo contains 10+ internal files that expose the development
process but confuse a prospect:
- `PLAN.md`, `HANDOFF.md`, `DECISIONS.md`, `FAILURES.md` — session
  workflow tracking
- `PROJECT_PLAN.md` — internal planning with references to "Claude
  Chat" and "Gemini scope review"
- `REVIEW_CODE.md`, `REVIEW_DATA.md`, `REVIEW_PROSE.md` — internal
  review artifacts
- `REMEDIATION.md` — bug tracker
- `AUDIT.md` — audit results

A CEO prospect sees "FAILURES.md" in the file listing. That sends
the wrong signal. Options: move to a `process/` or `.internal/`
directory, move to a separate branch, or remove from main.

**IMPORTANT: License contradiction.**
README says "Not yet determined." A `LICENSE` file with MIT terms
exists. Pick one truth and align them.

#### UX (workbook experience)

**The workbook structure is well-designed for its audience.**
- Tab 1 leads with the punchline (21.3% all-in vs. 17.3% planned)
- KPI row is immediately visible with benchmark comparison
- Responsibility matrix tells the CEO who owns each waste bucket
- Navigation hyperlinks between tabs
- Yellow-highlighted interactive input cells with data validation
- Excel Tables throughout (pivot-ready)
- Data bars for visual waterfall
- Trend analysis (H1 vs H2 waste trajectory)

**No UX issues found at the code level.** The remaining UX question
is whether this actually renders correctly in Excel — which requires
human visual QA (the audit claims it passes, but this should be
re-verified before prospect delivery).

#### Code Quality

**Generally clean.** The simplification pass addressed the worst
issues. Remaining:

- `database_url` is passed as a parameter to `generate_workbook()`
  and each `build_*()` function, but `connect()` in `db.py` reads
  from `os.environ["DATABASE_URL"]` directly. The parameter is
  misleading — it's never used. Either wire it through or remove it.

- Dead file: `scripts/build_db.py` is the SQLite-era build script.
  No code references it. Safe to delete.

- `bisect` is imported inside a function body in
  `tab_promo_efficacy.py` (PEP 8 violation, minor).

- `openpyxl` not pinned in `requirements.txt`. Should be
  `openpyxl>=3.1.5,<4.0` to prevent breaking changes.

#### Architecture

**Sound for its purpose.** One module per tab, shared styles/taxonomy/
channel-mapping modules, thin DB wrapper, separate build and validate
entry points. No over-engineering. The `deduction_taxonomy.py` and
`channel_mapping.py` modules are clean single-source-of-truth patterns.

No architectural issues found.

#### Tests

**Functional coverage is good (62 output checks). Unit coverage is
zero.** The validation suite checks the generated workbook against
expected values, which is the right test for this project. Unit tests
on individual tab modules would be nice but low leverage — the output
validation catches regressions.

The validation suite requires a running Postgres instance, so it
can't run in CI without infrastructure. Acceptable for a portfolio
piece.

#### Performance

**No issues.** Small dataset (trailing-365, ~3K deductions, ~600K scan
rows). Workbook generates in seconds. Multiple DB queries per tab is
fine at this scale.

#### Security

**No vulnerabilities found.**
- `.env` is gitignored
- `.env.example` has generic templates, no real credentials
- No hardcoded secrets (fixed during remediation)
- Database URL read from environment variable
- No user input handling (static generation)
- MIT license is appropriate

One note: the Fly.io Postgres instance is referenced in `.env.example`
comments. If the prospect can see `<fly-app>.flycast:5432`, that's
the Fly.io internal address — not externally routable, so not a
security issue, but it reveals infrastructure details.

#### DevEx

**CRITICAL: No artifact to hand over.**
`output/` is gitignored. The prospect can't download the .xlsx from
GitHub. Building requires `DATABASE_URL` pointing at a Postgres
instance with the Cinderhaven schema. A CEO won't do that. The
single highest-leverage fix is to either:
(a) Check in a pre-built .xlsx (or host it somewhere downloadable)
(b) Add a GitHub Release with the .xlsx as an asset
(c) Email it directly

**MINOR: Repo cleanup needed.**
- `.claude-project-url` contains "PASTE-YOUR-PROJECT-ID-HERE"
- 9 stale worktree branches (local only, not prospect-visible)

### Summary

The project's analytical depth, prose quality, and code structure
are strong. The workbook is well-designed for a CEO audience. The
two blockers for prospect delivery are both documentation/delivery
issues, not code issues:

1. **There's no way for a prospect to get the .xlsx** — it requires
   a Postgres instance to build, and the README's Quick Start is
   broken (references a removed submodule).

2. **The repo exposes internal process files** that would confuse
   or distract a prospect browsing GitHub.

Everything else is minor cleanup. The analytical content — the
workbook structure, the executive memo, the defensibility log — is
prospect-ready today.

---

## Phase 3: Landscape Scan
**Date:** 2026-05-16
**Category:** Trade spend diagnostic for mid-market CPG ($15M–$50M
revenue). Scanned: commercial TPM software, consulting firms, and
open-source/portfolio examples.

### Competitors / Similar Projects

| # | Name | Type | Description | Traction / Price |
|---|------|------|-------------|-----------------|
| 1 | UpClear BluePlanner | Software | Mid-market TPM: gross-to-net revenue mgmt, deduction mgmt, forecasting. 3–6 month implementation. | Clients: Beyond Meat, Vita Coco, Lundberg. Quote-only. |
| 2 | Vividly | Software | Two-tier TPM (Growth/Scale): promo ROI, forecasting, Customer P&L. 35+ retailer connectors. 3-month avg implementation. | G2 4.9/5. Claims 90% deduction-processing reduction. |
| 3 | TrewUp | Software | "Trade spend visibility layer" — connects deductions to promotions to show actuals. Not a planner. | 40+ CPG brands (Hain Celestial, Kikkoman). $60K recovery case study. |
| 4 | SupplyPike | Software | Retailer deduction management (Walmart, Kroger, Amazon). Pure recovery, no strategic analytics. | $810/mo starting. $1B+ deductions recovered (cumulative). |
| 5 | CPGvision (PSignite) | Software | Six-tier TPM on Salesforce. ~30% cost of enterprise TPM. 3–4 month implementation. | Clients: Hershey, Abbott. v5 launched Sep 2024. |
| 6 | Promomash / CPGenius | Software | Modular TPM + deduction mgmt with AI + human-in-the-loop. | Hundreds of CPG brands since 2015. Gartner listed. |
| 7 | L.E.K. Consulting | Consulting | Strategy firm with named Trade Spend Optimization practice. 3-phase: Diagnostic → Strategy → Enablement. | $350–$500+/hr blended. Enterprise clients. |
| 8 | Clarkston Consulting | Consulting | CPG-focused consultancy. Trade promotion practice, TPM selection, deduction diagnostics. | "Found hundreds of thousands in unauthorized deductions." |
| 9 | (Open source) | Portfolio | **Nothing exists.** Zero CPG trade-spend repos on GitHub. No diagnostic workbooks on Kaggle. | 43% of CPG brands still use spreadsheets (Tellius 2026). |

### Feature Matrix

| Feature | This Project | Mid-Market TPM (UpClear/Vividly) | SupplyPike | Consulting (L.E.K.) | Open Source |
|---------|:-----------:|:------:|:------:|:------:|:------:|
| All-in trade rate calculation | ✅ | ✅ | ❌ | ✅ | ❌ |
| Deduction taxonomy / classification | ✅ | ✅ | 🟡 | ✅ | ❌ |
| Promo ROI analysis | ✅ | ✅ | ❌ | ✅ | ❌ |
| Retailer / channel P&L | ✅ | ✅ | ❌ | ✅ | ❌ |
| Defensibility log (per-claim rebuttal) | ✅ | ❌ | 🟡 | 🟡 | ❌ |
| External benchmark comparison | ✅ | ❌ | ❌ | ✅ | ❌ |
| Interactive what-if inputs | ✅ | ✅ | ❌ | ❌ | ❌ |
| Waste trend (within-window) | ✅ | ✅ | ❌ | 🟡 | ❌ |
| Ongoing monitoring / live feeds | ❌ | ✅ | ✅ | ❌ | ❌ |
| Retailer portal connectivity | ❌ | ✅ | ✅ | ❌ | ❌ |
| Automated dispute filing | ❌ | 🟡 | ✅ | ❌ | ❌ |
| Collaborative planning / forecasting | ❌ | ✅ | ❌ | 🟡 | ❌ |
| Standalone artifact (no software) | ✅ | ❌ | ❌ | ✅ | ❌ |
| CEO-readable in <2 minutes | ✅ | ❌ | ❌ | 🟡 | ❌ |
| Zero procurement / no subscription | ✅ | ❌ | ❌ | ❌ | ❌ |
| Upfront cost to prospect | $0 (wedge) | $10K–$50K+/yr | $810+/mo | $50K–$150K+ | $0 |
| Time to first insight | Immediate | 3–6 months | 1–2 months | 4–8 weeks | N/A |

### Landscape Position

#### Table Stakes (standard in category)
- Trade rate calculation — ✅ have it
- Deduction classification — ✅ have it
- Retailer-level breakdowns — ✅ have it
- Promo ROI — ✅ have it

No table-stakes gaps.

#### Where This Project Is Stronger

1. **Zero friction to first insight.** Every competitor requires
   either a 3–6 month software implementation or a $50K+ consulting
   engagement before the CEO sees anything. This project delivers
   the punchline immediately — no procurement, no onboarding, no
   subscription decision.

2. **Defensibility log.** No software vendor provides per-claim
   rebuttal text. Consulting firms deliver verbal defensibility in
   meetings but rarely in a durable, handoff-ready document. The
   "VP of Sales rebuttal" artifact is genuinely differentiated.

3. **External benchmark grounding.** Most TPM software shows
   internal trends without a category yardstick. The 19–23%
   benchmark band gives the CEO context no tool provides out of
   the box.

4. **CEO-readable format.** TPM dashboards require training.
   This workbook's Tab 1 is designed for a phone-at-Starbucks
   scan. The executive memo is a one-pager.

#### Where This Project Is Weaker

1. **No ongoing monitoring.** This is a point-in-time snapshot.
   Competitors like Vividly and TrewUp show live actuals, trends,
   alerts. After the diagnostic lands, the CEO's next question is
   "now what do I do every month?" — and the answer today is
   "hire me for a real engagement."

2. **No retailer connectivity.** The data is simulated. Real
   delivery requires connecting to actual retailer portals
   (Walmart Retail Link, UNFI Connect, KeHE Connect, etc.).
   This is explicitly out of scope but the prospect will ask.

3. **No dispute workflow.** SupplyPike and Promomash automate
   the filing of disputes. This project identifies what to
   dispute but doesn't file anything.

4. **No collaborative planning.** TPM tools let Sales and Finance
   co-plan promotions. This project only looks backward.

#### Unique Differentiators

1. **The "before the subscription" wedge.** No other tool occupies
   this position — problem discovery that doesn't require committing
   to a platform. The diagnostic answers "do I even have a problem?"
   before the CEO has to decide whether to buy UpClear or hire L.E.K.

2. **Defensibility-per-claim documentation.** The combination of
   deduction taxonomy + written rebuttal for each bucket doesn't
   exist in any product or public artifact found in this scan.

3. **Open-source category is empty.** Zero public trade-spend
   diagnostic workbooks exist on GitHub or Kaggle. The portfolio
   differentiation is absolute — there is nothing to compare
   against in the public domain.

#### Category Trends

- **Consolidation:** TELUS acquired Exceedra + Blacksmith.
  Instacart acquired Eversight. SPS Commerce backs SupplyPike.
  The mid-market is being squeezed by enterprise roll-ups.
- **AI positioning:** Every vendor now claims AI (Promomash's
  "DeductionGenius," Vividly's predictive analytics). Most is
  classification/matching, not generative.
- **Visibility over planning:** Newer entrants (TrewUp, Vividly)
  emphasize "see what actually happened" over "plan what should
  happen" — same philosophy as this diagnostic.
- **43% still on spreadsheets:** The mid-market hasn't adopted
  TPM software. They live in Excel. A diagnostic delivered as an
  Excel workbook meets them where they are.

### Summary

This project occupies a white-space position: the "pre-subscription
diagnostic" for mid-market CPG CEOs who don't yet know if they have
a trade spend problem worth solving. Commercial TPM tools require
3–6 months and $10K+/yr before delivering insight. Consulting firms
charge $50K+ for the same analysis. Open-source alternatives don't
exist.

The weaknesses (no live monitoring, no retailer connectivity, no
dispute automation) are features of the ongoing tools that come
*after* the diagnostic — they're the engagement upsell, not gaps
in the wedge. The positioning is: "see the problem for free, then
decide whether to invest in fixing it."

---

## Phase 4: Differentiation & Next Moves
**Date:** 2026-05-16

### Cross-Reference Summary

The project's core competitive advantage — instant insight with zero
procurement — is currently **disabled** by a delivery failure. The
.xlsx isn't downloadable, and the README's Quick Start is broken. In
a category where time-to-first-insight is the primary differentiator
(3–6 months for software, 4–8 weeks for consulting, vs. "immediate"
for this project), having no delivery mechanism is not a minor gap.
It's the single thing that makes the competitive position theoretical
rather than actual.

The internal process files (FAILURES.md, REMEDIATION.md, references
to "Claude Chat" and "Gemini scope review") directly undermine the
second differentiator: CEO readability. The prospect's first
impression of the repo should be "this person understands my problem"
— not "this person is documenting their AI workflow." The landscape
scan confirmed there is zero public competition; the GitHub landing
page does all the selling. Anything that confuses or distracts is a
conversion leak in a funnel with no backup.

The code-level issues (unused parameter, dead scripts, unpinned deps)
have no competitive relevance. A prospect will never read the Python.
These are internal hygiene — worth doing but not before the prospect
can actually receive the deliverable.

### Ranked Next Moves

| # | Move | Category | Strategic | Internal | Effort | Score | Description |
|---|------|----------|-----------|----------|--------|-------|-------------|
| 1 | Ship the .xlsx | Leapfrog | 5 | 5 | 1 | 10.0 | Generate workbook, attach to GitHub Release. Activates the core differentiator. |
| 2 | README as prospect landing page | Double down | 5 | 4 | 1 | 9.0 | Remove "build it yourself" instructions. Lead with downloadable .xlsx link, exec memo, defensibility log. Fix license line, remove submodule refs. |
| 3 | Clean public face | Foundational | 4 | 3 | 1 | 7.0 | Move process files (PLAN, HANDOFF, DECISIONS, FAILURES, REVIEW_*, REMEDIATION, PROJECT_PLAN, AUDIT) to `.process/` or remove from main. |
| 4 | Visual QA in Excel | Close gap | 3 | 4 | 1 | 7.0 | Open .xlsx in Excel, verify every tab renders correctly. Screenshot evidence. Fix anything broken. |
| 5 | Define the delivery package | Double down | 4 | 2 | 2 | 3.0 | Decide exactly what the prospect gets: repo link? Email with .xlsx attached? Notion page? Loom walkthrough video? |
| 6 | Code cleanup (dead files, params) | Foundational | 0 | 3 | 1 | 3.0 | Delete scripts/build_db.py, remove unused database_url parameter, pin openpyxl, fix .claude-project-url. |
| 7 | Prospect-specific customization guide | Double down | 3 | 1 | 3 | 1.3 | Document how to swap Cinderhaven data for a real client's data. Makes the "engagement upsell" concrete. |

### Recommended Sequence

**Do today (30 minutes total):**
1. **Visual QA** — open the workbook in Excel. If anything's broken,
   fix it before shipping. (5 min)
2. **Ship the .xlsx** — run `build_workbook.py`, create a GitHub
   Release with the .xlsx attached. (5 min)
3. **README rewrite** — remove submodule/build instructions, add
   download link to the Release, fix license line. Make it a
   prospect landing page. (15 min)
4. **Clean public face** — move process files to `.process/` dir
   so the root file listing is: README, EXECUTIVE_MEMO, DEFENSIBILITY,
   walkthrough, LICENSE, build_workbook.py, workbook/, dev/. (5 min)

**Do before sending to prospect:**
5. **Define delivery package** — decide whether you send a repo link,
   email the .xlsx, or something else. Depends on the prospect
   relationship.

**Do later (nice-to-have, not blocking):**
6. Code cleanup
7. Customization guide

### What NOT to Do

- **Don't add live monitoring or dashboards.** That's chasing
  Vividly/TrewUp into their strength (connected data feeds, SaaS
  infrastructure). The wedge's power is that it requires nothing.
  Ongoing monitoring is the engagement you're selling, not the sample.

- **Don't build retailer connectivity.** The prospect will ask
  "can this connect to my actual data?" The answer is "yes, that's
  the engagement" — not "let me build an integration."

- **Don't add a web UI.** 43% of mid-market CPG runs trade on
  spreadsheets. Excel IS the UI. A web app adds procurement friction
  and loses the "meets you where you are" positioning.

- **Don't write unit tests.** The 62-check validation suite is
  sufficient. The prospect will never run your test suite. This is
  internal hygiene that doesn't move the needle on prospect
  conversion.

- **Don't fix code-level issues before delivery issues.** The
  unused `database_url` parameter is invisible to prospects. Fixing
  it before shipping the .xlsx is polishing the engine while the
  car has no wheels.

- **Don't over-explain the AI/automation story.** The PROJECT_PLAN
  references "Claude Chat," "Gemini scope review," and AI-assisted
  development. These are interesting process notes but they undermine
  the positioning with a prospect. The prospect should think "this
  person understands trade spend" — not "this person is good at
  prompting AI."

### Audit Complete

**What this audit found:**
- The analytical content is strong and genuinely differentiated
- The competitive position (pre-subscription diagnostic wedge) is
  unoccupied — zero public alternatives exist
- The project can't be delivered to a prospect because the .xlsx
  isn't accessible and the README is broken
- All blockers are delivery/presentation issues, fixable in 30
  minutes

**First step:** Run `/decompose` on moves 1–4 (the "do today"
batch), or just do them — they're simple enough to execute without
a plan.
