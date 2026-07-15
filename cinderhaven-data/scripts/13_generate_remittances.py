"""Generate the `remittances` table and link deductions to them.

Bundles deductions into payment events. Each remittance covers all
deductions for a (retailer, week) bucket — rough proxy for real
weekly/biweekly retailer remittance cadence.

Format varies by retailer (EDI 820 for the big ones, portal download
for UNFI/WFM, paper check / email PDF for some regional chains).

Clarity tracks how many vague deductions are bundled — `clear` if
none, `partial` if a few, `opaque` if vague dominates. The "opaque"
remittances are exactly the kind a lean team can't decode without
investigation.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from shared import DB_PATH

FORMAT_BY_RETAILER = {
    "walmart": "edi_820",
    "costco": "edi_820",
    "whole_foods": "portal_download",
    "unfi": "portal_download",
    "kehe": "edi_820",
    "kroger": "paper_check",
    "sprouts": "email_pdf",
    "regional_group": "email_pdf",
}


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        cur.execute("DELETE FROM remittances")
        cur.execute("UPDATE deductions SET remittance_id = NULL")

        # Pull deductions with order info for gross calculation
        rows = cur.execute("""
            SELECT d.deduction_id, d.retailer_id, d.deduction_date,
                   d.amount, d.is_vague, d.order_id,
                   o.total_value
            FROM deductions d
            LEFT JOIN orders o ON o.order_id = d.order_id
        """).fetchall()

        # Group by (retailer, week)
        groups: dict[tuple[str, date], list[tuple]] = {}
        for r in rows:
            retailer = r[1]
            ddate = date.fromisoformat(r[2])
            wk = week_start(ddate)
            groups.setdefault((retailer, wk), []).append(r)

        rem_rows = []
        deduction_to_rem: list[tuple[str, str]] = []
        seq_by_retailer: dict[str, int] = {}

        for (retailer, wk), items in sorted(groups.items()):
            seq_by_retailer[retailer] = seq_by_retailer.get(retailer, 0) + 1
            seq = seq_by_retailer[retailer]
            rem_id = f"REM-{retailer.upper()[:4]}-{seq:05d}"

            # Received date: end of the week
            received = wk + timedelta(days=6)

            # Total deductions
            total_deductions = sum(item[3] for item in items)

            # Gross amount: sum of unique linked order values + proxy for vague-no-order
            unique_orders: dict[str, float] = {}
            vague_no_order_total = 0.0
            for item in items:
                order_id = item[5]
                order_value = item[6]
                if order_id and order_value is not None:
                    unique_orders[order_id] = order_value
                elif item[4]:  # is_vague with no order link
                    # Proxy: assume vague deductions are ~3% of gross, so gross = 33x
                    vague_no_order_total += item[3] * 33.0
            gross = sum(unique_orders.values()) + vague_no_order_total
            # Floor: gross must be >= total_deductions
            gross = max(gross, total_deductions * 1.05)
            net = gross - total_deductions

            # Clarity
            n_vague = sum(1 for item in items if item[4])
            n_total = len(items)
            if n_vague == 0:
                clarity = "clear"
            elif n_vague / n_total >= 0.5:
                clarity = "opaque"
            else:
                clarity = "partial"

            fmt = FORMAT_BY_RETAILER.get(retailer, "email_pdf")

            rem_rows.append((
                rem_id, retailer, received.isoformat(), fmt,
                round(gross, 2), round(net, 2), round(total_deductions, 2),
                clarity,
            ))
            for item in items:
                deduction_to_rem.append((rem_id, item[0]))

        cur.executemany("""
            INSERT INTO remittances (
                remittance_id, retailer_id, received_date, format,
                gross_amount, net_amount, total_deductions, clarity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rem_rows)
        cur.executemany(
            "UPDATE deductions SET remittance_id = ? WHERE deduction_id = ?",
            deduction_to_rem,
        )
        con.commit()

        n = len(rem_rows)
        total_gross = sum(r[4] for r in rem_rows)
        total_net = sum(r[5] for r in rem_rows)
        total_ded = sum(r[6] for r in rem_rows)

        print(f"Inserted {n:,} remittances.")
        print(f"Total gross:     ${total_gross:>13,.0f}")
        print(f"Total net paid:  ${total_net:>13,.0f}")
        print(f"Total deductions:${total_ded:>13,.0f}  ({total_ded/total_gross:.1%} of gross)")
        print()
        print("By format:")
        from collections import Counter
        fc = Counter(r[3] for r in rem_rows)
        for f, c in fc.most_common():
            print(f"  {f:<18} {c:>5,}")
        print()
        print("By clarity:")
        cc = Counter(r[7] for r in rem_rows)
        for c_label, c in cc.most_common():
            print(f"  {c_label:<10} {c:>5,}  ({c/n:.1%})")

        # Verify all deductions linked
        orphan = cur.execute(
            "SELECT COUNT(*) FROM deductions WHERE remittance_id IS NULL"
        ).fetchone()[0]
        print(f"\nOrphan deductions (no remittance): {orphan}")



if __name__ == "__main__":
    main()
