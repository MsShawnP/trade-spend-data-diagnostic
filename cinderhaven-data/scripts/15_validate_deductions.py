"""Validate the deduction tables after the full pipeline.

Checks row counts, referential integrity, dollar volume targets,
date window alignment, double-dip presence, and design conventions.
Exits non-zero only on FAIL (structural issues).
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import date

from shared import DB_PATH

TARGETS = {
    "orders":            (9000, 14000),
    "order_lines":       (35000, 70000),
    "shipments":         (9000, 14000),
    "pack_records":      (9000, 14000),
    "deductions":        (7000, 16000),
    "remittances":       (400, 1400),
    "disputes":          (3000, 8000),
    "dispute_evidence":  (8000, 25000),
    "post_audit_claims": (30, 100),
    "retailers":         (10, 12),
    "retailer_rules":    (80, 120),
    "deduction_codes":   (70, 120),
    "edi_requirements":  (30, 50),
}

ANNUAL_DOLLAR_TARGET = (750_000, 1_200_000)
SCAN_DATA_END = date(2027, 1, 2)


class Reporter:
    def __init__(self) -> None:
        self.fail_count = 0
        self.warn_count = 0
        self.pass_count = 0

    def passed(self, msg: str) -> None:
        self.pass_count += 1
        print(f"  [PASS] {msg}")

    def warn(self, msg: str) -> None:
        self.warn_count += 1
        print(f"  [WARN] {msg}")

    def fail(self, msg: str) -> None:
        self.fail_count += 1
        print(f"  [FAIL] {msg}")


def in_range(value, lo, hi) -> bool:
    return lo <= value <= hi


def main() -> int:
    if not DB_PATH.exists():
        print(f"FATAL: {DB_PATH} does not exist.")
        return 2

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        rep = Reporter()

        # ===== Row counts =====
        print("Deduction table row counts:")
        for table, (lo, hi) in TARGETS.items():
            n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if in_range(n, lo, hi):
                rep.passed(f"{table:<22} {n:>6,}  (in [{lo:,}, {hi:,}])")
            else:
                rep.warn(f"{table:<22} {n:>6,}  (target [{lo:,}, {hi:,}])")

        # ===== Referential integrity =====
        print("\nReferential integrity:")
        checks = [
            ("orders.retailer_id -> retailers", """
                SELECT COUNT(*) FROM orders o
                LEFT JOIN retailers r ON r.retailer_id = o.retailer_id
                WHERE r.retailer_id IS NULL
            """),
            ("order_lines.order_id -> orders", """
                SELECT COUNT(*) FROM order_lines ol
                LEFT JOIN orders o ON o.order_id = ol.order_id
                WHERE o.order_id IS NULL
            """),
            ("order_lines.sku -> product_master", """
                SELECT COUNT(*) FROM order_lines ol
                LEFT JOIN product_master p ON p.sku = ol.sku
                WHERE p.sku IS NULL
            """),
            ("shipments.order_id -> orders", """
                SELECT COUNT(*) FROM shipments s
                LEFT JOIN orders o ON o.order_id = s.order_id
                WHERE o.order_id IS NULL
            """),
            ("pack_records.order_id -> orders", """
                SELECT COUNT(*) FROM pack_records p
                LEFT JOIN orders o ON o.order_id = p.order_id
                WHERE o.order_id IS NULL
            """),
            ("deductions.retailer_id -> retailers", """
                SELECT COUNT(*) FROM deductions d
                LEFT JOIN retailers r ON r.retailer_id = d.retailer_id
                WHERE r.retailer_id IS NULL
            """),
            ("deductions.order_id -> orders (where set)", """
                SELECT COUNT(*) FROM deductions d
                LEFT JOIN orders o ON o.order_id = d.order_id
                WHERE d.order_id IS NOT NULL AND o.order_id IS NULL
            """),
            ("deductions.code_id -> deduction_codes (where set)", """
                SELECT COUNT(*) FROM deductions d
                LEFT JOIN deduction_codes c ON c.code_id = d.code_id
                WHERE d.code_id IS NOT NULL AND c.code_id IS NULL
            """),
            ("deductions.remittance_id -> remittances (no orphans)", """
                SELECT COUNT(*) FROM deductions WHERE remittance_id IS NULL
            """),
            ("disputes.deduction_id -> deductions", """
                SELECT COUNT(*) FROM disputes d
                LEFT JOIN deductions de ON de.deduction_id = d.deduction_id
                WHERE de.deduction_id IS NULL
            """),
            ("dispute_evidence.dispute_id -> disputes", """
                SELECT COUNT(*) FROM dispute_evidence e
                LEFT JOIN disputes d ON d.dispute_id = e.dispute_id
                WHERE d.dispute_id IS NULL
            """),
            ("post_audit_claims.deduction_id -> deductions", """
                SELECT COUNT(*) FROM post_audit_claims p
                LEFT JOIN deductions d ON d.deduction_id = p.deduction_id
                WHERE d.deduction_id IS NULL
            """),
        ]
        for label, sql in checks:
            n = cur.execute(sql).fetchone()[0]
            if n == 0:
                rep.passed(label)
            else:
                rep.fail(f"{label}: {n} broken refs")

        # ===== Dollar volume =====
        print("\nDollar volume:")
        total = cur.execute("SELECT SUM(amount) FROM deductions").fetchone()[0] or 0
        window = cur.execute(
            "SELECT MIN(deduction_date), MAX(deduction_date) FROM deductions"
        ).fetchone()
        start = date.fromisoformat(window[0])
        end = date.fromisoformat(window[1])
        months = (end.year - start.year) * 12 + (end.month - start.month) + 1
        annualized = total * 12 / months

        lo, hi = ANNUAL_DOLLAR_TARGET
        if in_range(annualized, *ANNUAL_DOLLAR_TARGET):
            rep.passed(f"Annualized deductions ${annualized:,.0f} in target ${lo:,}-${hi:,}")
        else:
            rep.warn(f"Annualized deductions ${annualized:,.0f} outside target ${lo:,}-${hi:,}")

        # ===== Revenue still ~$25M =====
        print("\nBase dataset integrity:")
        total_rev = cur.execute("SELECT SUM(dollars_sold) FROM scan_data").fetchone()[0] or 0
        n_weeks = cur.execute("SELECT COUNT(DISTINCT week_ending) FROM scan_data").fetchone()[0] or 1
        annual_rev = total_rev * 52 / n_weeks
        if in_range(annual_rev, 23_000_000, 27_000_000):
            rep.passed(f"Annual wholesale revenue ${annual_rev:,.0f} still in target $23M-$27M")
        else:
            rep.fail(f"Annual wholesale revenue ${annual_rev:,.0f} OUTSIDE $23M-$27M")

        # ===== Date window alignment =====
        print("\nDate window alignment:")
        max_ded_date = cur.execute("SELECT MAX(deduction_date) FROM deductions").fetchone()[0]
        max_ded = date.fromisoformat(max_ded_date)
        if max_ded <= SCAN_DATA_END:
            rep.passed(f"Max deduction date {max_ded_date} <= scan_data end {SCAN_DATA_END.isoformat()}")
        else:
            rep.fail(f"Max deduction date {max_ded_date} > scan_data end {SCAN_DATA_END.isoformat()}")

        # ===== Double-dip presence =====
        print("\nDouble-dip deductions:")
        dd_count = cur.execute("SELECT COUNT(*) FROM deductions WHERE is_double_dip = 1").fetchone()[0]
        dd_total = cur.execute("SELECT SUM(amount) FROM deductions WHERE is_double_dip = 1").fetchone()[0] or 0
        if 2 <= dd_count <= 3:
            rep.passed(f"{dd_count} double-dip deductions present (target 2-3)")
        else:
            rep.fail(f"{dd_count} double-dip deductions (target 2-3)")
        if 15000 <= dd_total <= 20000:
            rep.passed(f"Double-dip total ${dd_total:,.0f} in target $15K-$20K")
        else:
            rep.warn(f"Double-dip total ${dd_total:,.0f} outside $15K-$20K target")

        # ===== Promotions: promo_cost and funding_mechanism =====
        print("\nPromotions extension:")
        promo_cols = [c[1] for c in cur.execute("PRAGMA table_info(promotions)").fetchall()]
        if "promo_cost" in promo_cols:
            rep.passed("promo_cost column exists on promotions")
            n_populated = cur.execute("SELECT COUNT(*) FROM promotions WHERE promo_cost IS NOT NULL").fetchone()[0]
            n_total = cur.execute("SELECT COUNT(*) FROM promotions").fetchone()[0]
            pct = n_populated / n_total if n_total else 0
            if 0.85 <= pct <= 0.95:
                rep.passed(f"promo_cost populated on {pct:.0%} of rows (~90% target)")
            else:
                rep.warn(f"promo_cost populated on {pct:.0%} of rows (target ~90%)")
        else:
            rep.fail("promo_cost column MISSING from promotions")

        if "funding_mechanism" in promo_cols:
            rep.passed("funding_mechanism column exists on promotions")
            n_populated = cur.execute(
                "SELECT COUNT(*) FROM promotions WHERE funding_mechanism IS NOT NULL"
            ).fetchone()[0]
            n_total = cur.execute("SELECT COUNT(*) FROM promotions").fetchone()[0]
            pct = n_populated / n_total if n_total else 0
            if pct >= 0.85:
                rep.passed(f"funding_mechanism populated on {pct:.0%} of rows")
            else:
                rep.warn(f"funding_mechanism populated on {pct:.0%} of rows")
        else:
            rep.fail("funding_mechanism column MISSING from promotions")

        # ===== Design conventions =====
        print("\nDesign conventions:")
        bad_vague = cur.execute(
            "SELECT COUNT(*) FROM deductions WHERE is_vague=1 AND deduction_type != 'vague'"
        ).fetchone()[0]
        if bad_vague == 0:
            rep.passed("is_vague=1 only on deduction_type='vague'")
        else:
            rep.fail(f"is_vague=1 on non-vague rows: {bad_vague}")

        slotting_with_dispute = cur.execute("""
            SELECT COUNT(*) FROM deductions d
            JOIN disputes disp ON disp.deduction_id = d.deduction_id
            WHERE d.deduction_type='slotting'
        """).fetchone()[0]
        if slotting_with_dispute == 0:
            rep.passed("Slotting deductions never have a dispute")
        else:
            rep.fail(f"{slotting_with_dispute} slotting deductions have disputes")

        # Recovery never exceeds deductions
        recovered = cur.execute("SELECT SUM(recovered_amount) FROM disputes").fetchone()[0] or 0
        if recovered <= total:
            rep.passed(f"Total recovered (${recovered:,.0f}) <= total deductions (${total:,.0f})")
        else:
            rep.fail(f"Total recovered (${recovered:,.0f}) EXCEEDS total deductions")

        # ===== Summary =====
        print()
        print("=" * 50)
        print(f"  PASS: {rep.pass_count}    WARN: {rep.warn_count}    FAIL: {rep.fail_count}")
        print("=" * 50)
    return 1 if rep.fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
