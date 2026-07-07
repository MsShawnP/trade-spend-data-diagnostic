-- ============================================
-- waste_by_category.sql
-- ============================================
-- Question: How does operational waste break down by deduction
--           type, and how long do disputes take to resolve?
-- Tables:   deductions, disputes
-- Output:   deduction_type, deduction_count, total_amount,
--           pct_of_waste, avg_days_to_resolve
-- Params:   :max_scan — most recent week_ending (defines the
--           trailing-365-day window end)
-- Notes:    Feeds Tab 2 (Leak Diagnostic). Excludes
--           promo_billback deductions. Category total should
--           sum to ~$1,967,416 (within DB rebuild tolerance).
-- ============================================

SELECT
    d.deduction_type,
    COUNT(*)       AS deduction_count,
    SUM(d.amount)  AS total_amount,
    ROUND(SUM(d.amount) * 100.0 / (
        SELECT SUM(amount) FROM deductions
        WHERE deduction_date > date(:max_scan, '-365 days')
          AND deduction_date <= :max_scan
          AND deduction_type != 'promo_billback'
    ), 1) AS pct_of_waste,
    ROUND(AVG(
        CASE WHEN dis.closed_date IS NOT NULL
             THEN julianday(dis.closed_date) - julianday(d.deduction_date)
        END
    )) AS avg_days_to_resolve
FROM deductions d
LEFT JOIN disputes dis ON dis.deduction_id = d.deduction_id
WHERE d.deduction_date > date(:max_scan, '-365 days')
  AND d.deduction_date <= :max_scan
  AND d.deduction_type != 'promo_billback'
GROUP BY d.deduction_type
ORDER BY total_amount DESC;
