# Trade Spend Data Diagnostic — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Write the narrative walkthrough that ties the diagnostic deliverables
together. This is the portfolio piece — the document a prospect reads
to understand what a trade spend diagnostic looks like, what it finds,
and what a real engagement would add.

## Why this arc, why now

Four arcs of technical work are done: data, workbook, SQL library,
dashboard. The deliverables exist but nothing explains them as a
coherent story. The walkthrough is the front door — it frames the
problem, walks through the methodology and findings, and positions
the deliverables as evidence. Without it, the portfolio is a pile
of files.

## Business question this arc answers

What does a trade spend diagnostic actually reveal, and why should
a CPG company in the $15M–$30M revenue band care?

## Tasks

- [x] Define the walkthrough structure in a brief outline — sections
      follow the diagnostic narrative arc from problem to engagement
- [x] Write `walkthrough.md` — full narrative, Economist style (sober,
      declarative, data-forward), with specific Cinderhaven numbers
- [x] Write project-level `README.md` — positioning, repo structure,
      quick start, links to all deliverables

## Out of scope for this arc

- Video walkthrough or slide deck
- Client-facing proposal template
- Additional data generation or workbook changes
- Power BI visual assembly (documented in BUILD_GUIDE.md, done manually)

## Definition of done for this arc

- [x] `walkthrough.md` covers problem, methodology, findings,
      deliverables, and real-engagement upsell — with specific numbers
- [x] Voice is consistent: declarative, data-forward, no marketing
      language ("unlocking value", "driving insights", "leveraging")
- [x] Project-level `README.md` orients a cold reader to the repo
- [x] All numbers in the walkthrough match verified actuals from the
      data foundation

---

## Arc history

### Arc 5: Written walkthrough (completed 2026-05-10)
- **Goal:** Write the narrative walkthrough and project README that
  tie the deliverables together as a portfolio piece
- **Outcome:** 2,276-word walkthrough covering problem, methodology,
  findings, deliverables, and real-engagement upsell — Economist
  voice, every paragraph data-forward with specific Cinderhaven
  numbers. Project README (76 lines) orients a cold visitor in
  under 60 seconds. All numbers verified against DB actuals.
- **Key decisions:** None — this arc was execution against the voice
  and structure decisions already in DECISIONS.md.

### Arc 4: Power BI dashboard preparation (completed 2026-05-10)
- **Goal:** Prepare everything needed to assemble the Power BI dashboard
  — data exports, DAX measures, build guide, automation tooling
- **Outcome:** 4-page dashboard fully specified. 7 CSV data exports
  (star schema: 3 dimensions, 4 facts, 601K scan rows). 49 DAX measures
  documented with formulas and cross-references. `generate_pbix_model.py`
  automates measure injection via pbi-tools (extract → inject JSON →
  compile). BUILD_GUIDE.md covers automated data model setup and manual
  visual assembly. 6 specific Power BI value-adds over Excel documented.
  All export numbers validated against locked actuals.
- **Key decisions:** pbi-tools for measure automation, visual layout
  stays manual (report page JSON is undocumented/brittle). Channel-average
  trade rate methodology (AVG across SKUs per channel, not per-SKU rates).

### Arc 3: SQL diagnostic query library (completed 2026-05-10)
- **Goal:** Extract and document standalone SQL queries from the
  workbook build scripts
- **Outcome:** 25 .sql files across 6 categories (trade_rate,
  deductions, promo_roi, retailer, crosswalk, reconciliation). 17
  extracted from workbook scripts, 6 new gap queries written, 2
  duplicates consolidated, 3 cleaned up. All execute without error.
  36/36 verification checks pass. sql/README.md provides query index,
  10-step analyst walkthrough, and locked numbers reference.
- **Key decisions:** None — this arc was execution, not architecture.

### Arc 2: Workbook build (completed 2026-05-10)
- **Goal:** Build the 7-tab diagnostic Excel workbook
- **Outcome:** All 7 tabs built (Executive Pulse, Leak Diagnostic,
  Promo Efficacy, Retailer Risk, Deduction Ledger, Deduction Code
  Crosswalk, Methodology & Logic). Shared styles module, 8 named
  ranges, print areas, data validation, conditional formatting.
  validate_workbook.py passes 43 checks. Findings surfaced during
  build: 137 ghost promo deductions ($95,826), 292 unmapped codes,
  11-retailer P&L. Minor DB rebuild nondeterminism: ±$1,500 on waste
  rate, ±1 on dispute count — handled by validation tolerances.
- **Key decisions:** rapidfuzz over fuzzywuzzy, separate validation
  script pattern.

### Arc 1: Data generation (completed 2026-05-09)
- **Goal:** Generate unified Cinderhaven trade spend dataset
- **Outcome:** cinderhaven-data repo updated with 21 tables, deduction
  lifecycle merged from retailer-deduction-recovery project, promo_cost
  and funding_mechanism fields added, double-dips seeded, date windows
  aligned. Three downstream repos updated via submodule. Verified
  numbers locked in TRADE_SPEND_VERIFICATION.md.
- **Key decisions:** Two-bucket framing (structural trade + operational
  waste), original brief numbers superseded by verified actuals,
  cinderhaven-data is single source of truth via submodule.
