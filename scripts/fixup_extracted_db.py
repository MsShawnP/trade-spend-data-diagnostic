"""Post-extraction fixup: add compatibility columns the workbook expects.

The Postgres schema uses retailer_id (e.g. 'RET-WALMART') and lacks several
columns that the local generation scripts added. This script patches the
extracted SQLite so the existing workbook code runs unchanged.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "cinderhaven-data" / "data" / "cinderhaven_product_master.db"

RETAILER_MAP = {
    "RET-COSTCO": "Costco",
    "RET-KROGER": "Kroger",
    "RET-REGIONAL": "Regional Group",
    "RET-SPROUTS": "Sprouts",
    "RET-WALMART": "Walmart",
    "RET-WHOLEFOODS": "Whole Foods",
}


def fixup():
    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA journal_mode=WAL")

    # --- stores: add 'retailer' column from retailer_id mapping ---
    cols = [r[1] for r in conn.execute("PRAGMA table_info(stores)").fetchall()]
    if "retailer" not in cols:
        conn.execute("ALTER TABLE stores ADD COLUMN retailer TEXT")
        for rid, name in RETAILER_MAP.items():
            conn.execute("UPDATE stores SET retailer = ? WHERE retailer_id = ?", (name, rid))
        print("  stores: added 'retailer' column")

    if "is_aggregated_channel" not in cols:
        conn.execute("ALTER TABLE stores ADD COLUMN is_aggregated_channel INTEGER DEFAULT 0")
        print("  stores: added 'is_aggregated_channel' column")

    # --- chargebacks: add 'retailer' from retailer_id ---
    cols = [r[1] for r in conn.execute("PRAGMA table_info(chargebacks)").fetchall()]
    if "retailer" not in cols:
        conn.execute("ALTER TABLE chargebacks ADD COLUMN retailer TEXT")
        for rid, name in RETAILER_MAP.items():
            conn.execute("UPDATE chargebacks SET retailer = ? WHERE retailer_id = ?", (name, rid))
        print("  chargebacks: added 'retailer' column")

    # --- price_history: add 'retailer' from retailer_id ---
    cols = [r[1] for r in conn.execute("PRAGMA table_info(price_history)").fetchall()]
    if "retailer" not in cols:
        conn.execute("ALTER TABLE price_history ADD COLUMN retailer TEXT")
        for rid, name in RETAILER_MAP.items():
            conn.execute("UPDATE price_history SET retailer = ? WHERE retailer_id = ?", (name, rid))
        print("  price_history: added 'retailer' column")

    # --- promotions: add 'retailer' + 'duration_weeks' + 'store_scope' ---
    cols = [r[1] for r in conn.execute("PRAGMA table_info(promotions)").fetchall()]
    if "retailer" not in cols:
        conn.execute("ALTER TABLE promotions ADD COLUMN retailer TEXT")
        for rid, name in RETAILER_MAP.items():
            conn.execute("UPDATE promotions SET retailer = ? WHERE retailer_id = ?", (name, rid))
        print("  promotions: added 'retailer' column")

    if "duration_weeks" not in cols:
        conn.execute("ALTER TABLE promotions ADD COLUMN duration_weeks INTEGER")
        conn.execute("""
            UPDATE promotions SET duration_weeks = CAST(
                (julianday(end_week) - julianday(start_week)) / 7.0 + 0.5 AS INTEGER
            ) WHERE start_week IS NOT NULL AND end_week IS NOT NULL
        """)
        print("  promotions: added 'duration_weeks' column")

    if "store_scope" not in cols:
        conn.execute("ALTER TABLE promotions ADD COLUMN store_scope TEXT DEFAULT 'all'")
        print("  promotions: added 'store_scope' column")

    # --- deductions: add missing columns ---
    cols = [r[1] for r in conn.execute("PRAGMA table_info(deductions)").fetchall()]

    if "shipment_id" not in cols:
        conn.execute("ALTER TABLE deductions ADD COLUMN shipment_id TEXT")
        conn.execute("""
            UPDATE deductions SET shipment_id = (
                SELECT s.shipment_id FROM shipments s
                WHERE s.order_id = deductions.order_id LIMIT 1
            ) WHERE order_id IS NOT NULL
        """)
        print("  deductions: added 'shipment_id' column")

    if "code_as_remitted" not in cols:
        conn.execute("ALTER TABLE deductions ADD COLUMN code_as_remitted TEXT")
        conn.execute("""
            UPDATE deductions SET code_as_remitted = (
                SELECT dc.code FROM deduction_codes dc WHERE dc.code_id = deductions.code_id
            ) WHERE code_id IS NOT NULL
        """)
        print("  deductions: added 'code_as_remitted' column")

    if "is_vague" not in cols:
        conn.execute("ALTER TABLE deductions ADD COLUMN is_vague INTEGER DEFAULT 0")
        conn.execute("""
            UPDATE deductions SET is_vague = 1
            WHERE code_as_remitted IS NULL OR code_as_remitted = ''
               OR deduction_type IN ('spoilage', 'damaged')
        """)
        print("  deductions: added 'is_vague' column")

    if "remittance_description" not in cols:
        conn.execute("ALTER TABLE deductions ADD COLUMN remittance_description TEXT")
        conn.execute("""
            UPDATE deductions SET remittance_description = deduction_type || ' - ' || retailer_id
        """)
        print("  deductions: added 'remittance_description' column")

    if "is_double_dip" not in cols:
        conn.execute("ALTER TABLE deductions ADD COLUMN is_double_dip INTEGER DEFAULT 0")
        conn.execute("""
            UPDATE deductions SET is_double_dip = 1
            WHERE deduction_id IN (
                SELECT d1.deduction_id
                FROM deductions d1
                JOIN deductions d2 ON d1.order_id = d2.order_id
                    AND d1.deduction_id != d2.deduction_id
                    AND d1.deduction_type = 'promo_billback'
                    AND d2.deduction_type = 'promo_billback'
                    AND ABS(d1.amount - d2.amount) < 0.01
                WHERE d1.order_id IS NOT NULL
            )
        """)
        print("  deductions: added 'is_double_dip' column")

    # --- disputes: add missing columns ---
    cols = [r[1] for r in conn.execute("PRAGMA table_info(disputes)").fetchall()]
    if "was_within_deadline" not in cols:
        conn.execute("ALTER TABLE disputes ADD COLUMN was_within_deadline INTEGER DEFAULT 1")
        print("  disputes: added 'was_within_deadline' column")

    if "submitted_evidence_count" not in cols:
        conn.execute("ALTER TABLE disputes ADD COLUMN submitted_evidence_count INTEGER DEFAULT 0")
        conn.execute("""
            UPDATE disputes SET submitted_evidence_count = (
                SELECT COUNT(*) FROM dispute_evidence de WHERE de.dispute_id = disputes.dispute_id
            )
        """)
        print("  disputes: added 'submitted_evidence_count' column")

    conn.commit()
    conn.execute("ANALYZE")
    conn.close()
    print("\nFixup complete.")


if __name__ == "__main__":
    fixup()
