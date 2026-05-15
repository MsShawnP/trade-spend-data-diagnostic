-- ============================================
-- gross_margin_by_channel.sql
-- ============================================
-- Question: What is the average gross margin for each sales
--           channel based on COGS and wholesale pricing?
-- Tables:   sku_costs
-- Output:   channel, avg_cogs, avg_wholesale, gross_margin_pct
-- Params:   None
-- Notes:    Cleaned from workbook code that ran 6 separate
--           queries via Python f-string interpolation. This
--           single query returns all channels. Gross margin =
--           (wholesale - COGS) / wholesale.
-- ============================================

SELECT
    'Walmart' AS channel,
    AVG(cogs_per_unit) AS avg_cogs,
    AVG(wholesale_walmart) AS avg_wholesale,
    ROUND((AVG(wholesale_walmart) - AVG(cogs_per_unit)) * 100.0
          / AVG(wholesale_walmart), 1) AS gross_margin_pct
FROM sku_costs
UNION ALL
SELECT 'Costco',
    AVG(cogs_per_unit), AVG(wholesale_costco),
    ROUND((AVG(wholesale_costco) - AVG(cogs_per_unit)) * 100.0
          / AVG(wholesale_costco), 1)
FROM sku_costs
UNION ALL
SELECT 'Whole Foods',
    AVG(cogs_per_unit), AVG(wholesale_whole_foods),
    ROUND((AVG(wholesale_whole_foods) - AVG(cogs_per_unit)) * 100.0
          / AVG(wholesale_whole_foods), 1)
FROM sku_costs
UNION ALL
SELECT 'UNFI',
    AVG(cogs_per_unit), AVG(wholesale_unfi),
    ROUND((AVG(wholesale_unfi) - AVG(cogs_per_unit)) * 100.0
          / AVG(wholesale_unfi), 1)
FROM sku_costs
UNION ALL
SELECT 'DTC',
    AVG(cogs_per_unit), AVG(wholesale_dtc),
    ROUND((AVG(wholesale_dtc) - AVG(cogs_per_unit)) * 100.0
          / AVG(wholesale_dtc), 1)
FROM sku_costs
UNION ALL
SELECT 'Regional',
    AVG(cogs_per_unit), AVG(wholesale_regional),
    ROUND((AVG(wholesale_regional) - AVG(cogs_per_unit)) * 100.0
          / AVG(wholesale_regional), 1)
FROM sku_costs;
