# Trade Spend Data Diagnostic — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Build a Power BI dashboard (.pbix) that adds interactive value beyond
the Excel workbook — drill-through, cross-filtering, trend lines,
and dynamic slicing that Excel can't do well.

## Why this arc, why now

The workbook is the static diagnostic. The dashboard is the interactive
companion — same data, different affordances. The SQL query library
(Arc 3) provides clean source queries for the data model, so the
Power BI data layer doesn't start from scratch. Building the dashboard
now, while the workbook is fresh, makes it easy to identify where
Power BI should diverge rather than replicate.

## Business question this arc answers

Same core question, interactive interface: where is the money going,
which promotions created value, and what's the addressable improvement —
with the ability to filter by retailer, time period, category, and
promo type dynamically.

## Tasks

- [ ] Design the dashboard page structure — which pages, what each
      shows, and how it differs from the corresponding workbook tab
      (the DECISIONS.md rule: "Power BI must add value beyond Excel")
- [ ] Build the Power BI data model — import tables from SQLite,
      define relationships, create calculated columns and measures
      using the SQL query library as reference
- [ ] Build Page 1: Executive overview — KPI cards, waterfall visual,
      trade rate trend line (if time-series data supports it),
      cross-filtering by retailer
- [ ] Build Page 2: Deduction deep-dive — category breakdown with
      drill-through to individual deductions, time-based filtering,
      retailer slicer
- [ ] Build Page 3: Promo performance — scatter plot (cost vs. lift),
      ROI distribution, drill-through to promo detail, ghost promo
      callout
- [ ] Build Page 4: Retailer comparison — net-net margin comparison,
      revenue vs. deduction share, what-if parameter for trade rate
      scenarios
- [ ] Add bookmarks or navigation for guided walkthrough
- [ ] Export .pbix file and document any DAX measures in a
      `powerbi/README.md`

## Out of scope for this arc

- Written walkthrough (next arc)
- Power BI Service deployment or refresh schedules
- Row-level security
- Custom visuals beyond built-in and standard marketplace visuals

## Definition of done for this arc

- [ ] .pbix file opens and connects to the cinderhaven-data SQLite
      database (or exported CSV/parquet if SQLite connector is
      problematic)
- [ ] Dashboard has 4 pages with interactive filtering and
      drill-through
- [ ] KPI figures match workbook locked numbers
- [ ] At least 3 clear examples of "Power BI adds value here that
      Excel can't" (documented in README)
- [ ] No replicated Excel charts — every visual justifies its
      existence in the interactive medium
- [ ] `powerbi/README.md` documents the data model, key DAX measures,
      and the value-add rationale

---

## Arc history

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
