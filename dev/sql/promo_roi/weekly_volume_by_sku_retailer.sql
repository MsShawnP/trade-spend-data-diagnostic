-- ============================================
-- weekly_volume_by_sku_retailer.sql
-- ============================================
-- Question: What is the weekly unit volume for each SKU at
--           each retailer?
-- Tables:   scan_data, stores
-- Output:   sku, retailer, week_ending, units
-- Params:   :sku_filter (optional) — filter to a specific SKU
--           :retailer_filter (optional) — filter to a specific
--           retailer
-- Notes:    Large result set (157 weeks x 50 SKUs x 11
--           retailers). Use the optional filters to scope down
--           for practical analysis. Feeds the promo ROI
--           pre/during/post volume comparison.
-- ============================================

SELECT
    sd.sku,
    s.retailer,
    sd.week_ending,
    SUM(sd.units_sold) AS units
FROM scan_data sd
JOIN stores s ON sd.store_id = s.store_id
-- Optional filters: uncomment and fill in to narrow results
-- WHERE sd.sku = :sku_filter
-- AND s.retailer = :retailer_filter
GROUP BY sd.sku, s.retailer, sd.week_ending
ORDER BY sd.sku, s.retailer, sd.week_ending;
