# Trade Spend Data Diagnostic — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Build a documented SQL diagnostic query library that a controller or
analyst can run against the cinderhaven-data SQLite database to
investigate trade spend, deduction patterns, and promo performance.

## Why this arc, why now

The workbook build scripts already contain most of the query logic —
this arc extracts, cleans, and documents them as standalone .sql files.
The formalized queries also feed directly into the Power BI data model
(next arc), avoiding duplicate work in DAX.

## Business question this arc answers

Same core question, different interface: where is the money going,
which promotions created value, and what's the addressable improvement —
answered via composable SQL that an analyst can modify and extend.

## Tasks

- [x] Inventory the queries already embedded in the workbook build
      scripts — list each, note what tab it feeds, and whether it's
      reusable as-is or needs cleanup
- [x] Extract and clean queries into standalone .sql files, one per
      diagnostic question, in a `sql/` directory
- [x] Organize files by category: trade_rate, deductions, promo_roi,
      retailer, crosswalk, reconciliation
- [x] Add a header comment block to each .sql file: what it answers,
      which tables it touches, expected output columns, any parameters
      (date range, retailer filter) as placeholder variables
- [ ] Write a `sql/README.md` documenting the full query library —
      one-line description per file, suggested execution order for a
      new analyst, and how to run against the SQLite database
- [ ] Verify every query runs clean against the current database and
      produces results consistent with the workbook's locked numbers

## Out of scope for this arc

- Power BI dashboard (next arc — consumes these queries)
- Written walkthrough (future arc)
- Query optimization or indexing (dataset is small)
- Stored procedures or views (SQLite doesn't support stored procs;
  views are optional and only if they simplify downstream consumption)

## Definition of done for this arc

- [ ] `sql/` directory contains standalone .sql files covering all
      key diagnostics from the workbook
- [ ] Each file has a header comment block documenting purpose, tables,
      output columns, and parameters
- [ ] `sql/README.md` documents the library with descriptions and
      execution guidance
- [ ] All queries execute without error against the current database
- [ ] Key query outputs match workbook locked numbers (within DB
      rebuild tolerances)

---

## Arc history

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
