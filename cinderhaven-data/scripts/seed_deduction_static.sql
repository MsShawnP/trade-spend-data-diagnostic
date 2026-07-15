-- Static seed data for retailer-deduction-recovery.
-- Loads retailers, retailer_rules, deduction_codes, edi_requirements.
-- Run after seed_deduction_schema.sql.
--
-- Retailer set: Walmart, Costco, Whole Foods, UNFI, KeHE (nationals/
-- distributors) plus three regional chains — Kroger, Sprouts,
-- Regional Group. Research in research/retailers/ is the source for
-- archetype behaviors.
--
-- Recovery rates and inferred values are calibration choices for
-- synthetic data; flagged in `notes` where unverified.

-- ---------- retailers ----------
INSERT INTO retailers (retailer_id, name, channel_type, dispute_portal_name, dispute_portal_url, dispute_method, notes) VALUES
  ('walmart',             'Walmart',                 'retailer',    'Retail Link / APDP / HighRadius',  'https://retaillink.wal-mart.com/',     'portal',       'Multiple systems by deduction type — APDP for AP shortages/allowances, HighRadius for AR/OTIF'),
  ('costco',              'Costco',                  'retailer',    'Costco Vendor Portal',             'https://fssts.costco.com/',            'portal',       'Lower-tech than Walmart; depot cross-dock model'),
  ('whole_foods',         'Whole Foods',             'retailer',    'VIP / Smartsheet',                 'https://vip.wholefoods.com',           'email_excel',  'Pay-by-PO program gates dispute access; regional fragmentation'),
  ('unfi',                'UNFI',                    'distributor', 'Email + Excel template (Natural)', NULL,                                   'email_excel',  'Natural side: Deductions@unfi.com — .xlsb only, PDFs/screenshots rejected'),
  ('kehe',                'KeHE',                    'distributor', 'K-Solve in KeHE CONNECT Supplier', 'https://connectsupplier.kehe.com/',    'portal',       '180-day cap (newly strict); 48-hour UDR response window. Not in base stores; orders generated against natural-foods-compatible SKU set'),
  ('kroger',              'Kroger',                  'retailer',    'Buyer email + AP',                 NULL,                                   'email_buyer',  'Kroger: specialty/local-supplier friendly, buyer-relationship dispute path, no published windows'),
  ('sprouts',             'Sprouts',                 'retailer',    'AP email',                         NULL,                                   'email_buyer',  'Sprouts: natural/reset-driven; many deductions arrive via UNFI/KeHE statements'),
  ('regional_group',      'Regional Group',          'retailer',    'AP email',                         NULL,                                   'email_buyer',  'Generic regional; inferred norms'),
  ('dtc',                 'DTC',                     'dtc',         NULL,                               NULL,                                   NULL,           'Direct-to-consumer; no deduction model');

-- ---------- retailer_rules ----------
-- 9 deduction_types per retailer (DTC excluded). dispute_window_days NULL where not published.
-- typical_recovery_rate is a per-retailer baseline for the simulation; actual
-- per-deduction outcome depends on evidence quality and timeliness.
-- Spoilage flows through the same failure pipeline as the other operational
-- types. Slotting is a negotiated cost (new-item fees, planogram changes,
-- shelf placement allowances) and is intentionally non-disputable —
-- typical_recovery_rate=0, no evidence_required, dispute_window NULL.

INSERT INTO retailer_rules (retailer_id, deduction_type, dispute_window_days, auto_deduct, evidence_required, typical_recovery_rate, notes) VALUES
  -- Walmart
  ('walmart', 'short_ship',     365,  1, 'signed_bol,pod,pack_log',          0.45, 'Verified — APDP 12-month window for codes 21–28'),
  ('walmart', 'label_fine',     NULL, 1, 'label_scan,pack_log',              0.20, 'SQEP fines; window not separately published'),
  ('walmart', 'pallet_fine',    NULL, 1, 'photo,pack_log',                   0.20, 'SQEP Phase 3; $200 admin + $4/pallet'),
  ('walmart', 'damaged',        365,  1, 'signed_bol,photo',                 0.55, 'Code 28; same APDP window as shortage'),
  ('walmart', 'late_delivery',  NULL, 1, 'pod,asn_confirmation',             0.30, 'OTIF; 3% of COGS; HighRadius dispute window not verified'),
  ('walmart', 'promo_billback', 730,  0, 'promo_agreement',                  0.50, 'Allowance — 24-month APDP window'),
  ('walmart', 'vague',          NULL, 1, 'pack_log',                         0.10, 'Code 87 catch-all'),
  -- Costco
  ('costco',  'short_ship',     NULL, 1, 'signed_bol,pack_log',              0.40, 'Windows not published; inferred industry norm'),
  ('costco',  'label_fine',     NULL, 1, 'label_scan',                       0.20, 'GS1-128/SSCC; not published'),
  ('costco',  'pallet_fine',    NULL, 1, 'photo',                            0.20, 'Lean/overhang/underhang; not published'),
  ('costco',  'damaged',        NULL, 1, 'signed_bol,photo',                 0.50, 'Inferred'),
  ('costco',  'late_delivery',  NULL, 1, 'pod',                              0.25, '30-min grace at depot then refusal'),
  ('costco',  'promo_billback', NULL, 0, 'promo_agreement',                  0.40, 'Inferred'),
  ('costco',  'vague',          NULL, 1, 'pack_log',                         0.10, 'Inferred'),
  -- Whole Foods (WFM-only scope)
  ('whole_foods', 'short_ship',     NULL, 0, 'signed_bol,pack_log',         0.40, 'Not published; Pay-by-PO program required'),
  ('whole_foods', 'label_fine',     NULL, 0, 'label_scan',                  0.25, 'Not published'),
  ('whole_foods', 'pallet_fine',    NULL, 0, 'photo',                       0.25, 'Not published'),
  ('whole_foods', 'damaged',        NULL, 0, 'signed_bol,photo',            0.50, 'Not published'),
  ('whole_foods', 'late_delivery',  NULL, 0, 'pod',                         0.30, 'No published OTIF program'),
  ('whole_foods', 'promo_billback', NULL, 0, 'promo_agreement',             0.40, 'Regional fragmentation — different practices per region'),
  ('whole_foods', 'vague',          NULL, 0, 'pack_log',                    0.10, 'Cost-feed mismatches drive opaque deductions'),
  -- UNFI (Natural side)
  ('unfi', 'short_ship',     60,   1, 'signed_bol,pack_log',                0.40, '30–60 day practical window; Excel-only dispute form'),
  ('unfi', 'label_fine',     60,   1, 'label_scan',                         0.25, 'Inferred'),
  ('unfi', 'pallet_fine',    60,   1, 'photo',                              0.25, 'Inferred'),
  ('unfi', 'damaged',        60,   1, 'signed_bol,photo',                   0.45, 'Includes unsaleables'),
  ('unfi', 'late_delivery',  60,   1, 'pod',                                0.30, '$250+ late, $500 no-show, $300 short-notice reschedule'),
  ('unfi', 'promo_billback', 60,   0, 'promo_agreement',                    0.35, 'MCB disputes common; unsubstantiated promo backups'),
  ('unfi', 'vague',          NULL, 1, 'pack_log',                           0.10, 'Vague chargebacks routine; PDFs/screenshots rejected on dispute form'),
  -- KeHE
  ('kehe', 'short_ship',     2,    1, 'signed_bol,pack_log',                0.35, '48-hour UDR window — locks fast'),
  ('kehe', 'label_fine',     180,  1, 'label_scan',                         0.30, 'K-Solve 180-day cap, newly strict'),
  ('kehe', 'pallet_fine',    180,  1, 'photo',                              0.30, 'K-Solve'),
  ('kehe', 'damaged',        180,  1, 'signed_bol,photo',                   0.45, 'K-Solve; UDR for damage at receipt'),
  ('kehe', 'late_delivery',  180,  1, 'pod',                                0.30, 'K-Solve'),
  ('kehe', 'promo_billback', 180,  0, 'promo_agreement',                    0.40, 'MCB + 8% admin fee + $65/DC minimum'),
  ('kehe', 'vague',          180,  1, 'pack_log',                           0.10, 'Connect BI fee 2% of sales falls here'),
  -- Kroger
  ('kroger', 'short_ship',     NULL, 0, 'signed_bol,pack_log',   0.50, 'No published window; specialty-friendly buyer-relationship dispute path'),
  ('kroger', 'label_fine',     NULL, 0, 'label_scan',            0.30, 'GS1-128 inferred from packaging guide'),
  ('kroger', 'pallet_fine',    NULL, 0, 'photo',                 0.30, '4-way pallet standards inferred'),
  ('kroger', 'damaged',        NULL, 0, 'signed_bol,photo',      0.55, 'No published window'),
  ('kroger', 'late_delivery',  NULL, 0, 'pod',                   0.40, 'No published OTIF'),
  ('kroger', 'promo_billback', NULL, 0, 'promo_agreement',       0.45, 'No published'),
  ('kroger', 'vague',          NULL, 0, 'pack_log',              0.15, 'Specialty-friendly buyer relationship'),
  -- Sprouts
  ('sprouts', 'short_ship',     NULL, 0, 'signed_bol,pack_log', 0.40, 'Many deductions arrive via UNFI/KeHE statements'),
  ('sprouts', 'label_fine',     NULL, 0, 'label_scan',          0.25, 'GS1-128 required'),
  ('sprouts', 'pallet_fine',    NULL, 0, 'photo',               0.25, 'Inferred'),
  ('sprouts', 'damaged',        NULL, 0, 'signed_bol,photo',    0.45, 'Inferred'),
  ('sprouts', 'late_delivery',  NULL, 0, 'pod',                 0.30, 'Inferred'),
  ('sprouts', 'promo_billback', NULL, 0, 'promo_agreement',     0.40, 'Free Fill + Fair Share via reset calendar'),
  ('sprouts', 'vague',          NULL, 0, 'pack_log',            0.10, 'Inferred'),
  -- Regional Group
  ('regional_group', 'short_ship',     NULL, 0, 'signed_bol,pack_log',  0.40, 'Inferred norms; no published windows'),
  ('regional_group', 'label_fine',     NULL, 0, 'label_scan',           0.25, 'Inferred'),
  ('regional_group', 'pallet_fine',    NULL, 0, 'photo',                0.25, 'Inferred'),
  ('regional_group', 'damaged',        NULL, 0, 'signed_bol,photo',     0.45, 'Inferred'),
  ('regional_group', 'late_delivery',  NULL, 0, 'pod',                  0.30, 'Inferred'),
  ('regional_group', 'promo_billback', NULL, 0, 'promo_agreement',      0.40, 'Inferred'),
  ('regional_group', 'vague',          NULL, 0, 'pack_log',             0.10, 'Inferred'),
  -- ---- spoilage (operational failure — full pipeline) ----
  ('walmart',             'spoilage', 365,  1, 'signed_bol,photo,pack_log',  0.45, 'Code 28-adjacent; product condition disputes at receiving — heat exposure, expiration, quality'),
  ('costco',              'spoilage', NULL, 1, 'signed_bol,photo',           0.45, 'Cross-dock receiving rejects on condition/quality at depot; window inferred'),
  ('whole_foods',         'spoilage', NULL, 0, 'signed_bol,photo',           0.40, 'Strict quality program; regional fragmentation drives variability'),
  ('unfi',                'spoilage', 60,   1, 'signed_bol,photo',           0.40, 'Includes unsaleables on the natural side; Excel-only dispute form'),
  ('kehe',                'spoilage', 180,  1, 'signed_bol,photo',           0.40, 'UDR window 48hr at receipt for damage/spoilage; K-Solve 180-day cap on follow-up'),
  ('kroger',              'spoilage', NULL, 0, 'signed_bol,photo',           0.55, 'Specialty buyer relationship; willing to credit on photo + record'),
  ('sprouts',             'spoilage', NULL, 0, 'signed_bol,photo',           0.45, 'Receiving teams reject perceived quality issues quickly'),
  ('regional_group',      'spoilage', NULL, 0, 'signed_bol,photo',           0.40, 'Inferred regional norm'),
  -- ---- slotting (negotiated cost — non-disputable, terminal) ----
  ('walmart',             'slotting', NULL, 1, '',                           0.0, 'Slotting / new-item / planogram fees — contractually agreed, not disputable'),
  ('costco',              'slotting', NULL, 1, '',                           0.0, 'Pay-to-play club placement and demo costs; non-disputable'),
  ('whole_foods',         'slotting', NULL, 1, '',                           0.0, 'New-item slotting + reset placement fees by region; non-disputable'),
  ('unfi',                'slotting', NULL, 1, '',                           0.0, 'New-item / catalog / planogram fees on the natural side; non-disputable'),
  ('kehe',                'slotting', NULL, 1, '',                           0.0, 'New-item slotting + Connect BI placement fees; non-disputable'),
  ('kroger',              'slotting', NULL, 1, '',                           0.0, 'Specialty placement allowance; negotiated annually'),
  ('sprouts',             'slotting', NULL, 1, '',                           0.0, 'Reset / new-item placement billbacks; non-disputable'),
  ('regional_group',      'slotting', NULL, 1, '',                           0.0, 'New-item placement allowance; non-disputable');

-- ---------- deduction_codes ----------
-- Walmart codes are publicly documented; KeHE codes mostly documented;
-- Costco / WFM / regional codes inferred (is_published=0) since
-- canonical lists aren't public. UNFI uses 3-letter codes that aren't
-- fully published — representative codes flagged unpublished.

INSERT INTO deduction_codes (code_id, retailer_id, code, name, deduction_type, is_published) VALUES
  -- Walmart (published)
  ('walmart_11', 'walmart', '11', 'Price Difference Between PO & Invoice',          'promo_billback', 1),
  ('walmart_13', 'walmart', '13', 'Substitution Overcharge',                        'short_ship',     1),
  ('walmart_21', 'walmart', '21', 'Concealed Shortage',                             'short_ship',     1),
  ('walmart_22', 'walmart', '22', 'Merchandise Billed Not Shipped',                 'short_ship',     1),
  ('walmart_24', 'walmart', '24', 'Carton Shortage / Freight Bill Signed Short',    'short_ship',     1),
  ('walmart_25', 'walmart', '25', 'No Merchandise Received for Invoice',            'short_ship',     1),
  ('walmart_28', 'walmart', '28', 'Carton Damage – Freight Bill Signed Damaged',    'damaged',        1),
  ('walmart_30', 'walmart', '30', 'Duplicate Billing',                              'vague',          1),
  ('walmart_51', 'walmart', '51', 'Promotional Allowance',                          'promo_billback', 1),
  ('walmart_59', 'walmart', '59', 'Defective Merchandise Allowance',                'damaged',        1),
  ('walmart_87', 'walmart', '87', 'Other',                                          'vague',          1),
  ('walmart_99', 'walmart', '99', 'OTIF',                                           'late_delivery',  1),
  -- Costco (inferred placeholders)
  ('costco_short_ship',     'costco', 'SHRT',  'Shortage at receiving',     'short_ship',     0),
  ('costco_label_fine',     'costco', 'LBL',   'Labeling noncompliance',    'label_fine',     0),
  ('costco_pallet_fine',    'costco', 'PALT',  'Pallet noncompliance',      'pallet_fine',    0),
  ('costco_damaged',        'costco', 'DMG',   'Damaged at receiving',      'damaged',        0),
  ('costco_late_delivery',  'costco', 'LATE',  'Late or refused delivery',  'late_delivery',  0),
  ('costco_promo_billback', 'costco', 'PROMO', 'Promotional allowance',     'promo_billback', 0),
  ('costco_vague',          'costco', 'MISC',  'Miscellaneous deduction',   'vague',          0),
  -- Whole Foods (inferred placeholders)
  ('wholefoods_short_ship',     'whole_foods', 'SHRT',  'Shortage',              'short_ship',     0),
  ('wholefoods_label_fine',     'whole_foods', 'LBL',   'Labeling fine',         'label_fine',     0),
  ('wholefoods_pallet_fine',    'whole_foods', 'PALT',  'Pallet fine',           'pallet_fine',    0),
  ('wholefoods_damaged',        'whole_foods', 'DMG',   'Damaged product',       'damaged',        0),
  ('wholefoods_late_delivery',  'whole_foods', 'LATE',  'Late delivery',         'late_delivery',  0),
  ('wholefoods_promo_billback', 'whole_foods', 'PROMO', 'Promo billback',        'promo_billback', 0),
  ('wholefoods_vague',          'whole_foods', 'MISC',  'Miscellaneous',         'vague',          0),
  -- UNFI (3-letter codes, partially inferred)
  ('unfi_sht', 'unfi', 'SHT', 'Shortage',                                   'short_ship',     0),
  ('unfi_lbl', 'unfi', 'LBL', 'Labeling fine',                              'label_fine',     0),
  ('unfi_plt', 'unfi', 'PLT', 'Pallet noncompliance',                       'pallet_fine',    0),
  ('unfi_dmg', 'unfi', 'DMG', 'Damaged product / unsaleable',               'damaged',        0),
  ('unfi_lat', 'unfi', 'LAT', 'Late delivery',                              'late_delivery',  0),
  ('unfi_mcb', 'unfi', 'MCB', 'Manufacturer chargeback (promo)',            'promo_billback', 0),
  ('unfi_msc', 'unfi', 'MSC', 'Miscellaneous deduction',                    'vague',          0),
  -- KeHE (mostly documented)
  ('kehe_udr',      'kehe', 'UDR',   'Unloading Discrepancy (shortage/over/damage)', 'short_ship',     1),
  ('kehe_mcb',      'kehe', 'MCB',   'Manufacturer Chargeback (promo)',              'promo_billback', 1),
  ('kehe_mcb_fee',  'kehe', 'MCBF',  'MCB admin fee (8%, $65/DC min)',               'promo_billback', 1),
  ('kehe_ep',       'kehe', 'EP',    'Event Promotion fee',                          'promo_billback', 1),
  ('kehe_bi',       'kehe', 'BI',    'Connect BI fee (2% of sales)',                 'vague',          1),
  ('kehe_freight',  'kehe', 'FRT',   'Freight allowance',                            'vague',          1),
  ('kehe_label',    'kehe', 'LBL',   'Labeling noncompliance',                       'label_fine',     0),
  ('kehe_late',     'kehe', 'LATE',  'Late delivery',                                'late_delivery',  0),
  -- Kroger (inferred)
  ('kroger_short_ship',     'kroger', 'SHRT',  'Shortage',         'short_ship',     0),
  ('kroger_label_fine',     'kroger', 'LBL',   'Label fine',       'label_fine',     0),
  ('kroger_pallet_fine',    'kroger', 'PALT',  'Pallet fine',      'pallet_fine',    0),
  ('kroger_damaged',        'kroger', 'DMG',   'Damaged',          'damaged',        0),
  ('kroger_late_delivery',  'kroger', 'LATE',  'Late delivery',    'late_delivery',  0),
  ('kroger_promo_billback', 'kroger', 'PROMO', 'Promo billback',   'promo_billback', 0),
  ('kroger_vague',          'kroger', 'MISC',  'Miscellaneous',    'vague',          0),
  -- Sprouts (with named billbacks)
  ('sprouts_short_ship',     'sprouts', 'SHRT', 'Shortage',                    'short_ship',     0),
  ('sprouts_label_fine',     'sprouts', 'LBL',  'Label fine',                  'label_fine',     0),
  ('sprouts_pallet_fine',    'sprouts', 'PALT', 'Pallet fine',                 'pallet_fine',    0),
  ('sprouts_damaged',        'sprouts', 'DMG',  'Damaged',                     'damaged',        0),
  ('sprouts_late_delivery',  'sprouts', 'LATE', 'Late delivery',               'late_delivery',  0),
  ('sprouts_freefill',       'sprouts', 'FFL',  'Free Fill new-item billback', 'promo_billback', 0),
  ('sprouts_fairshare',      'sprouts', 'FAIR', 'Fair Share reset billback',   'promo_billback', 0),
  ('sprouts_vague',          'sprouts', 'MISC', 'Miscellaneous',               'vague',          0),
  -- Regional Group (generic regional)
  ('regional_group_short_ship',     'regional_group', 'SHRT',  'Shortage',         'short_ship',     0),
  ('regional_group_label_fine',     'regional_group', 'LBL',   'Label fine',       'label_fine',     0),
  ('regional_group_pallet_fine',    'regional_group', 'PALT',  'Pallet fine',      'pallet_fine',    0),
  ('regional_group_damaged',        'regional_group', 'DMG',   'Damaged',          'damaged',        0),
  ('regional_group_late_delivery',  'regional_group', 'LATE',  'Late delivery',    'late_delivery',  0),
  ('regional_group_promo_billback', 'regional_group', 'PROMO', 'Promo billback',   'promo_billback', 0),
  ('regional_group_vague',          'regional_group', 'MISC',  'Miscellaneous',    'vague',          0),
  -- ---- spoilage codes ----
  ('walmart_spoilage',             'walmart',             '29',    'Concealed damage / spoilage at receipt',         'spoilage', 1),
  ('costco_spoilage',              'costco',              'SPL',   'Spoilage / product condition at receipt',         'spoilage', 0),
  ('wholefoods_spoilage',          'whole_foods',         'SPL',   'Spoilage / quality at receipt',                  'spoilage', 0),
  ('unfi_spoilage',                'unfi',                'UNS',   'Unsaleable / spoilage',                          'spoilage', 0),
  ('kehe_spoilage',                'kehe',                'UDRS',  'UDR — spoilage at receipt',                      'spoilage', 0),
  ('kroger_spoilage',              'kroger',              'SPL',   'Spoilage / quality complaint',                   'spoilage', 0),
  ('sprouts_spoilage',             'sprouts',             'SPL',   'Spoilage / quality complaint',                   'spoilage', 0),
  ('regional_group_spoilage',      'regional_group',      'SPL',   'Spoilage / quality complaint',                   'spoilage', 0),
  -- ---- slotting codes (non-disputable, negotiated) ----
  ('walmart_slotting',             'walmart',             'NIF',   'New-item / slotting fee',                        'slotting', 0),
  ('costco_slotting',              'costco',              'SLOT',  'Slotting / pay-to-play club placement',          'slotting', 0),
  ('wholefoods_slotting',          'whole_foods',         'SLOT',  'New-item / placement fee',                       'slotting', 0),
  ('unfi_slotting',                'unfi',                'SLOT',  'Slotting / catalog placement',                   'slotting', 0),
  ('kehe_slotting',                'kehe',                'SLOT',  'Slotting / Connect BI placement',                'slotting', 0),
  ('kroger_slotting',              'kroger',              'SLOT',  'Placement allowance',                            'slotting', 0),
  ('sprouts_slotting',             'sprouts',             'SLOT',  'Reset / new-item placement billback',            'slotting', 0),
  ('regional_group_slotting',      'regional_group',      'SLOT',  'New-item placement allowance',                   'slotting', 0);

-- ---------- edi_requirements ----------
-- Compliance specs per retailer. Used to render retailer-rule cards in the UI
-- and to seed pack_records (label compliance, pallet compliance, etc.).

INSERT INTO edi_requirements (retailer_id, category, requirement, penalty_if_violated, is_verified, source_url) VALUES
  -- Walmart
  ('walmart', 'label',       'GS1-128 case labels with Walmart-required fields, two per case',                              '$200 admin + $1/case (SQEP Phase 2)',                  1, 'https://supplierwiki.supplypike.com/articles/calculating-sqep-fines-by-defect'),
  ('walmart', 'pallet',      'Walmart pallet spec, slip-sheet/wrap, height limits',                                         '$200 admin + $4/pallet (SQEP Phase 3)',                1, 'https://supplierwiki.supplypike.com/articles/calculating-sqep-fines-by-defect'),
  ('walmart', 'asn',         'EDI 856 ASN required before shipment arrives',                                                '$25/PO if not downloaded (SQEP Phase 1, non-DSDC)',    1, 'https://supplierwiki.supplypike.com/articles/calculating-sqep-fines-by-defect'),
  ('walmart', 'otif',        'Prepaid 90% / Collect 98% on-time, 95% in-full',                                              '3% of COGS on non-compliant cases',                    1, 'https://vendormint.com/walmart-on-time-in-full-otif-compliance/'),
  ('walmart', 'carton',      'Walmart-spec carton dimensions and labeling',                                                 'Code 22 perceived shortage if not scannable',          1, 'https://www.8thandwalton.com/blog/walmart-deduction-codes/'),
  -- Costco
  ('costco',  'label',       'GS1-128/SSCC, on two adjacent sides; vendor#, PO, item, qty, weight, destination',            '$50–$150/carton (inferred)',                           0, 'https://www.orderease.com/community/the-2025-guide-to-costco-edi-compliance-automation-chargeback-prevention'),
  ('costco',  'pallet',      '48x40 footprint; 58 inch max height; iGPS/PECO/CHEP only — no GMA #1 stringer',               'Lean/overhang/underhang chargeback',                   1, 'https://www.clubstorepackaging.com/post/costco-packaging-specifications-requirements'),
  ('costco',  'asn',         'EDI 856 via SPS Commerce VAN',                                                                '$50–$200 per incident (inferred)',                     0, 'https://www.orderease.com/community/the-2025-guide-to-costco-edi-compliance-automation-chargeback-prevention'),
  ('costco',  'appointment', 'Scheduled appointment window; 30-minute grace then refusal',                                  'Refused delivery → reduced future allocation',         1, 'https://www.chep.com/files/download/costco-delivery-driver-guidelines-kemps-creek-depot-july-21.pdf'),
  ('costco',  'carton',      '50 lb max if hand-lifted; 1500 lbs crush <750lb load, 2500 lbs ≥750lb load',                  'Non-compliant packaging 2% chargeback',                1, 'https://www.clubstorepackaging.com/post/costco-packaging-specifications-requirements'),
  -- Whole Foods (WFM-only)
  ('whole_foods', 'label',  'GS1-128, regional spec varies',                                                                'Regional fragmentation — opaque deductions',           0, 'https://www.spscommerce.com/community/articles/how-to-navigate-the-whole-foods-supplier-portal'),
  ('whole_foods', 'asn',    'EDI 850/855/810/856/997',                                                                      'Inferred',                                             0, NULL),
  ('whole_foods', 'carton', 'Category-specific (Center Store, Perishable, Adult Beverage, Culinary)',                       'Inferred',                                             0, NULL),
  ('whole_foods', 'otif',   'No published OTIF program',                                                                    NULL,                                                   0, NULL),
  -- UNFI
  ('unfi', 'label',       'Standard grocery GS1-128 with UPC/lot/best-by',                                                  'Inferred',                                             0, NULL),
  ('unfi', 'asn',         'EDI 856 required',                                                                               'Inferred',                                             0, NULL),
  ('unfi', 'otif',        '95% fill-rate; service-level fine if missed two consecutive weeks',                              '3% service-level fine',                                1, 'https://www.spscommerce.com/community/articles/how-natural-suppliers-dispute-unfi-deductions'),
  ('unfi', 'appointment', 'Natural side: 1 day notice; Conventional: 3 days',                                               '$300 short-notice reschedule, $500 no-show',           1, 'https://www.spscommerce.com/community/articles/how-natural-suppliers-dispute-unfi-deductions'),
  -- KeHE
  ('kehe', 'label',  'GS1-128 standard with required fields',                                                               'Label fines via K-Solve',                              0, NULL),
  ('kehe', 'asn',    'EDI 856 required pre-arrival',                                                                        'ASN late = chargeback',                                0, NULL),
  ('kehe', 'otif',   'On-time delivery; UDR triggers on shortage/over/damage at receipt',                                   '48-hour UDR response window',                          1, 'https://tryintercept.com/blog/kehe-deductions'),
  ('kehe', 'carton', 'Standard carton requirements',                                                                        'Connect BI fee 2% of sales',                           1, 'https://tryintercept.com/blog/kehe-deductions'),
  -- Kroger
  ('kroger', 'label',  'GS1-128 case labels with lot/catch weight/expiration; SSCC pallet labels two per pallet','Routing-guide inferred',                               0, NULL),
  ('kroger', 'pallet', '4-way pallet condition standards',                                                       'Inferred',                                             0, NULL),
  ('kroger', 'asn',    'EDI 850/855/810/997; ASN entry via supplier portal',                                     'Inferred',                                             0, NULL),
  ('kroger', 'carton', 'Carton size/weight limits, one-PO-per-carton',                                           'Inferred',                                             0, NULL),
  -- Sprouts
  ('sprouts', 'label',       'GS1-128 (UCC-128) shipping labels required',                                      'Inferred',                                             0, NULL),
  ('sprouts', 'asn',         'EDI 850/855/860/856/810/812/997 mandatory',                                       'Inferred',                                             0, NULL),
  ('sprouts', 'carton',      'Standard carton requirements',                                                    'Inferred',                                             0, NULL),
  ('sprouts', 'appointment', 'Refresh / category-reset calendar drives placement timing',                       'Free Fill / Fair Share billbacks per reset',           0, NULL),
  -- Regional Group (generic regional)
  ('regional_group', 'label',  'Standard grocery GS1-128',                                                              'Inferred',                                             0, NULL),
  ('regional_group', 'asn',    'EDI 856 expected',                                                                      'Inferred',                                             0, NULL),
  ('regional_group', 'pallet', 'Standard pallet condition',                                                             'Inferred',                                             0, NULL),
  ('regional_group', 'carton', 'Standard carton requirements',                                                          'Inferred',                                             0, NULL);
