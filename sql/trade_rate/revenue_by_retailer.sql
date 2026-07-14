-- ============================================
-- revenue_by_retailer.sql
-- ============================================
-- Question: How is trailing-52-week revenue distributed across
--           retailers/channels?
-- Tables:   scan_data, stores
-- Output:   retailer (text), channel_revenue (dollars)
-- Params:   :oldest_week — the 52nd-most-recent distinct
--           week_ending from trailing_52_weeks.sql
-- Notes:    Feeds Tab 1 (Executive Pulse) and Tab 4 (Retailer
--           Risk). Retailers map to channels via stores table.
--           Revenue should sum to $32,472,742 (within tolerance).
-- ============================================

SELECT s.retailer,
       SUM(sd.dollars_sold) AS channel_revenue
FROM scan_data sd
JOIN stores s ON sd.store_id = s.store_id
WHERE sd.week_ending >= :oldest_week
GROUP BY s.retailer
ORDER BY channel_revenue DESC;
