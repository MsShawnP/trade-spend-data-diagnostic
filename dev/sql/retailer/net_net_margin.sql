-- ============================================
-- net_net_margin.sql
-- ============================================
-- Question: What is each retailer's net-net effective margin
--           after all trade costs?
-- Tables:   scan_data, stores, sku_costs, deductions
-- Output:   retailer, revenue, gross_margin_pct, structural_rate,
--           after_structural_pct, op_ded_rate, pb_ded_rate,
--           net_net_margin_pct
-- Params:   :oldest_week — 52nd-most-recent distinct week_ending
--           :max_scan — most recent week_ending
-- Notes:    Gap query — the workbook computed this in Python by
--           combining 4 separate queries. Margin waterfall:
--           gross margin -> minus structural trade rate -> minus
--           (op deductions + promo billback) / revenue = net-net.
--           Excludes KeHE (no revenue). Excludes freight,
--           warehousing, and non-trade SG&A.
-- ============================================

WITH channel_revenue AS (
    SELECT s.retailer,
           SUM(sd.dollars_sold) AS revenue
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
gross_margins AS (
    SELECT 'Walmart' AS channel,
        (AVG(wholesale_walmart) - AVG(cogs_per_unit)) / AVG(wholesale_walmart) AS gm
    FROM sku_costs
    UNION ALL SELECT 'Costco',
        (AVG(wholesale_costco) - AVG(cogs_per_unit)) / AVG(wholesale_costco) FROM sku_costs
    UNION ALL SELECT 'Whole Foods',
        (AVG(wholesale_whole_foods) - AVG(cogs_per_unit)) / AVG(wholesale_whole_foods) FROM sku_costs
    UNION ALL SELECT 'UNFI',
        (AVG(wholesale_unfi) - AVG(cogs_per_unit)) / AVG(wholesale_unfi) FROM sku_costs
    UNION ALL SELECT 'DTC',
        (AVG(wholesale_dtc) - AVG(cogs_per_unit)) / AVG(wholesale_dtc) FROM sku_costs
    UNION ALL SELECT 'Regional',
        (AVG(wholesale_regional) - AVG(cogs_per_unit)) / AVG(wholesale_regional) FROM sku_costs
),
op_deductions AS (
    SELECT retailer_id, SUM(amount) AS total
    FROM deductions
    WHERE deduction_date > date(:max_scan, '-365 days')
      AND deduction_date <= :max_scan
      AND deduction_type != 'promo_billback'
    GROUP BY retailer_id
),
pb_deductions AS (
    SELECT retailer_id, SUM(amount) AS total
    FROM deductions
    WHERE deduction_date > date(:max_scan, '-365 days')
      AND deduction_date <= :max_scan
      AND deduction_type = 'promo_billback'
    GROUP BY retailer_id
)
SELECT
    cr.retailer,
    cr.revenue,
    ROUND(gm.gm * 100, 1) AS gross_margin_pct,
    ROUND(CASE cr.retailer
        WHEN 'Walmart'     THEN rates.rate_walmart
        WHEN 'Costco'      THEN rates.rate_costco
        WHEN 'Whole Foods' THEN rates.rate_whole_foods
        WHEN 'UNFI'        THEN rates.rate_unfi
        WHEN 'DTC'         THEN rates.rate_dtc
        ELSE rates.rate_regional
    END * 100, 1) AS structural_rate_pct,
    ROUND((gm.gm - CASE cr.retailer
        WHEN 'Walmart'     THEN rates.rate_walmart
        WHEN 'Costco'      THEN rates.rate_costco
        WHEN 'Whole Foods' THEN rates.rate_whole_foods
        WHEN 'UNFI'        THEN rates.rate_unfi
        WHEN 'DTC'         THEN rates.rate_dtc
        ELSE rates.rate_regional
    END) * 100, 1) AS after_structural_pct,
    ROUND(COALESCE(od.total, 0) * 100.0 / cr.revenue, 1) AS op_ded_rate_pct,
    ROUND(COALESCE(pb.total, 0) * 100.0 / cr.revenue, 1) AS pb_ded_rate_pct,
    ROUND((gm.gm
        - CASE cr.retailer
            WHEN 'Walmart'     THEN rates.rate_walmart
            WHEN 'Costco'      THEN rates.rate_costco
            WHEN 'Whole Foods' THEN rates.rate_whole_foods
            WHEN 'UNFI'        THEN rates.rate_unfi
            WHEN 'DTC'         THEN rates.rate_dtc
            ELSE rates.rate_regional
          END
        - COALESCE(od.total, 0) / cr.revenue
        - COALESCE(pb.total, 0) / cr.revenue
    ) * 100, 1) AS net_net_margin_pct
FROM channel_revenue cr
CROSS JOIN channel_rates rates
LEFT JOIN gross_margins gm
    ON gm.channel = CASE
        WHEN cr.retailer IN ('Walmart','Costco','Whole Foods','UNFI','DTC')
        THEN cr.retailer ELSE 'Regional' END
LEFT JOIN op_deductions od
    ON od.retailer_id = LOWER(REPLACE(cr.retailer, ' ', '_'))
LEFT JOIN pb_deductions pb
    ON pb.retailer_id = LOWER(REPLACE(cr.retailer, ' ', '_'))
ORDER BY cr.revenue DESC;
