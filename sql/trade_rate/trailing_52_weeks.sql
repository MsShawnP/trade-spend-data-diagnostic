-- ============================================
-- trailing_52_weeks.sql
-- ============================================
-- Question: What are the 52 most recent weekly scan periods?
-- Tables:   scan_data
-- Output:   week_ending (date) — 52 rows, newest first
-- Params:   None
-- Notes:    Foundation query. Many other queries use the oldest
--           and newest values from this result to define the
--           trailing-52-week revenue window and trailing-365-day
--           deduction window. Run this first.
-- ============================================

SELECT DISTINCT week_ending
FROM scan_data
ORDER BY week_ending DESC
LIMIT 52;
