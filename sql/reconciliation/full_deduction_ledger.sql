-- ============================================
-- full_deduction_ledger.sql
-- ============================================
-- Question: What is the full deduction detail for the trailing
--           365 days, with code translations and dispute status?
-- Tables:   deductions, deduction_codes, disputes
-- Output:   20 columns — deduction_id, deduction_date,
--           retailer_id, code_as_remitted, translated_code,
--           deduction_type, amount, order_id, shipment_id,
--           remittance_id, remittance_description, dispute_outcome,
--           recovered_amount, filed_date, closed_date,
--           days_outstanding, dispute_deadline, is_vague,
--           is_post_audit, is_double_dip
-- Params:   :max_scan — most recent week_ending
-- Notes:    The most complex query — 3-way LEFT JOIN across
--           deductions, deduction_codes, and disputes. Feeds
--           Tab 5 (Deduction Ledger). ~2,374 rows. 292
--           deductions have no matching crosswalk entry
--           (show as 'Unmapped').
-- ============================================

SELECT
    d.deduction_id,
    d.deduction_date,
    d.retailer_id,
    d.code_as_remitted,
    COALESCE(dc.name, 'Unmapped')     AS translated_code,
    d.deduction_type,
    d.amount,
    d.order_id,
    d.shipment_id,
    d.remittance_id,
    d.remittance_description,
    dis.outcome                       AS dispute_outcome,
    dis.recovered_amount,
    dis.filed_date,
    dis.closed_date,
    CASE
        WHEN dis.closed_date IS NOT NULL
        THEN CAST(julianday(dis.closed_date) - julianday(d.deduction_date) AS INTEGER)
        WHEN dis.filed_date IS NOT NULL
        THEN CAST(julianday(:max_scan) - julianday(d.deduction_date) AS INTEGER)
        ELSE NULL
    END                               AS days_outstanding,
    d.dispute_deadline,
    d.is_vague,
    d.is_post_audit,
    d.is_double_dip
FROM deductions d
LEFT JOIN deduction_codes dc ON d.code_id = dc.code_id
LEFT JOIN disputes dis ON dis.deduction_id = d.deduction_id
WHERE d.deduction_date > date(:max_scan, '-365 days')
  AND d.deduction_date <= :max_scan
ORDER BY d.deduction_date DESC, d.amount DESC;
