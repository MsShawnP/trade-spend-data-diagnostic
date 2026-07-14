-- ============================================
-- recovery_rate.sql
-- ============================================
-- Question: What percentage of disputed dollars has been
--           successfully recovered?
-- Tables:   deductions, disputes
-- Output:   total_disputed_dollars, total_recovered,
--           recovery_rate_pct, won_count, partial_count,
--           lost_count, pending_count
-- Params:   None
-- Notes:    Computes recovery rate from data: recovered / disputed
--           dollars. Current DB yields 41.9% (5,247 disputes,
--           $160,161 recovered from $382,579 disputed). DB outcome
--           values are 'won', 'partial', 'lost', 'pending'
--           (1,411 / 1,478 / 1,509 / 849).
-- ============================================

SELECT
    SUM(d.amount)                                  AS total_disputed_dollars,
    SUM(dis.recovered_amount)                      AS total_recovered,
    ROUND(SUM(dis.recovered_amount) * 100.0
          / SUM(d.amount), 1)                      AS recovery_rate_pct,
    SUM(CASE WHEN dis.outcome = 'won'     THEN 1 ELSE 0 END) AS won_count,
    SUM(CASE WHEN dis.outcome = 'partial' THEN 1 ELSE 0 END) AS partial_count,
    SUM(CASE WHEN dis.outcome = 'lost'        THEN 1 ELSE 0 END) AS lost_count,
    SUM(CASE WHEN dis.outcome = 'pending'     THEN 1 ELSE 0 END) AS pending_count
FROM disputes dis
JOIN deductions d ON d.deduction_id = dis.deduction_id;
