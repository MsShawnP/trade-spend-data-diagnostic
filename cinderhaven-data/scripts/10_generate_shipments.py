"""Generate the `shipments` table and link them back to pack_records.

One shipment per order (V1: 1:1). Models on-time delivery realistically:
Walmart's OTIF program is tight; Costco's 30-minute grace at depot is
strict; UNFI/KeHE/regional are looser. Late-delivery rates here drive
downstream `late_delivery` deductions.

ASN timing is also retailer-aware — strict retailers see more
ASN-sent-late events, which surface as ASN chargebacks at Walmart and
Amazon-style ones at the natural-foods distributors.

Short-ship and damage at the BOL level are seeded here so the
deduction generator can correlate them with Code 22 / 24 / 28.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from shared import DB_PATH

SEED = 44

CARRIERS = ["CH Robinson", "FedEx Freight", "Estes", "Old Dominion", "Saia", "XPO"]
UNITS_PER_PALLET = 72  # rough average across SKUs

# Retailer-specific operational profiles. Higher rates drive richer
# downstream deductions. Calibrated against the 5-failures narrative —
# Walmart OTIF is the most painful, KeHE UDR the strictest at receipt.
PROFILES = {
    "walmart":              {"late_pct": 0.14, "short_pct": 0.10, "dmg_pct": 0.03, "asn_late_pct": 0.20, "pod_pct": 0.85, "transit": (2, 5)},
    "costco":               {"late_pct": 0.10, "short_pct": 0.06, "dmg_pct": 0.04, "asn_late_pct": 0.15, "pod_pct": 0.85, "transit": (2, 6)},
    "whole_foods":          {"late_pct": 0.12, "short_pct": 0.08, "dmg_pct": 0.04, "asn_late_pct": 0.18, "pod_pct": 0.75, "transit": (2, 6)},
    "unfi":                 {"late_pct": 0.18, "short_pct": 0.09, "dmg_pct": 0.05, "asn_late_pct": 0.22, "pod_pct": 0.70, "transit": (2, 7)},
    "kehe":                 {"late_pct": 0.16, "short_pct": 0.09, "dmg_pct": 0.05, "asn_late_pct": 0.20, "pod_pct": 0.70, "transit": (2, 7)},
    "kroger":               {"late_pct": 0.12, "short_pct": 0.07, "dmg_pct": 0.03, "asn_late_pct": 0.10, "pod_pct": 0.75, "transit": (1, 4)},
    "sprouts":              {"late_pct": 0.15, "short_pct": 0.07, "dmg_pct": 0.03, "asn_late_pct": 0.12, "pod_pct": 0.70, "transit": (2, 5)},
    "regional_group":       {"late_pct": 0.13, "short_pct": 0.08, "dmg_pct": 0.04, "asn_late_pct": 0.15, "pod_pct": 0.70, "transit": (2, 5)},
}


def main() -> None:
    rng = random.Random(SEED)
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        cur.execute("DELETE FROM shipments")

        rows = cur.execute("""
            SELECT o.order_id, o.retailer_id, o.requested_ship_date,
                   o.requested_delivery_window_start, o.requested_delivery_window_end,
                   p.units_packed, p.pack_date
            FROM orders o
            JOIN pack_records p ON p.order_id = o.order_id
            ORDER BY o.order_id
        """).fetchall()

        shipment_rows = []
        pack_link_updates = []
        counters = {
            "late": 0, "short": 0, "damage": 0, "asn_late": 0, "no_pod": 0, "no_asn": 0,
        }

        for (order_id, retailer_id, requested_ship_str, win_start_str, win_end_str,
             units_packed, pack_date_str) in rows:
            profile = PROFILES.get(retailer_id, PROFILES["walmart"])
            requested_ship = date.fromisoformat(requested_ship_str)

            # Ship date: usually within 1 day of requested_ship; occasionally late
            ship_offset = rng.choices([-1, 0, 0, 0, 1, 2, 3, 5], weights=[5, 35, 25, 15, 10, 5, 3, 2])[0]
            ship_date = requested_ship + timedelta(days=ship_offset)

            # Delivery: ship + transit
            t_min, t_max = profile["transit"]
            transit_days = rng.randint(t_min, t_max)
            # Add late jitter for the late_pct of shipments
            if rng.random() < profile["late_pct"]:
                transit_days += rng.randint(2, 6)
                counters["late"] += 1
            delivery_date = ship_date + timedelta(days=transit_days)

            # Short-ship (units_shipped < units_packed)
            units_shipped = units_packed
            bol_signed_short = 0
            if rng.random() < profile["short_pct"]:
                short_amount = rng.randint(1, max(2, units_packed // 25))
                units_shipped = max(1, units_packed - short_amount)
                bol_signed_short = 1
                counters["short"] += 1

            # Damage
            bol_signed_damaged = 0
            if rng.random() < profile["dmg_pct"]:
                bol_signed_damaged = 1
                counters["damage"] += 1

            # BOL signed: 92% (lean ops; some BOLs not retained)
            bol_signed = 1 if rng.random() < 0.92 else 0

            # POD received: retailer-dependent
            pod_received = 1 if rng.random() < profile["pod_pct"] else 0
            if not pod_received:
                counters["no_pod"] += 1

            # ASN: 90% sent (small % skip ASN, esp at smaller retailers)
            asn_sent = 1 if rng.random() < 0.92 else 0
            asn_sent_late = 0
            if asn_sent and rng.random() < profile["asn_late_pct"]:
                asn_sent_late = 1
                counters["asn_late"] += 1
            if not asn_sent:
                counters["no_asn"] += 1

            # Pallets
            pallets_shipped = max(1, (units_shipped + UNITS_PER_PALLET - 1) // UNITS_PER_PALLET)

            carrier = rng.choice(CARRIERS)
            shipment_id = f"{order_id}-S1"
            bol_number = f"BOL-{shipment_id}"

            shipment_rows.append((
                shipment_id, order_id,
                ship_date.isoformat(),
                delivery_date.isoformat(),
                carrier, bol_number,
                bol_signed, bol_signed_short, bol_signed_damaged, pod_received,
                units_shipped, pallets_shipped,
                asn_sent, asn_sent_late,
            ))
            pack_link_updates.append((shipment_id, order_id))

        cur.executemany("""
            INSERT INTO shipments (
                shipment_id, order_id, ship_date, delivery_date, carrier,
                bol_number, bol_signed, bol_signed_short, bol_signed_damaged,
                pod_received, units_shipped, pallets_shipped,
                asn_sent, asn_sent_late
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, shipment_rows)

        cur.executemany("""
            UPDATE pack_records SET shipment_id = ? WHERE order_id = ?
        """, pack_link_updates)

        con.commit()

        n = len(shipment_rows)
        print(f"Inserted {n:,} shipments and linked them to pack_records.")
        print()
        print("Operational issues seeded:")
        for k, v in counters.items():
            print(f"  {k:<10} {v:>5,}  ({v / n:.1%})")

        print("\nLate delivery vs. requested window (sanity check):")
        for retailer in ["walmart", "kehe", "unfi"]:
            late_count = cur.execute("""
                SELECT COUNT(*)
                FROM shipments s
                JOIN orders o ON o.order_id = s.order_id
                WHERE o.retailer_id = ?
                  AND o.requested_delivery_window_end IS NOT NULL
                  AND s.delivery_date > o.requested_delivery_window_end
            """, (retailer,)).fetchone()[0]
            total = cur.execute(
                "SELECT COUNT(*) FROM orders WHERE retailer_id = ?", (retailer,)
            ).fetchone()[0]
            print(f"  {retailer:<10} {late_count:>5}/{total} late ({late_count/total:.1%})")



if __name__ == "__main__":
    main()
