-- ============================================
-- waste_by_type_summary.sql
-- ============================================
-- Question: What is the total operational waste by deduction
--           type (without dispute join)?
-- Tables:   deductions
-- Output:   deduction_type, deduction_count, total_amount
-- Params:   :max_scan — most recent week_ending
-- Notes:    Simpler version of waste_by_category.sql without
--           the dispute resolution timeline. Feeds Tab 1
--           (Executive Pulse) responsibility matrix.
-- ============================================

SELECT
    deduction_type,
    COUNT(*)      AS deduction_count,
    SUM(amount)   AS total_amount
FROM deductions
WHERE deduction_date > date(:max_scan, '-365 days')
  AND deduction_date <= :max_scan
  AND deduction_type != 'promo_billback'
GROUP BY deduction_type
ORDER BY total_amount DESC;
