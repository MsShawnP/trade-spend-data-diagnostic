-- ============================================
-- total_revenue.sql
-- ============================================
-- Question: What is the total wholesale revenue for the trailing
--           52 weeks?
-- Tables:   scan_data
-- Output:   total_revenue (dollars)
-- Params:   :oldest_week — the 52nd-most-recent distinct
--           week_ending from trailing_52_weeks.sql
-- Notes:    Locked number: $25,593,052. Use the oldest week_ending
--           from trailing_52_weeks.sql as the parameter.
-- ============================================

SELECT SUM(dollars_sold) AS total_revenue
FROM scan_data
WHERE week_ending >= :oldest_week;
-- To run in sqlite3 CLI:
--   Replace :oldest_week with the value from trailing_52_weeks.sql,
--   e.g. WHERE week_ending >= '2025-05-10'
