"""Generate the `post_audit_claims` table and the post-audit deductions
that go with them.

Adds *new* rows to `deductions` (with is_post_audit=TRUE) and a
companion enrichment row in `post_audit_claims`. These deductions
have order_id / shipment_id = NULL — post-audit claims are
retroactive and don't link to a specific PO.

After running this script, re-run scripts 14 and 15 so the new
deductions are bundled into remittances and surface in disputes.

Auditor and lookback realism (from research/retailers/):
  - Walmart: Audit Partners Limited (APL) since Feb 2025; 2-year
    lookback after audited calendar year.
  - Costco: not publicly named; 3-year lookback per Basic Supplier
    Agreement.
  - KeHE: pass-through from retailer audits, can extend beyond 2-year.
  - UNFI: third-party post-audit firms, 2-3 year lookback.

Volume target: 30-80 post-audit deductions across the 18-month window,
clustered in 2026 (the recent half) since audits look back.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from shared import DB_PATH

SEED = 48

DATE_CAP = date(2027, 1, 2)

# Per-retailer audit profile.
#   audits: number of distinct audit events to seed
#   ds_per_audit: (min, max) deductions per audit
#   amount_range: (min, max) dollar value per deduction
#   auditor: name string (NULL for retailer self-audit)
#   lookback_months_range: (min, max) months between audit_period_end and deduction_date
PROFILES = {
    "walmart": {
        "audits": 8, "ds_per_audit": (1, 3),
        "amount_range": (500, 15000),
        "auditor": "Audit Partners Limited",
        "lookback_months_range": (12, 24),
    },
    "costco": {
        "audits": 4, "ds_per_audit": (1, 2),
        "amount_range": (800, 18000),
        "auditor": None,
        "lookback_months_range": (18, 36),
    },
    "kehe": {
        "audits": 5, "ds_per_audit": (1, 3),
        "amount_range": (300, 8000),
        "auditor": "Cotiviti",
        "lookback_months_range": (12, 24),
    },
    "unfi": {
        "audits": 5, "ds_per_audit": (1, 3),
        "amount_range": (300, 7000),
        "auditor": "Cotiviti",
        "lookback_months_range": (15, 30),
    },
}

# Map claim_type to a deduction_type for our taxonomy
CLAIM_TO_DEDUCTION = {
    "pricing":    "promo_billback",
    "allowance":  "promo_billback",
    "freight":    "vague",
    "compliance": "label_fine",
}

REMITTANCE_LAG = (28, 45)  # post-audit deductions hit on later remittances


def main() -> None:
    rng = random.Random(SEED)
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        cur.execute("DELETE FROM post_audit_claims")
        cur.execute("DELETE FROM deductions WHERE is_post_audit = 1")

        # Look up codes per retailer
        codes_by_retailer: dict[str, dict[str, tuple[str, str]]] = {}
        for cid, rid, code, dt in cur.execute(
            "SELECT code_id, retailer_id, code, deduction_type FROM deduction_codes"
        ).fetchall():
            codes_by_retailer.setdefault(rid, {})[dt] = (cid, code)

        rules = {
            (rid, dt): window
            for rid, dt, window in cur.execute(
                "SELECT retailer_id, deduction_type, dispute_window_days FROM retailer_rules"
            ).fetchall()
        }

        # Find current max deduction_id seq to continue numbering
        max_seq = cur.execute(
            "SELECT MAX(CAST(SUBSTR(deduction_id, 5) AS INTEGER)) FROM deductions"
        ).fetchone()[0] or 0

        deduction_rows = []
        claim_rows = []
        claim_seq = 0

        for retailer_id, profile in PROFILES.items():
            for _ in range(profile["audits"]):
                # Audit period: 6-12 months wide, ending 12-30 months before now
                audit_period_end_offset = rng.randint(*profile["lookback_months_range"])
                audit_period_end = date(2027, 1, 1) - timedelta(days=audit_period_end_offset * 30)
                period_width = rng.randint(180, 365)
                audit_period_start = audit_period_end - timedelta(days=period_width)

                # The post-audit deductions hit Cinderhaven in 2026 (recent)
                # Spread across Jun-Dec 2026
                audit_hit_month = rng.randint(6, 12)
                audit_hit_day = rng.randint(1, 28)
                audit_hit_date = date(2026, audit_hit_month, audit_hit_day)

                n_deductions = rng.randint(*profile["ds_per_audit"])
                claim_type = rng.choice(list(CLAIM_TO_DEDUCTION.keys()))
                deduction_type = CLAIM_TO_DEDUCTION[claim_type]

                for _ in range(n_deductions):
                    max_seq += 1
                    deduction_id = f"DED-{max_seq:07d}"
                    amount = round(rng.uniform(*profile["amount_range"]), 2)
                    ded_date = audit_hit_date + timedelta(days=rng.randint(0, 14))
                    if ded_date > DATE_CAP:
                        ded_date = DATE_CAP - timedelta(days=rng.randint(1, 7))

                    # Lookback months: from audit_period_end to deduction_date
                    lookback_months = max(1, (ded_date - audit_period_end).days // 30)

                    # Code
                    code_pair = codes_by_retailer.get(retailer_id, {}).get(deduction_type)
                    if code_pair:
                        code_id, code_remitted = code_pair
                    else:
                        code_id, code_remitted = None, ""

                    # Window from rules
                    window = rules.get((retailer_id, deduction_type))
                    deadline = (ded_date + timedelta(days=window)).isoformat() if window else None

                    # Description varies by claim type
                    period = f"{audit_period_start.isoformat()} to {audit_period_end.isoformat()}"
                    desc = {
                        "pricing":    f"Post-audit pricing recovery — period {period}",
                        "allowance":  f"Post-audit allowance reconciliation — period {period}",
                        "freight":    f"Post-audit freight chargeback — period {period}",
                        "compliance": f"Post-audit compliance findings — period {period}",
                    }[claim_type]

                    # Post-audit claims are *not* vague — they carry an audit
                    # period and claim type, so the supplier knows what the
                    # claim references even if they dispute it. is_vague stays
                    # 0 to keep the schema convention "is_vague implies
                    # deduction_type='vague'" intact.
                    deduction_rows.append((
                        deduction_id, retailer_id, None, None, deduction_type,
                        code_id, code_remitted, desc,
                        amount, ded_date.isoformat(), deadline,
                        0, 1,  # is_vague=0, is_post_audit=1
                        0,  # is_double_dip
                        None,  # remittance_id — repopulated by 13
                    ))

                    claim_seq += 1
                    claim_id = f"PA-{claim_seq:05d}"
                    claim_rows.append((
                        claim_id, deduction_id, profile["auditor"],
                        audit_period_start.isoformat(),
                        audit_period_end.isoformat(),
                        claim_type, lookback_months,
                    ))

        cur.executemany("""
            INSERT INTO deductions (
                deduction_id, retailer_id, order_id, shipment_id, deduction_type,
                code_id, code_as_remitted, remittance_description,
                amount, deduction_date, dispute_deadline,
                is_vague, is_post_audit, is_double_dip, remittance_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, deduction_rows)
        cur.executemany("""
            INSERT INTO post_audit_claims (
                claim_id, deduction_id, auditor_name,
                audit_period_start, audit_period_end,
                claim_type, lookback_months
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, claim_rows)
        con.commit()

        n_d = len(deduction_rows)
        n_c = len(claim_rows)
        total = sum(d[8] for d in deduction_rows)

        print(f"Inserted {n_d:,} post-audit deductions and {n_c:,} post_audit_claims rows.")
        print(f"Total post-audit deduction value: ${total:,.0f}")
        print()
        print("By retailer:")
        by_ret: dict[str, tuple[int, float]] = {}
        for d in deduction_rows:
            rid = d[1]
            c, a = by_ret.get(rid, (0, 0.0))
            by_ret[rid] = (c + 1, a + d[8])
        for rid, (c, a) in sorted(by_ret.items()):
            print(f"  {rid:<10} {c:>3} deductions  ${a:>10,.0f}")
        print()
        print("By claim type:")
        from collections import Counter
        cc = Counter(c[5] for c in claim_rows)
        for ct, n in cc.most_common():
            print(f"  {ct:<12} {n:>3}")
        print()
        print(f"Lookback months range: {min(c[6] for c in claim_rows)} – {max(c[6] for c in claim_rows)}")

        print()
        print("NOTE: re-run scripts 14 (remittances) and 15 (disputes) to "
              "bundle these into payment events and surface them in dispute data.")



if __name__ == "__main__":
    main()
