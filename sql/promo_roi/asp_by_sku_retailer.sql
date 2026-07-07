-- ============================================
-- asp_by_sku_retailer.sql
-- ============================================
-- Question: What is the average selling price for each SKU at
--           each retailer?
-- Tables:   scan_data, stores
-- Output:   sku, retailer, avg_selling_price
-- Params:   None
-- Notes:    ASP = dollars_sold / units_sold, averaged across
--           all weeks with positive unit sales. Used in promo
--           ROI calculation to convert incremental volume to
--           incremental revenue.
-- ============================================

SELECT
    sd.sku,
    s.retailer,
    AVG(sd.dollars_sold * 1.0 / sd.units_sold) AS avg_selling_price
FROM scan_data sd
JOIN stores s ON sd.store_id = s.store_id
WHERE sd.units_sold > 0
GROUP BY sd.sku, s.retailer
ORDER BY sd.sku, s.retailer;
