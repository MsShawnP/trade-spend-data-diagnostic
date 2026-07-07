-- ============================================
-- promo_performance.sql
-- ============================================
-- Question: What is the ROI of each promotion based on
--           pre/during volume comparison?
-- Tables:   promotions, scan_data, stores, deductions
-- Output:   promo_id, sku, retailer, promo_type, start_week,
--           end_week, planned_cost, actual_cost, baseline_avg,
--           during_avg, incremental_volume, asp, incremental_revenue,
--           roi, cost_source
-- Params:   :window — number of weeks for pre-period baseline
--           (default 4, range 1–8)
-- Notes:    Gap query — the workbook builds this from Python
--           list operations + Excel OFFSET formulas. This SQL
--           version computes ROI in a single query. Limitations:
--           does not adjust for seasonality, does not model
--           pantry-loading, not a causal model. Uses a fixed
--           pre-period window; the workbook makes this
--           adjustable via an input cell.
-- ============================================

WITH promo_weeks AS (
    SELECT DISTINCT week_ending
    FROM scan_data
    ORDER BY week_ending
),
weekly_vol AS (
    SELECT
        sd.sku,
        s.retailer,
        sd.week_ending,
        SUM(sd.units_sold)   AS units,
        SUM(sd.dollars_sold) AS dollars
    FROM scan_data sd
    JOIN stores s ON sd.store_id = s.store_id
    GROUP BY sd.sku, s.retailer, sd.week_ending
),
asp AS (
    SELECT
        sd.sku,
        s.retailer,
        AVG(sd.dollars_sold * 1.0 / sd.units_sold) AS avg_price
    FROM scan_data sd
    JOIN stores s ON sd.store_id = s.store_id
    WHERE sd.units_sold > 0
    GROUP BY sd.sku, s.retailer
),
actual_costs AS (
    SELECT
        p.promo_id, p.sku, p.retailer,
        SUM(d.amount) AS actual_cost
    FROM promotions p
    JOIN deductions d
        ON LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
       AND d.deduction_type = 'promo_billback'
       AND d.deduction_date BETWEEN date(p.start_week, '-14 days')
                                  AND date(p.end_week, '+90 days')
    GROUP BY p.promo_id, p.sku, p.retailer
),
baseline AS (
    -- Average weekly volume in the N weeks before promo start
    -- :window controls how many pre-weeks (default 4)
    SELECT
        p.promo_id, p.sku, p.retailer,
        AVG(wv.units) AS baseline_avg
    FROM promotions p
    JOIN weekly_vol wv ON wv.sku = p.sku
        AND wv.retailer = p.retailer
        AND wv.week_ending < p.start_week
        AND wv.week_ending >= date(p.start_week, '-' || (:window * 7) || ' days')
    GROUP BY p.promo_id, p.sku, p.retailer
),
during_period AS (
    SELECT
        p.promo_id, p.sku, p.retailer,
        AVG(wv.units) AS during_avg
    FROM promotions p
    JOIN weekly_vol wv ON wv.sku = p.sku
        AND wv.retailer = p.retailer
        AND wv.week_ending >= p.start_week
        AND wv.week_ending <= p.end_week
    GROUP BY p.promo_id, p.sku, p.retailer
)
SELECT
    p.promo_id,
    p.sku,
    p.retailer,
    p.promo_type,
    p.start_week,
    p.end_week,
    p.promo_cost                                AS planned_cost,
    ac.actual_cost,
    ROUND(b.baseline_avg, 1)                    AS baseline_avg,
    ROUND(dp.during_avg, 1)                     AS during_avg,
    ROUND((dp.during_avg - b.baseline_avg) * p.duration_weeks, 1) AS incremental_volume,
    ROUND(a.avg_price, 2)                       AS asp,
    ROUND((dp.during_avg - b.baseline_avg) * p.duration_weeks * a.avg_price, 2) AS incremental_revenue,
    ROUND(
        (dp.during_avg - b.baseline_avg) * p.duration_weeks * a.avg_price
        / COALESCE(ac.actual_cost, p.promo_cost),
    2) AS roi,
    CASE WHEN ac.actual_cost IS NOT NULL THEN 'actual' ELSE 'planned' END AS cost_source
FROM promotions p
LEFT JOIN baseline b       ON b.promo_id = p.promo_id AND b.sku = p.sku AND b.retailer = p.retailer
LEFT JOIN during_period dp ON dp.promo_id = p.promo_id AND dp.sku = p.sku AND dp.retailer = p.retailer
LEFT JOIN asp a            ON a.sku = p.sku AND a.retailer = p.retailer
LEFT JOIN actual_costs ac  ON ac.promo_id = p.promo_id AND ac.sku = p.sku AND ac.retailer = p.retailer
WHERE b.baseline_avg IS NOT NULL
  AND dp.during_avg IS NOT NULL
ORDER BY roi DESC;
-- To change the pre-period window, replace :window with an
-- integer 1–8 (e.g., 4 for a 4-week baseline).
