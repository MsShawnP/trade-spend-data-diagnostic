-- ============================================
-- deduction_codes.sql
-- ============================================
-- Question: What do the retailer-specific deduction codes mean,
--           and which have been verified vs. inferred?
-- Tables:   deduction_codes
-- Output:   retailer_id, code, name, deduction_type, status
-- Params:   None
-- Notes:    97 entries. 19 verified from vendor guides, 78
--           inferred via pattern matching. Used by the Deduction
--           Ledger to translate raw remittance codes to
--           plain-English descriptions.
-- ============================================

SELECT
    retailer_id,
    code,
    name,
    deduction_type,
    CASE WHEN is_published = 1 THEN 'Verified' ELSE 'Inferred' END AS status
FROM deduction_codes
ORDER BY retailer_id, deduction_type, code;
