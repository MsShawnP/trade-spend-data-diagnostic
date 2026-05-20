---
title: Circular hardcoded metric calculation always returns constant value
date: 2026-05-15
category: logic-errors
module: trade-spend-diagnostic
problem_type: logic_error
component: service_object
severity: critical
symptoms:
  - "Recovery rate metric always displays 14.3% regardless of underlying data"
  - "Metric appears data-driven but value never changes across different datasets"
  - "Back-calculated denominator cancels out numerator, producing algebraic identity"
root_cause: logic_error
resolution_type: code_fix
tags:
  - circular-calculation
  - hardcoded-metric
  - data-integrity
  - openpyxl
  - python
---

# Circular hardcoded metric calculation always returns constant value

## Problem

A trade spend diagnostic workbook's recovery rate metric was hardcoded to always return 14.3% regardless of underlying data, due to a circular formula that algebraically canceled out the data variables: `x / (x / 0.143)` simplifies to `0.143` for any nonzero `x`.

## Symptoms

- The Executive Pulse tab always displayed a recovery rate of exactly 14.3%, never changing even when underlying deduction or dispute data changed.
- The methodology tab cited a wrong denominator ($687,210 instead of the actual $716,082), suggesting the number was not dynamically derived.
- Three prose documents (walkthrough, memo, defensibility log) all cited "14.3%" as a data-derived finding, reinforcing the false value through repetition.
- The value was plausible (actual rate was 13.7%), so it passed casual inspection without raising suspicion.

## What Didn't Work

The bug was not caught during the original build or initial code review because:

1. **Plausible output masking**: The hardcoded 14.3% was close enough to the actual 13.7% that no one questioned it. A wildly wrong value (e.g., 95%) would have been caught immediately.
2. **Formula complexity as camouflage**: The expression `metrics["total_recovered"] / (metrics["total_recovered"] / 0.143)` looks like a real computation involving data. It references a live variable twice, creating the appearance of data dependency.
3. **No input variation testing**: Nobody changed the input data and checked whether the output changed. The metric was treated as "working" because it produced a reasonable number.
4. **Prose propagation**: Once 14.3% appeared in the code output, it was copy-pasted into three separate prose documents, making it look more authoritative with each repetition.

## Solution

**Before** (`workbook/tab_executive_pulse.py`, line 173):

```python
# BAD: circular -- always produces 0.143
recovery_rate = metrics["total_recovered"] / (metrics["total_recovered"] / 0.143) if metrics["total_recovered"] else 0
```

Algebraically: `a / (a / b)` = `a * b / a` = `b`. The data cancels out entirely.

**After**:

```python
# Query actual denominator from database
total_disputed = conn.execute("""
    SELECT SUM(d.amount) FROM deductions d
    JOIN disputes dis ON dis.deduction_id = d.deduction_id
""").fetchone()[0] or 0

# Direct computation from data -- no constants
recovery_rate = metrics["total_recovered"] / metrics["total_disputed"] if metrics["total_disputed"] else 0
```

Additionally, all three prose documents were updated to reflect the correct 13.7% recovery rate derived from actual data.

## Why This Works

The root cause was a prototyping artifact: a developer calculated the recovery rate manually during early development (getting approximately 14.3%), then wrote a formula that appeared to use live data but algebraically reduced to that constant. The denominator was reverse-engineered from the desired output rather than queried from the data source.

The fix works because it replaces the circular self-referencing formula with a direct computation: recovered dollars divided by disputed dollars. The denominator now comes from an actual database query (`SUM(d.amount)` for all deductions that have associated disputes) rather than being derived from the numerator and a constant. The metric now responds to data changes.

## Prevention

1. **Algebraic reduction check**: Any formula of the form `a / (a / b)` is circular and always returns `b`. During code review, simplify metric formulas algebraically. If the data variables cancel out, the formula is hardcoded regardless of how many variables it references.

2. **Independent validation path**: Calculate the same metric via a completely separate code path (e.g., a direct SQL query: `SELECT SUM(recovered_amount) / SUM(disputed_amount)`) and compare results. This is how the data review agent caught the bug -- by independently querying the database and comparing against the workbook output.

3. **Input perturbation test**: Change the underlying data and verify the output changes proportionally. If modifying the input to a "calculated" metric produces no change in the output, the metric is not actually calculated from data. This is the simplest and most reliable check.

4. **Flag magic numbers in formulas**: Any literal numeric constant inside a metric calculation formula (like `0.143`) is a code smell. Calculated metrics should derive entirely from data, not from embedded constants.

5. **Trace denominators to source**: When a metric involves division, verify the denominator is queried from data, not derived from the numerator. The circular pattern here was specifically that the denominator was constructed by dividing the numerator by a constant.

## Related Issues

- `REVIEW_CODE.md` finding B2: Original detection of circular recovery rate
- `REVIEW_DATA.md` finding D2: Data impact analysis (14.3% vs actual 13.7%)
- `REMEDIATION.md` item 1: Resolution record (consolidated fix across code + 4 prose documents)
