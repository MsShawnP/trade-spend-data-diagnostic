-- ============================================
-- addressable_improvement.sql
-- ============================================
-- Question: How much additional money could be recovered at a
--           given target recovery rate?
-- Tables:   deductions, disputes
-- Output:   operational_waste, current_recovered,
--           current_rate_pct, target_rate_pct,
--           recovery_at_target, incremental_opportunity
-- Params:   :max_scan — most recent week_ending
--           :target_rate — target recovery rate as decimal
--           (e.g., 0.30 for 30%)
-- Notes:    Gap query — the workbook uses an adjustable input
--           cell for target rate and Excel formulas for the
--           calculation. This SQL version takes the target as
--           a parameter. Assumes all operational waste is
--           potentially disputable. In practice, some categories
--           (slotting, label fines) have low recoverability.
-- ============================================

WITH waste AS (
    SELECT SUM(amount) AS total
    FROM deductions
    WHERE deduction_date > date(:max_scan, '-365 days')
      AND deduction_date <= :max_scan
      AND deduction_type != 'promo_billback'
),
recovery AS (
    SELECT SUM(recovered_amount) AS total
    FROM disputes
)
SELECT
    w.total                                     AS operational_waste,
    r.total                                     AS current_recovered,
    ROUND(r.total * 100.0 / w.total, 1)         AS current_rate_pct,
    ROUND(:target_rate * 100, 1)                 AS target_rate_pct,
    ROUND(w.total * :target_rate, 0)             AS recovery_at_target,
    ROUND(w.total * :target_rate - r.total, 0)   AS incremental_opportunity
FROM waste w, recovery r;
-- Example: for a 30% target rate, replace :target_rate with 0.30
