-- ============================================
-- channel_trade_rates.sql
-- ============================================
-- Question: What is the average structural trade rate for each
--           sales channel?
-- Tables:   sku_costs
-- Output:   One row with avg trade rate per channel (7 columns)
-- Params:   None
-- Notes:    Cleaned from workbook code that ran 6 separate queries
--           via Python f-string interpolation. This single query
--           returns all channels at once. Rates are the negotiated
--           rate-card discounts embedded in wholesale pricing.
-- ============================================

SELECT
    AVG(trade_spend_pct_walmart)     AS rate_walmart,
    AVG(trade_spend_pct_costco)      AS rate_costco,
    AVG(trade_spend_pct_whole_foods) AS rate_whole_foods,
    AVG(trade_spend_pct_unfi)        AS rate_unfi,
    AVG(trade_spend_pct_dtc)         AS rate_dtc,
    AVG(trade_spend_pct_kehe)        AS rate_kehe,
    AVG(trade_spend_pct_regional)    AS rate_regional
FROM sku_costs;
