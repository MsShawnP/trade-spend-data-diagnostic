-- ============================================
-- promo_billback_by_retailer.sql
-- ============================================
-- Question: How much does each retailer bill back for
--           promotional activity?
-- Tables:   deductions
-- Output:   retailer_id, total_amount
-- Params:   :max_scan — most recent week_ending
-- Notes:    Feeds Tab 4 (Retailer Risk). These are planned
--           promotional deductions — excluded from operational
--           waste but included in the all-in trade cost.
--           Total across all retailers: ~$51,479 (trailing-365).
-- ============================================

SELECT
    retailer_id,
    SUM(amount) AS total_amount
FROM deductions
WHERE deduction_date > date(:max_scan, '-365 days')
  AND deduction_date <= :max_scan
  AND deduction_type = 'promo_billback'
GROUP BY retailer_id
ORDER BY total_amount DESC;
