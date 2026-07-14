-- ============================================
-- double_dip_events.sql
-- ============================================
-- Question: Which deductions represent double-payments where
--           a promotion was discounted twice?
-- Tables:   deductions
-- Output:   deduction_id, retailer_id, amount, deduction_date,
--           deduction_type
-- Params:   None
-- Notes:    Feeds Tab 2 (Leak Diagnostic). Double-dip means the
--           retailer collected both an off-invoice discount and a
--           promo_billback deduction for the same promotion.
--           Locked number: 0 events in the regenerated DB.
-- ============================================

SELECT
    deduction_id,
    retailer_id,
    amount,
    deduction_date,
    deduction_type
FROM deductions
WHERE is_double_dip = 1
ORDER BY amount DESC;
