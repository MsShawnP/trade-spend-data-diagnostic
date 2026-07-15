"""Generate the `pack_records` table.

One pack record per order. Models the operational reality at
Cinderhaven: nearly all orders use a single generic label (not
retailer-compliant), pack verification is handwritten paper notes,
and evidence retrieval is time-consuming.

Per CLAUDE.md: Cinderhaven uses one generic label across all
retailers instead of retailer-specific compliant labels, and pack
verification is handwritten — not digital. This generator encodes
those realities so downstream deduction generation can branch on
label_scannable and evidence quality.

shipment_id is left NULL here and populated when shipments are
generated in 12_generate_shipments.py.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from shared import DB_PATH

SEED = 43

PACKERS = ["JM", "RS", "AT", "KP", "DL", "EB", "TC"]

# Retailers that require a retailer-specific compliant label. If Cinderhaven
# uses generic, the label is non-scannable at receiving and drives Code-22-
# style perceived shortages.
STRICT_LABEL_RETAILERS = {"walmart", "costco"}

# Label compliance distribution at Cinderhaven: overwhelmingly generic.
# 8% of orders use a retailer-compliant label (occasional ad-hoc attempts;
# the project's "what fixing this is worth" simulation needs both groups).
LABEL_GENERIC_PROB = 0.92

# Pack verification distribution. Handwritten paper notes dominate; digital
# logs are rare and recent (modeled stochastically here, not date-aware).
VERIFICATION_DIST = [
    ("paper_note", 0.75),
    ("none",       0.20),
    ("digital_log", 0.05),
]

# Pick / pack mismatch probability. When mismatch occurs, packed differs
# from picked by 1-4 units. This is the "the warehouse made a counting
# error" path that surfaces as a shortage even when paperwork looks clean.
PICK_PACK_MISMATCH_PROB = 0.06


def weighted_choice(rng: random.Random, choices: list[tuple[str, float]]) -> str:
    r = rng.random()
    cum = 0.0
    for v, w in choices:
        cum += w
        if r <= cum:
            return v
    return choices[-1][0]


def evidence_for(
    rng: random.Random, verification: str, pack_dt: date, today: date,
) -> tuple[str, str | None, int | None]:
    """Returns (evidence_format, evidence_location, retrieval_minutes)."""
    age_days = (today - pack_dt).days

    if verification == "none":
        return "none", None, None
    if verification == "digital_log":
        return "digital", "system", rng.randint(2, 8)

    # paper_note
    if age_days < 60:
        loc = "warehouse_clipboard"
        mins = rng.randint(15, 35)
    elif age_days < 180:
        loc = "office_filing_cabinet"
        mins = rng.randint(30, 75)
    else:
        # Older paper goes deeper, some lost
        if rng.random() < 0.10:
            return "paper_note", "lost", None
        loc = "office_filing_cabinet"
        mins = rng.randint(45, 120)
    return "paper_note", loc, mins


def main() -> None:
    rng = random.Random(SEED)
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        cur.execute("DELETE FROM pack_records")

        today = date(2027, 1, 2)  # end of window — drives "age" for evidence-location

        rows = cur.execute("""
            SELECT order_id, retailer_id, requested_ship_date, total_units
            FROM orders
            ORDER BY order_id
        """).fetchall()

        pack_rows = []
        for order_id, retailer_id, requested_ship_str, total_units in rows:
            requested_ship = date.fromisoformat(requested_ship_str)
            # Pack 1-3 days before requested ship
            pack_dt = requested_ship - timedelta(days=rng.randint(1, 3))

            # Label compliance
            if rng.random() < LABEL_GENERIC_PROB:
                label_type = "generic"
            else:
                # Retailer-compliant: name follows retailer slug
                label_type = f"{retailer_id}_compliant"

            # Scannability: generic-on-strict-retailer is non-scannable
            if label_type == "generic" and retailer_id in STRICT_LABEL_RETAILERS:
                label_scannable = 0
            else:
                label_scannable = 1

            # Pick / pack quantities
            units_picked = total_units
            if rng.random() < PICK_PACK_MISMATCH_PROB:
                delta = rng.randint(1, max(2, total_units // 30))
                # Mismatch can go either way, but short-pack is more common (favor short)
                if rng.random() < 0.7:
                    units_packed = units_picked - delta
                else:
                    units_packed = units_picked + delta
                pick_pack_match = 0
            else:
                units_packed = units_picked
                pick_pack_match = 1

            # Pack verification
            verification = weighted_choice(rng, VERIFICATION_DIST)
            evidence_format, evidence_location, retrieval_minutes = evidence_for(
                rng, verification, pack_dt, today
            )

            packer = rng.choice(PACKERS)

            pack_rows.append((
                order_id,
                None,  # shipment_id — populated by 12_generate_shipments
                pack_dt.isoformat(),
                packer,
                units_picked,
                units_packed,
                pick_pack_match,
                label_type,
                label_scannable,
                verification,
                evidence_format,
                evidence_location,
                retrieval_minutes,
            ))

        cur.executemany("""
            INSERT INTO pack_records (
                order_id, shipment_id, pack_date, packer_initials,
                units_picked, units_packed, units_pick_pack_match,
                label_type_used, label_scannable, pack_verification,
                evidence_format, evidence_location, evidence_retrieval_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, pack_rows)
        con.commit()

        # Summary
        print(f"Inserted {len(pack_rows):,} pack_records.")

        print("\nLabel compliance:")
        print("  generic:          ", sum(1 for r in pack_rows if r[7] == "generic"))
        print("  retailer-compliant:", sum(1 for r in pack_rows if r[7] != "generic"))

        non_scan = sum(1 for r in pack_rows if not r[8])
        print(f"\nNon-scannable labels: {non_scan:,} ({non_scan / len(pack_rows):.1%})")
        print("  — these drive Code-22-style perceived shortages at Walmart/Costco")

        print("\nPack verification:")
        from collections import Counter
        vc = Counter(r[9] for r in pack_rows)
        for v, n in vc.most_common():
            print(f"  {v:<14} {n:>5,}  ({n / len(pack_rows):.1%})")

        print("\nEvidence accessibility:")
        loc = Counter(r[11] for r in pack_rows)
        for l, n in loc.most_common():
            label = l if l is not None else "(none — no verification)"
            print(f"  {label:<28} {n:>5,}  ({n / len(pack_rows):.1%})")

        mismatches = sum(1 for r in pack_rows if not r[6])
        print(f"\nPick/pack mismatches: {mismatches:,} ({mismatches / len(pack_rows):.1%})")



if __name__ == "__main__":
    main()
