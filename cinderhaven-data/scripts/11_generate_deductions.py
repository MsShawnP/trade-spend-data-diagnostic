"""Generate the `deductions` table.

The central deduction record. Drives a realistic distribution of:
  - short_ship (correlates with bol_signed_short, pick_pack_mismatch,
    AND non-scannable labels at Walmart/Costco where receiving hand-
    counts and undercounts — the Code 22 perceived-shortage path)
  - label_fine (generic labels at strict retailers — SQEP-style)
  - pallet_fine (low base rate per retailer)
  - damaged (bol_signed_damaged drives most of these)
  - late_delivery (retailer-aware: only when delivery missed window
    AND sampled at late_pct so volume stays realistic)
  - promo_billback (random per retailer; tied to promo activity)
  - vague (Walmart Code 87/99 catch-all; MISC at others; opaque
    descriptions for the "vague/undecodable" feature)
  - spoilage (product-condition disputes at receiving — heat exposure,
    expiration, quality, damage-in-transit; shelf-stable catalog so no
    cold-chain; flows through the same failure pipeline)
  - slotting (negotiated cost — new-item / planogram / shelf placement
    fees; NOT an operational failure, generated as periodic per-retailer
    events outside the per-order loop, no order_id / shipment_id, no
    dispute_deadline, recovery_rate=0)

Volume target: $750K-$1.2M annualized (3-5% of $25M wholesale revenue).
Roughly 12,000-14,000 standard deductions over 36 months, plus ~50-70
slotting events.

Deduction date is set 14-45 days after delivery_date (retailer-aware
remittance cadence). dispute_deadline is calculated from
retailer_rules.dispute_window_days where published, NULL otherwise.

Post-audit deductions (is_post_audit=TRUE) are added by a separate
script (17_generate_post_audit_claims.py) — this generator only
produces standard deductions.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from shared import DB_PATH

SEED = 45

DATE_CAP = date(2027, 1, 2)

# Per-retailer deduction probability + amount config.
# rates: probability that THIS deduction type fires for an order, given
#   the necessary precondition (e.g., short_ship requires either bol-short,
#   pick/pack mismatch, or non-scannable label at strict retailers).
# Calibrated against $750K-$1.2M annualized volume target.
PROFILES = {
    # short_perceived: extra rate of perceived-shortage deductions when label
    # is non-scannable at strict retailers (Walmart Code 22 driver)
    # spoilage: per-order base rate of product-condition deductions
    # slotting_events: integer count of slotting events to generate per
    #   retailer across the data window (not per-order)
    # slotting_amount_range: (min, max) dollars per slotting event
    "walmart": {
        "short_ship_real":         0.85,   # of bol-short or pick-mismatch
        "short_ship_perceived":    0.45,   # of non-scannable-label orders
        "label_fine":              0.25,   # of generic-label orders (sampled)
        "pallet_fine":             0.04,
        "damaged":                 0.85,   # of bol-damaged
        "late_delivery_window":    0.55,   # of orders that missed window
        "promo_billback":          0.14,
        "vague":                   0.06,
        "spoilage":                0.05,
        "slotting_events":         3,
        "slotting_amount_range":   (5500, 13000),
        "remittance_lag":          (28, 42),
    },
    "costco": {
        "short_ship_real":         0.80,
        "short_ship_perceived":    0.30,
        "label_fine":              0.15,
        "pallet_fine":             0.06,
        "damaged":                 0.85,
        "late_delivery_window":    0.50,
        "promo_billback":          0.08,
        "vague":                   0.05,
        "spoilage":                0.045,
        "slotting_events":         3,
        "slotting_amount_range":   (8000, 18000),
        "remittance_lag":          (30, 45),
    },
    "whole_foods": {
        "short_ship_real":         0.65,
        "short_ship_perceived":    0.0,    # not strict-label
        "label_fine":              0.05,
        "pallet_fine":             0.02,
        "damaged":                 0.70,
        "late_delivery_window":    0.30,
        "promo_billback":          0.10,
        "vague":                   0.07,
        "spoilage":                0.05,
        "slotting_events":         4,
        "slotting_amount_range":   (3000, 6500),
        "remittance_lag":          (21, 35)
    },
    "unfi": {
        "short_ship_real":         0.70,
        "short_ship_perceived":    0.0,
        "label_fine":              0.05,
        "pallet_fine":             0.02,
        "damaged":                 0.65,
        "late_delivery_window":    0.30,
        "promo_billback":          0.18,   # MCB-heavy
        "vague":                   0.10,
        "spoilage":                0.05,
        "slotting_events":         5,
        "slotting_amount_range":   (2000, 4500),
        "remittance_lag":          (7, 21),  # weekly cadence
    },
    "kehe": {
        "short_ship_real":         0.85,   # 48hr UDR locks fast
        "short_ship_perceived":    0.0,
        "label_fine":              0.06,
        "pallet_fine":             0.02,
        "damaged":                 0.80,
        "late_delivery_window":    0.30,
        "promo_billback":          0.18,
        "vague":                   0.10,
        "spoilage":                0.04,
        "slotting_events":         5,
        "slotting_amount_range":   (1500, 3500),
        "remittance_lag":          (10, 21),  # biweekly
    },
    "kroger": {
        "short_ship_real":         0.55,
        "short_ship_perceived":    0.0,
        "label_fine":              0.03,
        "pallet_fine":             0.01,
        "damaged":                 0.55,
        "late_delivery_window":    0.20,
        "promo_billback":          0.08,
        "vague":                   0.06,
        "spoilage":                0.03,
        "slotting_events":         2,
        "slotting_amount_range":   (500, 1300),
        "remittance_lag":          (21, 40),
    },
    "sprouts": {
        "short_ship_real":         0.55,
        "short_ship_perceived":    0.0,
        "label_fine":              0.03,
        "pallet_fine":             0.01,
        "damaged":                 0.55,
        "late_delivery_window":    0.25,
        "promo_billback":          0.14,
        "vague":                   0.07,
        "spoilage":                0.03,
        "slotting_events":         3,
        "slotting_amount_range":   (400, 1100),
        "remittance_lag":          (21, 40),
    },
    "regional_group": {
        "short_ship_real":         0.55,
        "short_ship_perceived":    0.0,
        "label_fine":              0.03,
        "pallet_fine":             0.01,
        "damaged":                 0.55,
        "late_delivery_window":    0.25,
        "promo_billback":          0.04,
        "vague":                   0.04,
        "spoilage":                0.012,
        "slotting_events":         2,
        "slotting_amount_range":   (300, 850),
        "remittance_lag":          (21, 40),
    },
}

# Spoilage descriptions encode the sub-cause as a keyword the Sankey
# rootCauseFor function reads. Keep keywords stable: 'temperature',
# 'expired'/'short-dated', 'quality', 'damage in transit'.
# Cinderhaven's catalog is shelf-stable (sauces, condiments, pantry
# staples) — no cold chain. "Temperature" here means heat exposure
# degrading product condition, not refrigeration failure.
SPOILAGE_TEMPLATES = [
    "Spoilage — temperature exposure in transit",
    "Spoilage — expired or short-dated at receiving",
    "Spoilage — quality complaint at receiving",
    "Spoilage — damage in transit affecting condition",
]

SLOTTING_TEMPLATES = [
    "New-item slotting fee — placement allowance",
    "Planogram reset — placement billback",
    "Shelf placement / new-item program",
    "Category-reset placement billback",
]

# Vague deduction descriptions that read like real remittance lines —
# the "Code 99 / promo -$X with no PO reference" reality.
VAGUE_TEMPLATES = [
    "Code {code}: {label}",
    "Promo allowance",
    "Marketing chargeback",
    "Audit adjustment",
    "Misc deduction — see invoice",
    "Cash discount take-down",
    "Slotting reconciliation",
    "Trade spend true-up",
    "Allowance reconciliation",
    "Compliance fee",
]


def code_id_for(retailer_id: str, deduction_type: str, codes_by_retailer: dict) -> tuple[str | None, str]:
    """Pick a code_id and return (code_id, code_as_remitted)."""
    matches = [
        (cid, code) for (cid, code, dt) in codes_by_retailer.get(retailer_id, [])
        if dt == deduction_type
    ]
    if not matches:
        return None, ""
    cid, code = matches[0]
    return cid, code


def short_ship_amount(rng: random.Random, units_short: int, line_value_avg: float) -> float:
    """Dollar value of short ship — recoup of unsupplied units."""
    base = units_short * line_value_avg * rng.uniform(0.9, 1.05)
    return round(max(75.0, base), 2)


def label_fine_amount(rng: random.Random, retailer_id: str, total_units: int) -> float:
    """Walmart SQEP Phase 2: $200 admin + $1/case. Other retailers smaller."""
    if retailer_id == "walmart":
        return round(200.0 + total_units * rng.uniform(0.8, 1.2), 2)
    if retailer_id == "costco":
        return round(rng.uniform(50.0, 150.0) * max(1, total_units // 100), 2)
    return round(rng.uniform(75.0, 250.0), 2)


def pallet_fine_amount(rng: random.Random, retailer_id: str, pallets: int) -> float:
    if retailer_id == "walmart":
        return round(200.0 + pallets * rng.uniform(3.5, 4.5), 2)
    return round(rng.uniform(80.0, 220.0), 2)


def damaged_amount(rng: random.Random, total_value: float) -> float:
    """Damage refund — small percentage of order value (5-15%)."""
    return round(total_value * rng.uniform(0.05, 0.15), 2)


def late_amount(rng: random.Random, retailer_id: str, total_value: float) -> float:
    """Late-delivery / OTIF fines."""
    if retailer_id == "walmart":
        # Walmart OTIF: 3% of COGS (approximate as 3% of wholesale)
        return round(total_value * 0.03, 2)
    if retailer_id == "unfi":
        # UNFI flat fines: $250 late, $500 no-show
        return round(rng.choice([250.0, 250.0, 500.0]), 2)
    return round(total_value * rng.uniform(0.015, 0.03), 2)


def promo_amount(rng: random.Random, total_value: float) -> float:
    """Promo billback — 5-15% of order value."""
    return round(total_value * rng.uniform(0.05, 0.15), 2)


def vague_amount(rng: random.Random) -> float:
    """Vague deductions span small fees to mystery big-tickets."""
    if rng.random() < 0.6:
        return round(rng.uniform(50.0, 600.0), 2)
    return round(rng.uniform(800.0, 4500.0), 2)


def spoilage_amount(rng: random.Random, total_value: float) -> float:
    """Spoilage refund — partial credit for product condition issues at
    receiving. Typically 8-22% of order value (a portion of the order
    rejected, not the whole load)."""
    return round(total_value * rng.uniform(0.08, 0.22), 2)


def deduction_date_for(rng: random.Random, delivery_date: date, lag_range: tuple[int, int]) -> date:
    return delivery_date + timedelta(days=rng.randint(*lag_range))


def main() -> None:
    rng = random.Random(SEED)
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        cur.execute("DELETE FROM deductions")

        # Lookup tables
        codes_by_retailer: dict[str, list[tuple[str, str, str]]] = {}
        for cid, rid, code, dt in cur.execute(
            "SELECT code_id, retailer_id, code, deduction_type FROM deduction_codes"
        ).fetchall():
            codes_by_retailer.setdefault(rid, []).append((cid, code, dt))

        rules = {
            (rid, dt): (window, evidence)
            for rid, dt, window, evidence in cur.execute(
                "SELECT retailer_id, deduction_type, dispute_window_days, evidence_required FROM retailer_rules"
            ).fetchall()
        }

        # Pull denormalized order/shipment/pack data — one query, in-memory join
        rows = cur.execute("""
            SELECT
                o.order_id, o.retailer_id, o.total_units, o.total_value,
                o.requested_delivery_window_end,
                s.shipment_id, s.delivery_date, s.units_shipped,
                s.bol_signed_short, s.bol_signed_damaged, s.pallets_shipped,
                p.units_picked, p.units_packed, p.units_pick_pack_match,
                p.label_type_used, p.label_scannable
            FROM orders o
            JOIN shipments s ON s.order_id = o.order_id
            JOIN pack_records p ON p.order_id = o.order_id
        """).fetchall()

        deductions = []
        seq = 0
        counters = {k: 0 for k in (
            "short_ship", "label_fine", "pallet_fine", "damaged",
            "late_delivery", "promo_billback", "vague",
            "spoilage", "slotting",
        )}

        def add_deduction(retailer_id, dt, order_id, shipment_id, amount,
                          code_id, code_remitted, description,
                          deduction_dt, is_vague=0):
            nonlocal seq
            if deduction_dt > DATE_CAP:
                return
            seq += 1
            deduction_id = f"DED-{seq:07d}"
            window = rules.get((retailer_id, dt), (None, None))[0]
            deadline = (deduction_dt + timedelta(days=window)).isoformat() if window else None
            deductions.append((
                deduction_id, retailer_id, order_id, shipment_id, dt,
                code_id, code_remitted, description,
                amount, deduction_dt.isoformat(), deadline,
                is_vague, 0,  # is_post_audit
                0,  # is_double_dip
                None,  # remittance_id — populated later
            ))
            counters[dt] += 1

        for row in rows:
            (order_id, retailer_id, total_units, total_value,
             window_end_str,
             shipment_id, delivery_date_str, units_shipped,
             bol_short, bol_damaged, pallets,
             units_picked, units_packed, pick_pack_match,
             label_type, label_scannable) = row

            profile = PROFILES.get(retailer_id)
            if not profile:
                continue
            delivery_date = date.fromisoformat(delivery_date_str)
            window_end = date.fromisoformat(window_end_str) if window_end_str else None
            ded_dt = deduction_date_for(rng, delivery_date, profile["remittance_lag"])
            line_value_avg = total_value / max(1, total_units)

            # 1. SHORT SHIP — real (bol-short OR pick-mismatch)
            units_short = max(0, units_packed - units_shipped) + max(0, units_picked - units_packed)
            if (bol_short or not pick_pack_match) and rng.random() < profile["short_ship_real"]:
                cid, code = code_id_for(retailer_id, "short_ship", codes_by_retailer)
                amt = short_ship_amount(rng, max(units_short, 1), line_value_avg)
                add_deduction(retailer_id, "short_ship", order_id, shipment_id,
                              amt, cid, code,
                              f"Short ship: {units_short or 'qty'} units missing",
                              ded_dt)

            # 1b. SHORT SHIP — perceived (non-scannable label causes hand-count undercount)
            elif (label_scannable == 0 and rng.random() < profile["short_ship_perceived"]):
                cid, code = code_id_for(retailer_id, "short_ship", codes_by_retailer)
                phantom_short = rng.randint(2, max(3, total_units // 20))
                amt = short_ship_amount(rng, phantom_short, line_value_avg)
                add_deduction(retailer_id, "short_ship", order_id, shipment_id,
                              amt, cid, code,
                              f"Short ship: receiving hand-count {phantom_short} units short",
                              ded_dt)

            # 2. LABEL FINE — generic at strict retailer, sampled
            if label_type == "generic" and rng.random() < profile["label_fine"]:
                cid, code = code_id_for(retailer_id, "label_fine", codes_by_retailer)
                amt = label_fine_amount(rng, retailer_id, total_units)
                add_deduction(retailer_id, "label_fine", order_id, shipment_id,
                              amt, cid, code,
                              "Label noncompliance — generic label not retailer-spec",
                              ded_dt)

            # 3. PALLET FINE
            if rng.random() < profile["pallet_fine"]:
                cid, code = code_id_for(retailer_id, "pallet_fine", codes_by_retailer)
                amt = pallet_fine_amount(rng, retailer_id, pallets or 1)
                add_deduction(retailer_id, "pallet_fine", order_id, shipment_id,
                              amt, cid, code, "Pallet noncompliance", ded_dt)

            # 4. DAMAGED
            if bol_damaged and rng.random() < profile["damaged"]:
                cid, code = code_id_for(retailer_id, "damaged", codes_by_retailer)
                amt = damaged_amount(rng, total_value)
                add_deduction(retailer_id, "damaged", order_id, shipment_id,
                              amt, cid, code,
                              "Damage at receiving — BOL signed damaged",
                              ded_dt)

            # 5. LATE DELIVERY — must miss window AND be sampled
            if window_end and delivery_date > window_end:
                if rng.random() < profile["late_delivery_window"]:
                    cid, code = code_id_for(retailer_id, "late_delivery", codes_by_retailer)
                    amt = late_amount(rng, retailer_id, total_value)
                    days_late = (delivery_date - window_end).days
                    add_deduction(retailer_id, "late_delivery", order_id, shipment_id,
                                  amt, cid, code,
                                  f"Late delivery — {days_late} days past window",
                                  ded_dt)

            # 6. PROMO BILLBACK
            if rng.random() < profile["promo_billback"]:
                cid, code = code_id_for(retailer_id, "promo_billback", codes_by_retailer)
                amt = promo_amount(rng, total_value)
                add_deduction(retailer_id, "promo_billback", order_id, shipment_id,
                              amt, cid, code,
                              "Promo billback (MCB / scan-down)",
                              ded_dt)

            # 7. VAGUE — small base rate, opaque description, often no order linkage
            if rng.random() < profile["vague"]:
                cid, code = code_id_for(retailer_id, "vague", codes_by_retailer)
                amt = vague_amount(rng)
                template = rng.choice(VAGUE_TEMPLATES)
                description = template.format(code=rng.randint(85, 99), label="Other")
                # 30% of vague deductions have no order_id link (real remittances)
                link_order = order_id if rng.random() > 0.30 else None
                link_shipment = shipment_id if link_order else None
                add_deduction(retailer_id, "vague", link_order, link_shipment,
                              amt, cid, code, description, ded_dt, is_vague=1)

            # 8. SPOILAGE — product-condition disputes at receiving. Flows
            # through the same failure pipeline as the other operational
            # types (root cause derived from the description keyword).
            if rng.random() < profile["spoilage"]:
                cid, code = code_id_for(retailer_id, "spoilage", codes_by_retailer)
                amt = spoilage_amount(rng, total_value)
                description = rng.choice(SPOILAGE_TEMPLATES)
                add_deduction(retailer_id, "spoilage", order_id, shipment_id,
                              amt, cid, code, description, ded_dt)

        # 9. SLOTTING — periodic, not order-tied. Negotiated cost, not an
        # operational failure. No order_id, no shipment_id, no dispute window.
        # Spread N events per retailer evenly across the order date window.
        window = cur.execute(
            "SELECT MIN(po_date), MAX(po_date) FROM orders"
        ).fetchone()
        if window and window[0] and window[1]:
            ws = date.fromisoformat(window[0])
            we = date.fromisoformat(window[1])
            total_days = max(1, (we - ws).days)
            for retailer_id, profile in PROFILES.items():
                n_events = profile["slotting_events"]
                amount_lo, amount_hi = profile["slotting_amount_range"]
                cid, code = code_id_for(retailer_id, "slotting", codes_by_retailer)
                for i in range(n_events):
                    # Even spread with jitter so events don't cluster on day 0
                    frac = (i + 0.5) / n_events + rng.uniform(-0.25, 0.25) / n_events
                    frac = max(0.0, min(0.999, frac))
                    ded_dt = ws + timedelta(days=int(frac * total_days))
                    if ded_dt > DATE_CAP:
                        continue
                    amt = round(rng.uniform(amount_lo, amount_hi), 2)
                    description = rng.choice(SLOTTING_TEMPLATES)
                    seq += 1
                    deduction_id = f"DED-{seq:07d}"
                    deductions.append((
                        deduction_id, retailer_id, None, None, "slotting",
                        cid, code, description,
                        amt, ded_dt.isoformat(), None,  # dispute_deadline NULL
                        0, 0,  # is_vague=0, is_post_audit=0
                        0,  # is_double_dip
                        None,  # remittance_id populated later
                    ))
                    counters["slotting"] += 1

        cur.executemany("""
            INSERT INTO deductions (
                deduction_id, retailer_id, order_id, shipment_id, deduction_type,
                code_id, code_as_remitted, remittance_description,
                amount, deduction_date, dispute_deadline,
                is_vague, is_post_audit, is_double_dip, remittance_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, deductions)
        con.commit()

        # --- DOUBLE-DIP SEEDING ---
        # Find promotions funded via off_invoice and create 2-3 scan_down
        # deductions for the same SKU/retailer/time window. These are cases
        # where the retailer already received a price reduction on the invoice
        # AND is now claiming a promo billback for the same event.
        promo_rows = cur.execute("""
            SELECT p.promo_id, p.sku, p.retailer, p.start_week, p.end_week,
                   p.discount_depth_pct, p.funding_mechanism
            FROM promotions p
            WHERE p.funding_mechanism = 'off_invoice'
              AND p.retailer IN ('Walmart', 'UNFI', 'Whole Foods', 'Costco')
            ORDER BY p.start_week
            LIMIT 10
        """).fetchall()

        double_dip_ids = []
        dd_total = 0.0
        dd_target_hi = 20000.0
        dd_per_deduction = [6500.0, 7200.0, 5800.0]

        for idx, promo_row in enumerate(promo_rows):
            if len(double_dip_ids) >= 3 or dd_total >= dd_target_hi:
                break
            promo_id, sku, retailer_name, start_wk, end_wk, depth, _ = promo_row
            retailer_slug = None
            for rid, rname in cur.execute("SELECT retailer_id, name FROM retailers").fetchall():
                if rname == retailer_name:
                    retailer_slug = rid
                    break
            if not retailer_slug:
                continue
            price_row = cur.execute(
                "SELECT unit_price FROM order_lines WHERE sku = ? LIMIT 1", (sku,)
            ).fetchone()
            if not price_row:
                continue
            # Target $5K-$7.5K per double-dip: represents a multi-week,
            # multi-store scan-back claim on a SKU that already had off_invoice
            amt = round(dd_per_deduction[len(double_dip_ids)] * rng.uniform(0.95, 1.05), 2)
            if dd_total + amt > dd_target_hi:
                amt = round(dd_target_hi - dd_total, 2)
            if amt < 2000:
                continue

            # Create the double-dip deduction
            ded_date = date.fromisoformat(start_wk) + timedelta(days=rng.randint(14, 35))
            if ded_date > DATE_CAP:
                ded_date = DATE_CAP - timedelta(days=rng.randint(1, 14))
            seq += 1
            deduction_id = f"DED-{seq:07d}"
            cid_row = cur.execute(
                "SELECT code_id, code FROM deduction_codes"
                " WHERE retailer_id = ? AND deduction_type = 'promo_billback' LIMIT 1",
                (retailer_slug,)
            ).fetchone()
            code_id = cid_row[0] if cid_row else None
            code_remitted = cid_row[1] if cid_row else ""
            description = f"Scan-back: {sku} — TPR wk {start_wk}"
            window_days = rules.get((retailer_slug, "promo_billback"), (None, None))[0]
            deadline = (ded_date + timedelta(days=window_days)).isoformat() if window_days else None

            cur.execute("""
                INSERT INTO deductions (
                    deduction_id, retailer_id, order_id, shipment_id, deduction_type,
                    code_id, code_as_remitted, remittance_description,
                    amount, deduction_date, dispute_deadline,
                    is_vague, is_post_audit, is_double_dip, remittance_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deduction_id, retailer_slug, None, None, "promo_billback",
                code_id, code_remitted, description,
                amt, ded_date.isoformat(), deadline,
                0, 0, 1,  # is_double_dip = TRUE
                None,
            ))
            double_dip_ids.append(deduction_id)
            dd_total += amt
            counters["promo_billback"] += 1

        con.commit()
        print(f"\nDouble-dip deductions seeded: {len(double_dip_ids)}, total ${dd_total:,.0f}")
        for did in double_dip_ids:
            row = cur.execute(
                "SELECT deduction_id, amount, remittance_description FROM deductions WHERE deduction_id = ?",
                (did,)
            ).fetchone()
            print(f"  {row[0]}  ${row[1]:,.2f}  {row[2]}")

        # Summary
        n = len(deductions)
        total = sum(d[8] for d in deductions)
        months = 36
        annualized = total * 12 / months

        print(f"Inserted {n:,} deductions.")
        print(f"Total deduction value: ${total:,.0f}")
        print(f"Annualized:            ${annualized:,.0f}  (target $750K-$1.2M)")
        print()
        print("By type:")
        type_amounts: dict[str, float] = {}
        for d in deductions:
            type_amounts[d[4]] = type_amounts.get(d[4], 0.0) + d[8]
        for dt, count in sorted(counters.items(), key=lambda x: -x[1]):
            amt = type_amounts.get(dt, 0)
            print(f"  {dt:<16} {count:>5,}  ${amt:>10,.0f}")
        print()
        print("By retailer:")
        by_ret_count: dict[str, int] = {}
        by_ret_amt: dict[str, float] = {}
        for d in deductions:
            by_ret_count[d[1]] = by_ret_count.get(d[1], 0) + 1
            by_ret_amt[d[1]] = by_ret_amt.get(d[1], 0.0) + d[8]
        for slug in PROFILES:
            c = by_ret_count.get(slug, 0)
            a = by_ret_amt.get(slug, 0)
            print(f"  {slug:<22} {c:>5,}  ${a:>10,.0f}")

        # Sanity: vague + post-audit visibility
        vague_n = sum(1 for d in deductions if d[11])
        no_order = sum(1 for d in deductions if d[2] is None)
        print(f"\nVague deductions:   {vague_n:,}")
        print(f"With no PO link:    {no_order:,} ({no_order/n:.1%})")



if __name__ == "__main__":
    main()
