-- ============================================
-- ghost_promos.sql
-- ============================================
-- Question: Which promo_billback deductions have no matching
--           promotion in the calendar?
-- Tables:   deductions, promotions
-- Output:   deduction_id, retailer_id, amount, deduction_date
-- Params:   None
-- Notes:    "Ghost promos" are deductions that reference
--           promotional activity not found in the promotions
--           table. This suggests either an incomplete promo
--           calendar or unauthorized promotional spend.
--           137 events, $95,826 total.
-- ============================================

SELECT
    d.deduction_id,
    d.retailer_id,
    d.amount,
    d.deduction_date
FROM deductions d
WHERE d.deduction_type = 'promo_billback'
  AND NOT EXISTS (
      SELECT 1 FROM promotions p
      WHERE LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
        AND d.deduction_date BETWEEN date(p.start_week, '-14 days')
                                  AND date(p.end_week, '+90 days')
  )
ORDER BY d.amount DESC;
