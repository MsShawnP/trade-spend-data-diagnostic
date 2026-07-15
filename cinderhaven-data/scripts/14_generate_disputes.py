"""Generate the `disputes` and `dispute_evidence` tables.

Models Cinderhaven's lean-team dispute reality:
  - Only ~50% of deductions get a dispute attempt at all (lower for
    small / vague / weak-evidence cases).
  - Filing date lags 7-60 days from deduction (paper retrieval takes
    time, dispute is rarely the urgent item on someone's desk).
  - Evidence quality is determined by what pack_records and shipments
    actually have on file: digital_complete is rare (only digital_log
    pack records), handwritten_only is the norm, none happens when
    paper is lost or no verification existed.
  - Outcomes branch on (evidence_quality × was_within_deadline ×
    retailer typical_recovery_rate) with realistic skew toward losses
    when evidence is weak or deadlines are missed.

dispute_evidence rows are generated alongside disputes — for each
required evidence type per retailer_rules, mark whether Cinderhaven
actually has it (looking at shipments.bol_signed, pod_received,
asn_sent, and pack_records.evidence_format/location).
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from shared import DB_PATH

SEED = 47

# Today / window-end — anything more recent should occasionally still be `pending`.
TODAY = date(2027, 1, 2)

# Filing rate: % of deductions that get a dispute attempt at all.
FILING_RATE = {
    "walmart":              0.65,
    "costco":               0.50,
    "whole_foods":          0.40,
    "unfi":                 0.55,
    "kehe":                 0.50,
    "kroger":               0.40,
    "sprouts":              0.40,
    "regional_group":       0.35,
}

FILING_METHOD = {
    "walmart": "portal", "costco": "portal", "kehe": "portal",
    "whole_foods": "email_excel", "unfi": "email_excel",
    "kroger": "email_buyer", "sprouts": "email_buyer",
    "regional_group": "email_buyer",
}


def determine_evidence_quality(rng: random.Random, evidence_format: str | None,
                               evidence_location: str | None) -> str:
    if evidence_format == "digital":
        return "digital_complete" if rng.random() < 0.85 else "digital_partial"
    if evidence_format == "paper_note":
        if evidence_location == "lost":
            return "none"
        return "handwritten_only"
    return "none"


def evidence_count_for(rng: random.Random, quality: str) -> int:
    if quality == "digital_complete":
        return rng.randint(3, 6)
    if quality == "digital_partial":
        return rng.randint(2, 4)
    if quality == "handwritten_only":
        return rng.randint(1, 3)
    return 0


def filing_lag_days(rng: random.Random) -> int:
    """Days from deduction_date to filed_date. Median ~25 days, long tail."""
    return max(1, int(rng.triangular(3, 90, 25)))


def determine_outcome(rng: random.Random, retailer_id: str, recovery_rate: float,
                       evidence_quality: str, was_within_deadline: int | None,
                       filed_date: date, deduction_amount: float) -> tuple[str, float]:
    """Return (outcome, recovered_amount)."""

    # Recent filings might still be pending (closed_date logic later)
    days_since_filing = (TODAY - filed_date).days
    if days_since_filing < 30 and rng.random() < 0.60:
        return "pending", 0.0

    # Filed past deadline → almost always lost_deadline
    if was_within_deadline == 0:
        r = rng.random()
        if r < 0.75:
            return "lost_deadline", 0.0
        if r < 0.90:
            return "lost_other", 0.0
        # Occasional partial recovery
        return "won_partial", round(deduction_amount * rng.uniform(0.2, 0.5), 2)

    # No evidence → almost always lost_evidence or abandoned
    if evidence_quality == "none":
        r = rng.random()
        if r < 0.70:
            return "lost_evidence", 0.0
        if r < 0.95:
            return "abandoned", 0.0
        return "lost_no_response", 0.0

    # Compute effective recovery rate with evidence modifiers
    effective = recovery_rate
    if evidence_quality == "digital_complete":
        effective = min(0.95, recovery_rate + 0.30)
    elif evidence_quality == "digital_partial":
        effective = min(0.85, recovery_rate + 0.10)
    elif evidence_quality == "handwritten_only":
        effective = max(0.05, recovery_rate - 0.05)

    r = rng.random()

    # Roll for win
    if r < effective * 0.70:
        return "won_full", round(deduction_amount, 2)
    if r < effective:
        partial_pct = rng.uniform(0.30, 0.70)
        return "won_partial", round(deduction_amount * partial_pct, 2)

    # Lost — distribute reasons
    loss_roll = rng.random()
    if evidence_quality == "handwritten_only" and loss_roll < 0.45:
        return "lost_evidence", 0.0
    if loss_roll < 0.65:
        return "lost_other", 0.0
    if loss_roll < 0.85:
        return "lost_no_response", 0.0
    return "abandoned", 0.0


def closed_date_for(rng: random.Random, outcome: str, filed_date: date) -> str | None:
    if outcome == "pending":
        return None
    if outcome == "abandoned":
        return (filed_date + timedelta(days=rng.randint(30, 60))).isoformat()
    return (filed_date + timedelta(days=rng.randint(21, 90))).isoformat()


def labor_hours_for(rng: random.Random, retrieval_minutes: int | None,
                    evidence_quality: str) -> float:
    base = rng.uniform(0.5, 1.5)
    retrieval = (retrieval_minutes or 0) / 60.0
    prep = {"digital_complete": 0.5, "digital_partial": 1.0,
            "handwritten_only": 1.5, "none": 2.0}[evidence_quality]
    response = rng.uniform(0.0, 1.5)
    total = base + retrieval + prep + response
    return round(total, 2)


# Map retailer_rules.evidence_required string -> ordered list of types
def parse_required(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def evidence_availability(evidence_type: str, pack_data: dict, ship_data: dict,
                          rng: random.Random) -> tuple[bool, str | None, str]:
    """Return (was_submitted, format, notes_template)."""
    if evidence_type == "signed_bol":
        if ship_data.get("bol_signed"):
            return True, "paper_scan", "BOL retained and scanned"
        return False, "missing", "BOL not retained — driver took it"
    if evidence_type == "pod":
        if ship_data.get("pod_received"):
            return True, "digital", "POD received from carrier"
        return False, "missing", "POD never received from carrier"
    if evidence_type == "pack_log":
        ef = pack_data.get("evidence_format")
        loc = pack_data.get("evidence_location")
        if ef == "digital":
            return True, "digital", "Digital pack log on file"
        if ef == "paper_note" and loc != "lost":
            return True, "handwritten_note", f"Handwritten pack note ({loc})"
        return False, "missing", "Pack log not retrievable"
    if evidence_type == "label_scan":
        if pack_data.get("label_scannable"):
            return True, "digital", "Compliant label image"
        return False, "missing", "Generic label — no scan record"
    if evidence_type == "asn_confirmation":
        if ship_data.get("asn_sent"):
            return True, "digital", "EDI 856 confirmation"
        return False, "missing", "ASN not sent"
    if evidence_type == "promo_agreement":
        if rng.random() < 0.40:
            return True, "digital", "Promo agreement email thread"
        return False, "missing", "Promo agreement not located"
    if evidence_type == "photo":
        if rng.random() < 0.15:
            return True, "digital", "Receiving photo (rare)"
        return False, "missing", "No photo taken at receiving"
    return False, "missing", ""


def main() -> None:
    rng = random.Random(SEED)
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        cur.execute("DELETE FROM dispute_evidence")
        cur.execute("DELETE FROM disputes")

        # Retailer rules → recovery rate + evidence required + dispute window
        rules: dict[tuple[str, str], dict] = {}
        for retailer_id, dt, window, evidence_req, recovery, _ in cur.execute("""
            SELECT retailer_id, deduction_type, dispute_window_days,
                   evidence_required, typical_recovery_rate, notes
            FROM retailer_rules
        """).fetchall():
            rules[(retailer_id, dt)] = {
                "window": window,
                "required": parse_required(evidence_req),
                "recovery": recovery or 0.30,
            }

        # Pull deductions joined to pack and shipment context
        rows = cur.execute("""
            SELECT
                d.deduction_id, d.retailer_id, d.deduction_type,
                d.amount, d.deduction_date, d.dispute_deadline,
                d.is_vague, d.order_id,
                s.bol_signed, s.bol_signed_short, s.bol_signed_damaged,
                s.pod_received, s.asn_sent,
                p.evidence_format, p.evidence_location,
                p.evidence_retrieval_minutes, p.label_scannable
            FROM deductions d
            LEFT JOIN shipments s ON s.shipment_id = d.shipment_id
            LEFT JOIN pack_records p ON p.order_id = d.order_id
        """).fetchall()

        dispute_rows = []
        evidence_rows = []
        seq = 0
        counters = {
            "filed": 0, "skipped": 0,
            "pending": 0, "won_full": 0, "won_partial": 0,
            "lost_evidence": 0, "lost_deadline": 0, "lost_no_response": 0,
            "lost_other": 0, "abandoned": 0,
        }

        for r in rows:
            (deduction_id, retailer_id, dt,
             amount, ded_date_str, deadline_str,
             is_vague, order_id,
             bol_signed, bol_short, bol_damaged, pod_received, asn_sent,
             evidence_format, evidence_location,
             retrieval_minutes, label_scannable) = r

            # Slotting is a negotiated cost, not an operational failure —
            # never disputed, never has evidence. Skip entirely.
            if dt == "slotting":
                counters["skipped"] += 1
                continue

            # Filing rate, with adjustments
            rate = FILING_RATE.get(retailer_id, 0.40)
            if amount < 100:
                rate -= 0.20
            if is_vague:
                rate -= 0.15
            if bol_signed == 0:
                rate -= 0.10
            if evidence_format == "none":
                rate -= 0.25
            rate = max(0.05, rate)

            if rng.random() >= rate:
                counters["skipped"] += 1
                continue

            ded_date = date.fromisoformat(ded_date_str)
            deadline = date.fromisoformat(deadline_str) if deadline_str else None
            lag = filing_lag_days(rng)
            filed_date = ded_date + timedelta(days=lag)
            if filed_date > TODAY:
                filed_date = TODAY

            was_within_deadline: int | None
            if deadline is not None:
                was_within_deadline = 1 if filed_date <= deadline else 0
            else:
                was_within_deadline = None

            # Evidence quality
            eq = determine_evidence_quality(rng, evidence_format, evidence_location)
            ec = evidence_count_for(rng, eq)

            rule = rules.get((retailer_id, dt), {"recovery": 0.30, "required": []})
            outcome, recovered = determine_outcome(
                rng, retailer_id, rule["recovery"], eq, was_within_deadline,
                filed_date, amount,
            )

            closed_date = closed_date_for(rng, outcome, filed_date)
            labor = labor_hours_for(rng, retrieval_minutes, eq)
            method = FILING_METHOD.get(retailer_id, "email_buyer")

            seq += 1
            dispute_id = f"DSP-{seq:07d}"
            dispute_rows.append((
                dispute_id, deduction_id,
                filed_date.isoformat(), method, eq, ec,
                was_within_deadline, outcome, recovered, closed_date, labor,
            ))
            counters["filed"] += 1
            counters[outcome] += 1

            # Evidence rows: one per required evidence type, plus 0-2 supporting
            pack_data = {
                "evidence_format": evidence_format,
                "evidence_location": evidence_location,
                "label_scannable": label_scannable,
            }
            ship_data = {
                "bol_signed": bol_signed,
                "pod_received": pod_received,
                "asn_sent": asn_sent,
            }

            seen_types: set[str] = set()
            for etype in rule["required"]:
                was_sub, fmt, notes = evidence_availability(etype, pack_data, ship_data, rng)
                evidence_rows.append((
                    dispute_id, etype,
                    1 if was_sub else 0, 1, fmt, notes,
                ))
                seen_types.add(etype)
            # Optional supporting items (occasional)
            if rng.random() < 0.25:
                extra = rng.choice(["photo", "asn_confirmation", "promo_agreement"])
                if extra not in seen_types:
                    was_sub, fmt, notes = evidence_availability(extra, pack_data, ship_data, rng)
                    evidence_rows.append((
                        dispute_id, extra,
                        1 if was_sub else 0, 0, fmt, notes,
                    ))

        cur.executemany("""
            INSERT INTO disputes (
                dispute_id, deduction_id, filed_date, filing_method,
                evidence_quality, submitted_evidence_count,
                was_within_deadline, outcome, recovered_amount,
                closed_date, labor_hours
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, dispute_rows)
        cur.executemany("""
            INSERT INTO dispute_evidence (
                dispute_id, evidence_type, was_submitted, was_required, format, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, evidence_rows)
        con.commit()

        n_disputes = counters["filed"]
        total_deductions = n_disputes + counters["skipped"]
        print(f"Inserted {n_disputes:,} disputes (out of {total_deductions:,} deductions; "
              f"{n_disputes/total_deductions:.1%} filing rate).")
        print(f"Inserted {len(evidence_rows):,} dispute_evidence rows.")
        print()
        print("Outcomes:")
        for k in ("won_full", "won_partial", "pending", "lost_evidence",
                  "lost_deadline", "lost_no_response", "lost_other", "abandoned"):
            v = counters[k]
            print(f"  {k:<18} {v:>5,}  ({v/n_disputes:.1%})")

        # Recovery $ by outcome
        print()
        print("Recovery dollars:")
        by_outcome = {}
        deduction_dollars = 0.0
        for d in dispute_rows:
            outcome = d[7]
            by_outcome[outcome] = by_outcome.get(outcome, 0.0) + (d[8] or 0)
        total_recovered = sum(by_outcome.values())
        deduction_dollars = sum(r[3] for r in rows)
        print(f"  Total deduction $:          ${deduction_dollars:>11,.0f}")
        print(f"  Total recovered:            ${total_recovered:>11,.0f}  ({total_recovered/deduction_dollars:.1%})")
        won_full_amt = by_outcome.get("won_full", 0)
        won_partial_amt = by_outcome.get("won_partial", 0)
        print(f"  Won full:                   ${won_full_amt:>11,.0f}")
        print(f"  Won partial:                ${won_partial_amt:>11,.0f}")

        print()
        print("Evidence quality distribution:")
        from collections import Counter
        eqc = Counter(d[4] for d in dispute_rows)
        for q in ("digital_complete", "digital_partial", "handwritten_only", "none"):
            v = eqc[q]
            print(f"  {q:<20} {v:>5,}  ({v/n_disputes:.1%})")

        deadline_missed = sum(1 for d in dispute_rows if d[6] == 0)
        deadline_met = sum(1 for d in dispute_rows if d[6] == 1)
        deadline_na = sum(1 for d in dispute_rows if d[6] is None)
        print()
        print(f"Deadline status: met {deadline_met:,}  missed {deadline_missed:,}  "
              f"no published window {deadline_na:,}")

        total_hours = sum(d[10] for d in dispute_rows)
        print(f"\nTotal labor hours on disputes: {total_hours:,.0f}  (~{total_hours/2080:.1f} FTE)")



if __name__ == "__main__":
    main()
