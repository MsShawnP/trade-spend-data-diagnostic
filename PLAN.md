# Trade Spend Data Diagnostic — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Build the 7-tab Excel workbook that a CEO can open cold, see the
trade spend headline on tab 1, and drill into deduction detail,
promo ROI, and double-dip detection across the remaining tabs.

## Why this arc, why now

The unified dataset is complete (cinderhaven-data, 21 tables, verified
numbers). The workbook is the centerpiece deliverable — everything
else (dashboard, SQL queries, walkthrough) builds on top of it. A
working workbook also serves as the fastest way to validate that the
data tells a coherent story end-to-end.

## Business question this arc answers

For a $25M specialty food brand spending 17.3% of revenue on planned
trade and losing an additional 4.0% to operational deductions: where
exactly is the money going, which promotions created value, and what's
the addressable improvement?

## Locked numbers (from TRADE_SPEND_VERIFICATION.md)

| Metric                              | Value              |
|--------------------------------------|--------------------|
| Annual wholesale revenue             | $25,593,052        |
| Structural trade (sku_costs)         | $4,435,052 (17.3%) |
| Operational/compliance (trail-365)   | $1,010,940 (4.0%)  |
| Promo_billback deductions            | $211,513           |
| All-in trade cost                    | $5,445,992 (21.3%) |
| Double-dips                          | 3 / $19,306        |
| Disputes filed                       | 1,409              |
| Total recovered                      | $98,216 (14.3%)    |

## Tasks

Work in vertical slices. Each task produces a working tab (or group
of related tabs) that can be reviewed before moving to the next.

- [x] Set up project structure — submodule, build script, workbook
      generation entry point
- [x] Design tab list, ordering, and color-coding scheme — 7 tabs
      confirmed (down from original 13)
- [x] Build Tab 1: Executive Pulse (green) — two-bucket framing,
      waterfall chart, KPI trio, addressable improvement headline,
      responsibility matrix (waste → department), dynamic action
      items, hyperlinked navigation, instructional callout
- [x] Build Tab 2: Leak Diagnostic (green) — operational waste by
      category, double-dip alert with cell comments explaining
      mechanism, adjustable target recovery rate input cell,
      recoverability score
- [x] Build Tab 3: Promo Efficacy (green) — top/bottom performers
      by lift vs. cost, adjustable pre/post window (default 4wk),
      data quality indicator per promo, ghost promo flags, honest
      coverage disclosure
- [x] Build Tab 4: Retailer Risk (green) — revenue share vs.
      deduction share, net-net effective margin by retailer (gross
      margin → structural trade → operational waste → effective),
      what-if trade rate input cells per retailer
- [x] Build Tab 5: Deduction Ledger (blue) — trailing-365 deductions
      (2,365 rows), translated codes from crosswalk, auto-filters,
      freeze panes, consistent join keys
- [ ] Build Tab 6: Deduction Code Crosswalk (gray) — retailer codes
      mapped to plain English and standardized categories, verified
      vs. inferred flags
- [ ] Build Tab 7: Methodology & Logic (gray) — two-bucket
      definitions, data lineage, ROI methodology, net-net margin
      methodology, build date timestamp, SQL logic summary
- [ ] Workbook-level features — named ranges for KPIs, conditional
      formatting, no gridlines on green/gray tabs, print areas,
      data validation on input cells, yellow fill on adjustable
      cells with cell comments
- [ ] Validate end-to-end — numbers on Tab 1 match locked numbers,
      interactive cells recalculate correctly, vlookup across tabs
      returns clean results, all auto-filters work

## Out of scope for this arc

- Power BI dashboard (next arc — consumes workbook structure)
- SQL diagnostic query library (future arc)
- Written walkthrough / README beyond the in-workbook README tab
  (future arc)
- Fuzzy matching algorithm as a standalone deliverable (matching
  logic is embedded in the workbook's plan-vs-actual tab)
- VP Sales calendar quirks overlay on the promotions data (this is
  a cinderhaven-data change if needed, not a workbook task)

## Definition of done for this arc

- [ ] 7-tab .xlsx workbook generates from the unified cinderhaven-data
      database via submodule
- [ ] Executive Pulse tab tells the two-bucket story with locked
      numbers, waterfall chart, and addressable improvement headline
- [ ] Tabs are color-coded green/blue/gray
- [ ] Promo ROI calculations work with adjustable pre/post window
- [ ] Double-dip detection surfaces the 3 flagged events with
      explanatory cell comments
- [ ] Net-net effective margin by retailer calculated and displayed
- [ ] Interactive input cells (recovery rate, promo window, what-if
      trade rates) recalculate dependent values
- [ ] Deduction code crosswalk translates retailer codes to plain
      English
- [ ] A non-technical user can open the workbook cold and understand
      the structure without external documentation
- [ ] All numbers trace back to TRADE_SPEND_VERIFICATION.md actuals
- [ ] No raw scan data in the workbook — all aggregated
- [ ] Join keys consistent across all tabs (no vlookup #N/A errors)

---

## Arc history

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
