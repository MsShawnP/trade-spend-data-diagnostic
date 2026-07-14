-- ============================================
-- ghost_promo_summary.sql
-- ============================================
-- Question: How many ghost promo deductions exist and what is
--           their total dollar impact?
-- Tables:   deductions, promotions
-- Output:   ghost_count, ghost_total_dollars
-- Params:   None
-- Notes:    Aggregate companion to ghost_promos.sql.
--           Locked number: 1,550 events, $145,082.
-- ============================================

SELECT
    COUNT(*)    AS ghost_count,
    SUM(d.amount) AS ghost_total_dollars
FROM deductions d
WHERE d.deduction_type = 'promo_billback'
  AND NOT EXISTS (
      SELECT 1 FROM promotions p
      WHERE LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
        AND d.deduction_date BETWEEN date(p.start_week, '-14 days')
                                  AND date(p.end_week, '+90 days')
  );
