-- Deduction-tracking schema for the retailer-deduction-recovery project.
-- Extends the base cinderhaven-data SQLite database without modifying its
-- existing tables. Run after the base build_db.py has produced
-- cinderhaven_product_master.db.
--
-- Design rationale: see data/schema.md.

-- ---------- 1. retailers ----------
DROP TABLE IF EXISTS retailers;
CREATE TABLE retailers (
    retailer_id          TEXT PRIMARY KEY,
    name                 TEXT NOT NULL,
    channel_type         TEXT NOT NULL CHECK (channel_type IN ('retailer', 'distributor', 'dtc')),
    dispute_portal_name  TEXT,
    dispute_portal_url   TEXT,
    dispute_method       TEXT CHECK (dispute_method IN ('portal', 'email_excel', 'email_buyer', 'mixed', NULL)),
    notes                TEXT
);

-- ---------- 2. retailer_rules ----------
DROP TABLE IF EXISTS retailer_rules;
CREATE TABLE retailer_rules (
    retailer_id            TEXT NOT NULL,
    deduction_type         TEXT NOT NULL CHECK (deduction_type IN (
        'short_ship', 'label_fine', 'pallet_fine', 'damaged',
        'late_delivery', 'promo_billback', 'vague',
        'spoilage', 'slotting')),
    dispute_window_days    INTEGER,
    auto_deduct            INTEGER NOT NULL DEFAULT 0,  -- BOOLEAN as 0/1
    evidence_required      TEXT,
    typical_recovery_rate  REAL,
    notes                  TEXT,
    PRIMARY KEY (retailer_id, deduction_type),
    FOREIGN KEY (retailer_id) REFERENCES retailers(retailer_id)
);

-- ---------- 3. deduction_codes ----------
DROP TABLE IF EXISTS deduction_codes;
CREATE TABLE deduction_codes (
    code_id          TEXT PRIMARY KEY,
    retailer_id      TEXT NOT NULL,
    code             TEXT NOT NULL,
    name             TEXT NOT NULL,
    deduction_type   TEXT NOT NULL,
    is_published     INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (retailer_id) REFERENCES retailers(retailer_id)
);
CREATE INDEX idx_deduction_codes_retailer ON deduction_codes(retailer_id);

-- ---------- 4. orders ----------
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id                          TEXT PRIMARY KEY,
    retailer_id                       TEXT NOT NULL,
    po_number                         TEXT NOT NULL,
    po_date                           TEXT NOT NULL,
    requested_ship_date               TEXT NOT NULL,
    requested_delivery_window_start   TEXT,
    requested_delivery_window_end     TEXT,
    dc_id                             TEXT,
    total_units                       INTEGER NOT NULL,
    total_value                       REAL NOT NULL,
    FOREIGN KEY (retailer_id) REFERENCES retailers(retailer_id)
);
CREATE INDEX idx_orders_po_number ON orders(po_number);
CREATE INDEX idx_orders_retailer_date ON orders(retailer_id, po_date);

-- ---------- 5. order_lines ----------
DROP TABLE IF EXISTS order_lines;
CREATE TABLE order_lines (
    order_line_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id       TEXT NOT NULL,
    sku            TEXT NOT NULL,
    units_ordered  INTEGER NOT NULL,
    unit_price     REAL NOT NULL,
    line_total     REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (sku) REFERENCES product_master(sku)
);
CREATE INDEX idx_order_lines_order ON order_lines(order_id);
CREATE INDEX idx_order_lines_sku ON order_lines(sku);

-- ---------- 6. shipments ----------
DROP TABLE IF EXISTS shipments;
CREATE TABLE shipments (
    shipment_id        TEXT PRIMARY KEY,
    order_id           TEXT NOT NULL,
    ship_date          TEXT NOT NULL,
    delivery_date      TEXT,
    carrier            TEXT,
    bol_number         TEXT,
    bol_signed         INTEGER NOT NULL DEFAULT 0,
    bol_signed_short   INTEGER NOT NULL DEFAULT 0,
    bol_signed_damaged INTEGER NOT NULL DEFAULT 0,
    pod_received       INTEGER NOT NULL DEFAULT 0,
    units_shipped      INTEGER NOT NULL,
    pallets_shipped    INTEGER,
    asn_sent           INTEGER NOT NULL DEFAULT 0,
    asn_sent_late      INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
CREATE INDEX idx_shipments_order ON shipments(order_id);
CREATE INDEX idx_shipments_date ON shipments(ship_date);

-- ---------- 7. pack_records ----------
DROP TABLE IF EXISTS pack_records;
CREATE TABLE pack_records (
    pack_record_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id                    TEXT NOT NULL,
    shipment_id                 TEXT,
    pack_date                   TEXT NOT NULL,
    packer_initials             TEXT,
    units_picked                INTEGER NOT NULL,
    units_packed                INTEGER NOT NULL,
    units_pick_pack_match       INTEGER NOT NULL,
    label_type_used             TEXT NOT NULL,
    label_scannable             INTEGER NOT NULL,
    pack_verification           TEXT NOT NULL CHECK (pack_verification IN ('none', 'paper_note', 'digital_log')),
    evidence_format             TEXT NOT NULL CHECK (evidence_format IN ('paper_note', 'digital', 'none')),
    evidence_location           TEXT CHECK (evidence_location IN ('office_filing_cabinet', 'warehouse_clipboard', 'system', 'lost', NULL)),
    evidence_retrieval_minutes  INTEGER,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);
CREATE INDEX idx_pack_records_order ON pack_records(order_id);

-- ---------- 8. remittances (created before deductions because deductions FK to remittances) ----------
DROP TABLE IF EXISTS remittances;
CREATE TABLE remittances (
    remittance_id     TEXT PRIMARY KEY,
    retailer_id       TEXT NOT NULL,
    received_date     TEXT NOT NULL,
    format            TEXT NOT NULL CHECK (format IN ('edi_820', 'portal_download', 'paper_check', 'email_pdf')),
    gross_amount      REAL NOT NULL,
    net_amount        REAL NOT NULL,
    total_deductions  REAL NOT NULL,
    clarity           TEXT NOT NULL CHECK (clarity IN ('clear', 'partial', 'opaque')),
    FOREIGN KEY (retailer_id) REFERENCES retailers(retailer_id)
);
CREATE INDEX idx_remittances_retailer_date ON remittances(retailer_id, received_date);

-- ---------- 9. deductions ----------
DROP TABLE IF EXISTS deductions;
CREATE TABLE deductions (
    deduction_id            TEXT PRIMARY KEY,
    retailer_id             TEXT NOT NULL,
    order_id                TEXT,
    shipment_id             TEXT,
    deduction_type          TEXT NOT NULL CHECK (deduction_type IN (
        'short_ship', 'label_fine', 'pallet_fine', 'damaged',
        'late_delivery', 'promo_billback', 'vague',
        'spoilage', 'slotting')),
    code_id                 TEXT,
    code_as_remitted        TEXT,
    remittance_description  TEXT,
    amount                  REAL NOT NULL,
    deduction_date          TEXT NOT NULL,
    dispute_deadline        TEXT,
    is_vague                INTEGER NOT NULL DEFAULT 0,
    is_post_audit           INTEGER NOT NULL DEFAULT 0,
    is_double_dip           INTEGER NOT NULL DEFAULT 0,
    remittance_id           TEXT,
    FOREIGN KEY (retailer_id) REFERENCES retailers(retailer_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    FOREIGN KEY (code_id) REFERENCES deduction_codes(code_id),
    FOREIGN KEY (remittance_id) REFERENCES remittances(remittance_id)
);
CREATE INDEX idx_deductions_retailer_date ON deductions(retailer_id, deduction_date);
CREATE INDEX idx_deductions_order ON deductions(order_id);
CREATE INDEX idx_deductions_deadline ON deductions(dispute_deadline);

-- ---------- 10. disputes ----------
DROP TABLE IF EXISTS disputes;
CREATE TABLE disputes (
    dispute_id                TEXT PRIMARY KEY,
    deduction_id              TEXT NOT NULL UNIQUE,
    filed_date                TEXT,
    filing_method             TEXT CHECK (filing_method IN ('portal', 'email_excel', 'email_buyer', NULL)),
    evidence_quality          TEXT NOT NULL CHECK (evidence_quality IN (
        'digital_complete', 'digital_partial', 'handwritten_only', 'none')),
    submitted_evidence_count  INTEGER NOT NULL,
    was_within_deadline       INTEGER,
    outcome                   TEXT NOT NULL CHECK (outcome IN (
        'pending', 'won_full', 'won_partial', 'lost_evidence',
        'lost_deadline', 'lost_no_response', 'lost_other', 'abandoned')),
    recovered_amount          REAL,
    closed_date               TEXT,
    labor_hours               REAL NOT NULL,
    FOREIGN KEY (deduction_id) REFERENCES deductions(deduction_id)
);
CREATE INDEX idx_disputes_deduction ON disputes(deduction_id);

-- ---------- 11. dispute_evidence ----------
DROP TABLE IF EXISTS dispute_evidence;
CREATE TABLE dispute_evidence (
    evidence_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    dispute_id       TEXT NOT NULL,
    evidence_type    TEXT NOT NULL CHECK (evidence_type IN (
        'signed_bol', 'pod', 'pack_log', 'label_scan',
        'promo_agreement', 'asn_confirmation', 'photo')),
    was_submitted    INTEGER NOT NULL,
    was_required     INTEGER NOT NULL,
    format           TEXT CHECK (format IN ('digital', 'paper_scan', 'handwritten_note', 'missing', NULL)),
    notes            TEXT,
    FOREIGN KEY (dispute_id) REFERENCES disputes(dispute_id)
);
CREATE INDEX idx_dispute_evidence_dispute ON dispute_evidence(dispute_id);

-- ---------- 12. edi_requirements ----------
DROP TABLE IF EXISTS edi_requirements;
CREATE TABLE edi_requirements (
    requirement_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    retailer_id           TEXT NOT NULL,
    category              TEXT NOT NULL CHECK (category IN (
        'label', 'pallet', 'asn', 'otif', 'appointment', 'carton')),
    requirement           TEXT NOT NULL,
    penalty_if_violated   TEXT,
    is_verified           INTEGER NOT NULL,
    source_url            TEXT,
    FOREIGN KEY (retailer_id) REFERENCES retailers(retailer_id)
);
CREATE INDEX idx_edi_requirements_retailer ON edi_requirements(retailer_id, category);

-- ---------- 13. post_audit_claims ----------
DROP TABLE IF EXISTS post_audit_claims;
CREATE TABLE post_audit_claims (
    claim_id            TEXT PRIMARY KEY,
    deduction_id        TEXT NOT NULL,
    auditor_name        TEXT,
    audit_period_start  TEXT,
    audit_period_end    TEXT,
    claim_type          TEXT CHECK (claim_type IN ('pricing', 'allowance', 'freight', 'compliance', NULL)),
    lookback_months     INTEGER,
    FOREIGN KEY (deduction_id) REFERENCES deductions(deduction_id)
);
CREATE INDEX idx_post_audit_deduction ON post_audit_claims(deduction_id);
