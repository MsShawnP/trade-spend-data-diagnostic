-- ============================================
-- recovery_rate.sql
-- ============================================
-- Question: What percentage of disputed dollars has been
--           successfully recovered?
-- Tables:   deductions, disputes
-- Output:   total_disputed_dollars, total_recovered,
--           recovery_rate_pct, won_full_count, won_partial_count,
--           lost_count, pending_count
-- Params:   None
-- Notes:    Computes recovery rate from data: recovered / disputed
--           dollars. Current DB yields 19.8% (6,105 disputes,
--           $987,798 recovered from $4,989,889 disputed).
-- ============================================

SELECT
    SUM(d.amount)                                  AS total_disputed_dollars,
    SUM(dis.recovered_amount)                      AS total_recovered,
    ROUND(SUM(dis.recovered_amount) * 100.0
          / SUM(d.amount), 1)                      AS recovery_rate_pct,
    SUM(CASE WHEN dis.outcome = 'won_full'    THEN 1 ELSE 0 END) AS won_full_count,
    SUM(CASE WHEN dis.outcome = 'won_partial' THEN 1 ELSE 0 END) AS won_partial_count,
    SUM(CASE WHEN dis.outcome = 'lost'        THEN 1 ELSE 0 END) AS lost_count,
    SUM(CASE WHEN dis.outcome = 'pending'     THEN 1 ELSE 0 END) AS pending_count
FROM disputes dis
JOIN deductions d ON d.deduction_id = dis.deduction_id;
