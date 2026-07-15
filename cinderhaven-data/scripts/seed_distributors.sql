-- Distributor reference data and SKU-distributor authorization mappings.
-- Loaded by scripts/build_db.py after seed_product_master.sql.

CREATE TABLE IF NOT EXISTS distributors (
    distributor_id    TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    type              TEXT NOT NULL,
    coverage          TEXT NOT NULL,
    margin_pct        REAL NOT NULL,
    payment_terms_days INTEGER NOT NULL,
    headquarters      TEXT,
    notes             TEXT
);

INSERT INTO distributors VALUES ('UNFI', 'United Natural Foods Inc.', 'natural_specialty', 'national', 0.25, 30, 'Providence, RI', 'Largest US natural/organic distributor. Primary distribution partner.');
INSERT INTO distributors VALUES ('KeHE', 'KeHE Distributors LLC', 'natural_specialty', 'national', 0.27, 30, 'Naperville, IL', 'Second-largest US natural/specialty distributor. Secondary distribution partner.');

CREATE TABLE IF NOT EXISTS sku_distributors (
    sku               TEXT NOT NULL,
    distributor_id    TEXT NOT NULL,
    PRIMARY KEY (sku, distributor_id),
    FOREIGN KEY (sku) REFERENCES product_master(sku),
    FOREIGN KEY (distributor_id) REFERENCES distributors(distributor_id)
);

-- UNFI: 33 SKUs (primary distributor, broadest reach)
INSERT INTO sku_distributors VALUES ('CHP-0001', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0002', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0006', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0007', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0008', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0009', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0015', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0016', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0017', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0018', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0019', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0020', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0021', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0022', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0026', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0027', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0028', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0029', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0030', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0031', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0032', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0035', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0036', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0037', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0039', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0040', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0041', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0044', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0046', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0047', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0048', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0049', 'UNFI');
INSERT INTO sku_distributors VALUES ('CHP-0050', 'UNFI');

-- KeHE: 22 SKUs (~67% overlap with UNFI, typical for dual-distribution)
INSERT INTO sku_distributors VALUES ('CHP-0001', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0002', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0007', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0009', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0016', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0018', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0019', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0021', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0022', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0027', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0029', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0030', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0031', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0032', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0035', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0036', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0039', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0040', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0044', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0047', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0049', 'KeHE');
INSERT INTO sku_distributors VALUES ('CHP-0050', 'KeHE');
