-- ============================================
-- operational_deductions_by_retailer.sql
-- ============================================
-- Question: How much operational waste does each retailer
--           generate in deductions?
-- Tables:   deductions
-- Output:   retailer_id, total_amount
-- Params:   :max_scan — most recent week_ending
-- Notes:    Feeds Tab 4 (Retailer Risk). Excludes promo_billback.
--           KeHE now has scan revenue (~$2.6M) and its own
--           trade_spend_pct_kehe rate column.
-- ============================================

SELECT
    retailer_id,
    SUM(amount) AS total_amount
FROM deductions
WHERE deduction_date > date(:max_scan, '-365 days')
  AND deduction_date <= :max_scan
  AND deduction_type != 'promo_billback'
GROUP BY retailer_id
ORDER BY total_amount DESC;
