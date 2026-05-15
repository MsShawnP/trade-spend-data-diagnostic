-- ============================================
-- all_promotions.sql
-- ============================================
-- Question: What promotions are in the calendar?
-- Tables:   promotions
-- Output:   promo_id, sku, retailer, start_week, end_week,
--           duration_weeks, discount_depth_pct, promo_type,
--           promo_cost, funding_mechanism
-- Params:   None
-- Notes:    188 rows across 75 distinct promo_ids. Not all
--           promotions have matching POS data in scan_data.
--           The promotions table may be incomplete — ghost
--           promo analysis (ghost_promos.sql) identifies
--           deductions referencing promotions not listed here.
-- ============================================

SELECT
    promo_id,
    sku,
    retailer,
    start_week,
    end_week,
    duration_weeks,
    discount_depth_pct,
    promo_type,
    promo_cost,
    funding_mechanism
FROM promotions
ORDER BY promo_id, retailer;
