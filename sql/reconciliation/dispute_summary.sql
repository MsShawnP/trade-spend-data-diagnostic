-- ============================================
-- dispute_summary.sql
-- ============================================
-- Question: How many disputes have been filed and how much has
--           been recovered?
-- Tables:   disputes
-- Output:   dispute_count, total_recovered
-- Params:   None
-- Notes:    Locked numbers: 6,105 disputes (±10 for DB rebuild
--           variance), $987,798 recovered.
-- ============================================

SELECT
    COUNT(*)              AS dispute_count,
    SUM(recovered_amount) AS total_recovered
FROM disputes;
