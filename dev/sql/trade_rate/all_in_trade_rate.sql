-- ============================================
-- all_in_trade_rate.sql
-- ============================================
-- Question: What is the all-in trade rate (structural +
--           operational waste) as a percentage of revenue?
-- Tables:   scan_data, stores, sku_costs, deductions
-- Output:   total_revenue, structural_trade, operational_waste,
--           all_in_trade, structural_rate, waste_rate, all_in_rate
-- Params:   :oldest_week — 52nd-most-recent distinct week_ending
--           :max_scan — most recent week_ending (for deduction
--           trailing-365 window)
-- Notes:    Gap query — was Python arithmetic combining three
--           separate query results. Locked numbers: revenue
--           $25,593,052, structural $4,435,052 (17.3%), waste
--           $1,010,940 (4.0%), all-in 21.3%.
-- ============================================

WITH revenue AS (
    SELECT SUM(dollars_sold) AS total
    FROM scan_data
    WHERE week_ending >= :oldest_week
),
channel_revenue AS (
    SELECT s.retailer,
           SUM(sd.dollars_sold) AS rev
    FROM scan_data sd
    JOIN stores s ON sd.store_id = s.store_id
    WHERE sd.week_ending >= :oldest_week
    GROUP BY s.retailer
),
channel_rates AS (
    SELECT
        AVG(trade_spend_pct_walmart)     AS rate_walmart,
        AVG(trade_spend_pct_costco)      AS rate_costco,
        AVG(trade_spend_pct_whole_foods) AS rate_whole_foods,
        AVG(trade_spend_pct_unfi)        AS rate_unfi,
        AVG(trade_spend_pct_dtc)         AS rate_dtc,
        AVG(trade_spend_pct_regional)    AS rate_regional
    FROM sku_costs
),
structural AS (
    SELECT SUM(
        cr.rev * CASE cr.retailer
            WHEN 'Walmart'     THEN rates.rate_walmart
            WHEN 'Costco'      THEN rates.rate_costco
            WHEN 'Whole Foods' THEN rates.rate_whole_foods
            WHEN 'UNFI'        THEN rates.rate_unfi
            WHEN 'DTC'         THEN rates.rate_dtc
            ELSE rates.rate_regional
        END
    ) AS total
    FROM channel_revenue cr
    CROSS JOIN channel_rates rates
),
waste AS (
    SELECT SUM(amount) AS total
    FROM deductions
    WHERE deduction_date > date(:max_scan, '-365 days')
      AND deduction_date <= :max_scan
      AND deduction_type != 'promo_billback'
)
SELECT
    r.total                               AS total_revenue,
    s.total                               AS structural_trade,
    w.total                               AS operational_waste,
    s.total + w.total                      AS all_in_trade,
    ROUND(s.total * 100.0 / r.total, 1)   AS structural_rate_pct,
    ROUND(w.total * 100.0 / r.total, 1)   AS waste_rate_pct,
    ROUND((s.total + w.total) * 100.0 / r.total, 1) AS all_in_rate_pct
FROM revenue r, structural s, waste w;
