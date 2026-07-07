-- ============================================
-- matched_promo_deductions.sql
-- ============================================
-- Question: Which promo_billback deductions match a planned
--           promotion, and what was the actual cost?
-- Tables:   promotions, deductions
-- Output:   promo_id, sku, retailer, actual_cost
-- Params:   None
-- Notes:    Matches deductions to promotions by retailer name
--           (normalized) and date window (14 days before promo
--           start through 90 days after promo end). If actual
--           cost differs from planned cost, the promotion
--           over- or under-delivered on its budget.
-- ============================================

SELECT
    p.promo_id,
    p.sku,
    p.retailer,
    SUM(d.amount) AS actual_cost
FROM promotions p
JOIN deductions d
    ON LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
   AND d.deduction_type = 'promo_billback'
   AND d.deduction_date BETWEEN date(p.start_week, '-14 days')
                              AND date(p.end_week, '+90 days')
GROUP BY p.promo_id, p.sku, p.retailer
ORDER BY actual_cost DESC;
