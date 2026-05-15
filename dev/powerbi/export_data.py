"""Export data files for Power BI consumption.

Connects to the Cinderhaven Data Platform (Postgres) and exports one CSV
per logical table into powerbi/data/. Re-runnable — re-running refreshes
all files from the current database state.
"""

import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from workbook.db import connect

OUT = Path(__file__).resolve().parent / "data"


def _connect():
    return connect()


def _write_csv(filename: str, headers: list[str], rows: list[tuple]):
    path = OUT / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  {filename}: {len(rows):,} rows")


def _get_trailing_window(conn):
    weeks = conn.execute(
        "SELECT DISTINCT week_ending FROM stg_scan_data ORDER BY week_ending DESC LIMIT 52"
    ).fetchall()
    oldest_week = weeks[-1][0]
    max_scan = weeks[0][0]
    return oldest_week, max_scan


def export_dim_retailer(conn, oldest_week, max_scan):
    """Retailer dimension with trade rates, margins, and deduction totals."""
    retailers = conn.execute("""
        SELECT retailer_id, retailer_name, channel_type
        FROM dim_retailers
        ORDER BY retailer_name
    """).fetchall()

    channel_rev = dict(conn.execute("""
        SELECT s.retailer, SUM(sd.dollars_sold)
        FROM stg_scan_data sd JOIN stg_stores s ON sd.store_id = s.store_id
        WHERE sd.week_ending >= %s
        GROUP BY s.retailer
    """, (oldest_week,)).fetchall())

    rates_row = conn.execute("""
        SELECT AVG(trade_spend_pct_walmart), AVG(trade_spend_pct_costco),
               AVG(trade_spend_pct_whole_foods), AVG(trade_spend_pct_unfi),
               AVG(trade_spend_pct_dtc), AVG(trade_spend_pct_regional)
        FROM stg_sku_costs
    """).fetchone()
    rate_map = {
        "Walmart": rates_row[0], "Costco": rates_row[1],
        "Whole Foods": rates_row[2], "UNFI": rates_row[3],
        "DTC": rates_row[4],
    }
    regional_rate = rates_row[5]

    gm_rows = conn.execute("""
        SELECT AVG(cogs_per_unit),
               AVG(wholesale_walmart), AVG(wholesale_costco),
               AVG(wholesale_whole_foods), AVG(wholesale_unfi),
               AVG(wholesale_dtc), AVG(wholesale_regional)
        FROM stg_sku_costs
    """).fetchone()
    cogs = gm_rows[0]
    gm_map = {
        "Walmart": (gm_rows[1] - cogs) / gm_rows[1],
        "Costco": (gm_rows[2] - cogs) / gm_rows[2],
        "Whole Foods": (gm_rows[3] - cogs) / gm_rows[3],
        "UNFI": (gm_rows[4] - cogs) / gm_rows[4],
        "DTC": (gm_rows[5] - cogs) / gm_rows[5],
        "Regional": (gm_rows[6] - cogs) / gm_rows[6],
    }

    op_ded = dict(conn.execute("""
        SELECT retailer_id, SUM(amount)
        FROM stg_deductions
        WHERE deduction_date > (%s::date - interval '365 days')::date AND deduction_date <= %s
          AND deduction_type != 'promo_billback'
        GROUP BY retailer_id
    """, (max_scan, max_scan)).fetchall())

    pb_ded = dict(conn.execute("""
        SELECT retailer_id, SUM(amount)
        FROM stg_deductions
        WHERE deduction_date > (%s::date - interval '365 days')::date AND deduction_date <= %s
          AND deduction_type = 'promo_billback'
        GROUP BY retailer_id
    """, (max_scan, max_scan)).fetchall())

    headers = [
        "retailer_id", "retailer_name", "channel_type", "revenue",
        "trade_rate", "gross_margin", "structural_trade_dollars",
        "op_deductions", "promo_billback", "all_in_trade",
        "all_in_rate", "net_net_margin",
    ]
    rows = []
    for rid, retailer_name, channel in retailers:
        display = retailer_name
        rev = channel_rev.get(display, 0)
        rate = rate_map.get(display, regional_rate)
        gm = gm_map.get(display, gm_map["Regional"])
        structural = rev * rate
        op = op_ded.get(rid, 0)
        pb = pb_ded.get(rid, 0)
        all_in = structural + op + pb
        all_in_rate = all_in / rev if rev else 0
        net_net = gm - (all_in / rev) if rev else 0

        rows.append((
            rid, display, channel, round(rev, 2),
            round(rate, 6), round(gm, 6), round(structural, 2),
            round(op, 2), round(pb, 2), round(all_in, 2),
            round(all_in_rate, 6), round(net_net, 6),
        ))

    _write_csv("dim_retailer.csv", headers, rows)


def export_dim_product(conn):
    """Product/SKU dimension from dim_products + stg_sku_costs."""
    rows = conn.execute("""
        SELECT
            pm.sku,
            pm.product_name,
            pm.product_line,
            pm.subcategory,
            sc.cogs_per_unit,
            sc.wholesale_price,
            sc.wholesale_walmart,
            sc.wholesale_costco,
            sc.wholesale_whole_foods,
            sc.wholesale_regional,
            sc.wholesale_unfi,
            sc.wholesale_dtc
        FROM dim_products pm
        LEFT JOIN stg_sku_costs sc ON pm.sku = sc.sku
        ORDER BY pm.product_line, pm.sku
    """).fetchall()

    headers = [
        "sku", "product_name", "product_line", "subcategory",
        "cogs_per_unit", "wholesale_price",
        "wholesale_walmart", "wholesale_costco",
        "wholesale_whole_foods", "wholesale_regional",
        "wholesale_unfi", "wholesale_dtc",
    ]
    _write_csv("dim_product.csv", headers, rows)


def export_dim_promo(conn):
    """Promotion dimension with matched actual costs and computed ROI."""
    import bisect

    all_weeks = [r[0] for r in conn.execute(
        "SELECT DISTINCT week_ending FROM stg_scan_data ORDER BY week_ending"
    ).fetchall()]

    promos = conn.execute("""
        SELECT promo_id, sku, retailer, store_scope, start_week, end_week,
               duration_weeks, discount_depth_pct, promo_type, promo_cost,
               funding_mechanism
        FROM stg_promotions ORDER BY promo_id
    """).fetchall()

    actual_costs = dict(conn.execute("""
        SELECT p.promo_id || '|' || p.sku || '|' || p.retailer, SUM(d.amount)
        FROM stg_promotions p
        JOIN stg_deductions d ON LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
            AND d.deduction_type = 'promo_billback'
            AND d.deduction_date BETWEEN (p.start_week - interval '14 days')::date
                                     AND (p.end_week + interval '90 days')::date
        GROUP BY p.promo_id, p.sku, p.retailer
    """).fetchall())

    asp_map = dict(conn.execute("""
        SELECT sd.sku || '|' || s.retailer, AVG(sd.dollars_sold * 1.0 / sd.units_sold)
        FROM stg_scan_data sd JOIN stg_stores s ON sd.store_id = s.store_id
        WHERE sd.units_sold > 0
        GROUP BY sd.sku, s.retailer
    """).fetchall())

    vol_map = {}
    for sku, retailer, week, units in conn.execute("""
        SELECT sd.sku, s.retailer, sd.week_ending, SUM(sd.units_sold)
        FROM stg_scan_data sd JOIN stg_stores s ON sd.store_id = s.store_id
        GROUP BY sd.sku, s.retailer, sd.week_ending
    """).fetchall():
        vol_map.setdefault(f"{sku}|{retailer}", {})[week] = units

    def _nearest_idx(target):
        idx = bisect.bisect_left(all_weeks, target)
        if idx >= len(all_weeks):
            return len(all_weeks) - 1
        if idx == 0:
            return 0
        if abs(ord(all_weeks[idx][8]) - ord(target[8])) <= abs(ord(all_weeks[idx-1][8]) - ord(target[8])):
            return idx
        return idx - 1

    headers = [
        "promo_id", "sku", "retailer", "store_scope", "start_week",
        "end_week", "duration_weeks", "discount_depth_pct", "promo_type",
        "planned_cost", "actual_cost", "funding_mechanism",
        "asp", "baseline_avg_volume", "during_avg_volume",
        "incremental_volume", "incremental_revenue", "roi",
        "cost_source", "data_quality",
    ]

    window = 4
    rows = []
    for (pid, sku, retailer, scope, start_wk, end_wk, dur,
         discount, ptype, pcost, funding) in promos:

        key = f"{pid}|{sku}|{retailer}"
        vol_key = f"{sku}|{retailer}"
        actual = actual_costs.get(key)
        asp = asp_map.get(vol_key)
        weekly = vol_map.get(vol_key, {})

        start_idx = _nearest_idx(start_wk)
        end_idx = _nearest_idx(end_wk)

        pre_vols = []
        for offset in range(window, 0, -1):
            idx = start_idx - offset
            if 0 <= idx < len(all_weeks):
                v = weekly.get(all_weeks[idx], 0)
                if v > 0:
                    pre_vols.append(v)

        during_vols = []
        for idx in range(start_idx, min(end_idx + 1, len(all_weeks))):
            v = weekly.get(all_weeks[idx], 0)
            if v > 0:
                during_vols.append(v)

        post_vols = []
        for offset in range(1, window + 1):
            idx = end_idx + offset
            if idx < len(all_weeks):
                v = weekly.get(all_weeks[idx], 0)
                if v > 0:
                    post_vols.append(v)

        has_pre = len(pre_vols) > 0
        has_during = len(during_vols) > 0
        has_post = len(post_vols) > 0

        if has_pre and has_during and has_post:
            quality = "Full"
        elif has_during and (has_pre or has_post):
            quality = "Partial"
        else:
            quality = "No POS"

        baseline = sum(pre_vols) / len(pre_vols) if pre_vols else None
        during_avg = sum(during_vols) / len(during_vols) if during_vols else None

        if baseline is not None and during_avg is not None and asp:
            incr_vol = (during_avg - baseline) * (dur or 1)
            incr_rev = incr_vol * asp
            cost_used = actual if actual else pcost
            roi = incr_rev / cost_used if cost_used else None
        else:
            incr_vol = None
            incr_rev = None
            roi = None

        cost_source = "actual" if actual else "planned"

        rows.append((
            pid, sku, retailer, scope, start_wk, end_wk, dur,
            discount, ptype, pcost, actual, funding,
            round(asp, 4) if asp else None,
            round(baseline, 2) if baseline else None,
            round(during_avg, 2) if during_avg else None,
            round(incr_vol, 2) if incr_vol is not None else None,
            round(incr_rev, 2) if incr_rev is not None else None,
            round(roi, 4) if roi is not None else None,
            cost_source, quality,
        ))

    _write_csv("dim_promo.csv", headers, rows)


def export_fact_deductions(conn, max_scan):
    """Deductions export: trailing-365 window plus all-time risk flags.

    Includes rows outside the trailing window if they are double-dip
    events or ghost promo deductions, so those KPI cards show the
    correct all-time totals (matching the workbook).  An
    ``in_trailing_window`` flag lets DAX measures scope aggregations
    to the trailing period when needed.
    """
    # Ghost promo detection — all-time, no date filter (matches workbook)
    ghost_ids = set(r[0] for r in conn.execute("""
        SELECT d.deduction_id
        FROM stg_deductions d
        WHERE d.deduction_type = 'promo_billback'
          AND NOT EXISTS (
              SELECT 1 FROM stg_promotions p
              WHERE LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
                AND d.deduction_date BETWEEN (p.start_week - interval '14 days')::date
                                         AND (p.end_week + interval '90 days')::date
          )
    """).fetchall())

    # Main query: trailing-365 window + double-dip + ghost promo rows
    raw = conn.execute("""
        SELECT
            d.deduction_id,
            d.retailer_id,
            d.deduction_date,
            d.deduction_type,
            d.amount,
            d.code_as_remitted,
            COALESCE(dc.name, 'Unmapped') AS translated_code,
            COALESCE(dc.deduction_type, d.deduction_type) AS standardized_category,
            d.order_id,
            d.shipment_id,
            d.remittance_id,
            d.remittance_description,
            d.dispute_deadline,
            d.is_vague,
            d.is_post_audit,
            d.is_double_dip,
            dis.outcome AS dispute_outcome,
            dis.recovered_amount,
            dis.filed_date AS dispute_filed_date,
            dis.closed_date AS dispute_closed_date,
            CASE
                WHEN dis.closed_date IS NOT NULL
                THEN (dis.closed_date - d.deduction_date)
                WHEN dis.filed_date IS NOT NULL
                THEN (%s::date - d.deduction_date)
                ELSE NULL
            END AS days_outstanding,
            CASE
                WHEN d.deduction_date > (%s::date - interval '365 days')::date
                     AND d.deduction_date <= %s
                THEN 1 ELSE 0
            END AS in_trailing_window
        FROM stg_deductions d
        LEFT JOIN stg_deduction_codes dc ON d.code_id = dc.code_id
        LEFT JOIN stg_disputes dis ON dis.deduction_id = d.deduction_id
        WHERE (d.deduction_date > (%s::date - interval '365 days')::date AND d.deduction_date <= %s)
           OR d.is_double_dip = true
        ORDER BY d.deduction_date DESC, d.amount DESC
    """, (max_scan, max_scan, max_scan, max_scan, max_scan)).fetchall()

    # Also pull ghost promo deductions outside the trailing window
    ghost_outside = conn.execute("""
        SELECT
            d.deduction_id,
            d.retailer_id,
            d.deduction_date,
            d.deduction_type,
            d.amount,
            d.code_as_remitted,
            COALESCE(dc.name, 'Unmapped') AS translated_code,
            COALESCE(dc.deduction_type, d.deduction_type) AS standardized_category,
            d.order_id,
            d.shipment_id,
            d.remittance_id,
            d.remittance_description,
            d.dispute_deadline,
            d.is_vague,
            d.is_post_audit,
            d.is_double_dip,
            dis.outcome AS dispute_outcome,
            dis.recovered_amount,
            dis.filed_date AS dispute_filed_date,
            dis.closed_date AS dispute_closed_date,
            CASE
                WHEN dis.closed_date IS NOT NULL
                THEN (dis.closed_date - d.deduction_date)
                WHEN dis.filed_date IS NOT NULL
                THEN (%s::date - d.deduction_date)
                ELSE NULL
            END AS days_outstanding,
            0 AS in_trailing_window
        FROM stg_deductions d
        LEFT JOIN stg_deduction_codes dc ON d.code_id = dc.code_id
        LEFT JOIN stg_disputes dis ON dis.deduction_id = d.deduction_id
        WHERE d.deduction_type = 'promo_billback'
          AND NOT (d.deduction_date > (%s::date - interval '365 days')::date AND d.deduction_date <= %s)
          AND d.is_double_dip = false
        ORDER BY d.deduction_date DESC
    """, (max_scan, max_scan, max_scan)).fetchall()

    # Merge and deduplicate (double-dip rows may overlap with ghost)
    seen = set()
    rows = []
    for r in list(raw) + list(ghost_outside):
        ded_id = r[0]
        if ded_id in seen:
            continue
        seen.add(ded_id)
        is_ghost = 1 if ded_id in ghost_ids else 0
        rows.append(r + (is_ghost,))

    headers = [
        "deduction_id", "retailer_id", "deduction_date", "deduction_type",
        "amount", "code_as_remitted", "translated_code",
        "standardized_category", "order_id", "shipment_id",
        "remittance_id", "remittance_description", "dispute_deadline",
        "is_vague", "is_post_audit", "is_double_dip",
        "dispute_outcome", "recovered_amount",
        "dispute_filed_date", "dispute_closed_date", "days_outstanding",
        "in_trailing_window", "is_ghost_promo",
    ]
    _write_csv("fact_deductions.csv", headers, rows)
    return len(rows)


def export_fact_structural_trade(conn, oldest_week):
    """Structural trade by retailer using channel-average rates."""
    rows = conn.execute("""
        WITH channel_revenue AS (
            SELECT s.retailer,
                   SUM(sd.dollars_sold) AS revenue
            FROM stg_scan_data sd
            JOIN stg_stores s ON sd.store_id = s.store_id
            WHERE sd.week_ending >= %s
            GROUP BY s.retailer
        ),
        channel_rates AS (
            SELECT
                AVG(trade_spend_pct_walmart)     AS rate_walmart,
                AVG(trade_spend_pct_costco)      AS rate_costco,
                AVG(trade_spend_pct_whole_foods) AS rate_whole_foods,
                AVG(trade_spend_pct_unfi)        AS rate_unfi,
                AVG(trade_spend_pct_dtc)         AS rate_dtc,
                AVG(trade_spend_pct_regional)    AS rate_regional
            FROM stg_sku_costs
        )
        SELECT
            cr.retailer AS retailer_id,
            cr.revenue,
            CASE cr.retailer
                WHEN 'Walmart'     THEN rates.rate_walmart
                WHEN 'Costco'      THEN rates.rate_costco
                WHEN 'Whole Foods' THEN rates.rate_whole_foods
                WHEN 'UNFI'        THEN rates.rate_unfi
                WHEN 'DTC'         THEN rates.rate_dtc
                ELSE rates.rate_regional
            END AS trade_rate,
            cr.revenue * CASE cr.retailer
                WHEN 'Walmart'     THEN rates.rate_walmart
                WHEN 'Costco'      THEN rates.rate_costco
                WHEN 'Whole Foods' THEN rates.rate_whole_foods
                WHEN 'UNFI'        THEN rates.rate_unfi
                WHEN 'DTC'         THEN rates.rate_dtc
                ELSE rates.rate_regional
            END AS structural_trade_dollars
        FROM channel_revenue cr
        CROSS JOIN channel_rates rates
        ORDER BY cr.revenue DESC
    """, (oldest_week,)).fetchall()

    headers = [
        "retailer_id", "revenue", "trade_rate",
        "structural_trade_dollars",
    ]
    _write_csv("fact_structural_trade.csv", headers, rows)


def export_fact_scan_data(conn, oldest_week):
    """Scan data with pre/during/post promo flags for lift calculation."""
    import bisect

    all_weeks = [r[0] for r in conn.execute(
        "SELECT DISTINCT week_ending FROM stg_scan_data ORDER BY week_ending"
    ).fetchall()]

    promos = conn.execute("""
        SELECT promo_id, sku, retailer, start_week, end_week, duration_weeks
        FROM stg_promotions
    """).fetchall()

    scan_rows = conn.execute("""
        SELECT sd.sku, s.retailer, sd.store_id, sd.week_ending,
               sd.units_sold, sd.dollars_sold
        FROM stg_scan_data sd
        JOIN stg_stores s ON sd.store_id = s.store_id
        WHERE sd.week_ending >= %s
        ORDER BY sd.sku, s.retailer, sd.week_ending
    """, (oldest_week,)).fetchall()

    promo_windows = {}
    for pid, sku, retailer, start_wk, end_wk, dur in promos:
        key = f"{sku}|{retailer}"
        if key not in promo_windows:
            promo_windows[key] = []
        promo_windows[key].append((pid, start_wk, end_wk))

    def _find_nearest_week(target):
        idx = bisect.bisect_left(all_weeks, target)
        if idx >= len(all_weeks):
            return all_weeks[-1]
        if idx == 0:
            return all_weeks[0]
        if abs(ord(all_weeks[idx][8]) - ord(target[8])) <= abs(ord(all_weeks[idx-1][8]) - ord(target[8])):
            return all_weeks[idx]
        return all_weeks[idx - 1]

    headers = [
        "sku", "retailer", "store_id", "week_ending",
        "units_sold", "dollars_sold",
        "promo_id", "promo_period",
    ]

    rows = []
    window = 4
    for sku, retailer, store_id, week, units, dollars in scan_rows:
        key = f"{sku}|{retailer}"
        promo_id = None
        period = "none"

        if key in promo_windows:
            for pid, start_wk, end_wk in promo_windows[key]:
                nearest_start = _find_nearest_week(start_wk)
                nearest_end = _find_nearest_week(end_wk)

                start_idx = all_weeks.index(nearest_start) if nearest_start in all_weeks else -1
                end_idx = all_weeks.index(nearest_end) if nearest_end in all_weeks else -1
                week_idx = all_weeks.index(week) if week in all_weeks else -1

                if week_idx < 0 or start_idx < 0:
                    continue

                if start_idx <= week_idx <= end_idx:
                    promo_id = pid
                    period = "during"
                    break
                elif start_idx - window <= week_idx < start_idx:
                    promo_id = pid
                    period = "pre"
                    break
                elif end_idx < week_idx <= end_idx + window:
                    promo_id = pid
                    period = "post"
                    break

        rows.append((sku, retailer, store_id, week, units, dollars, promo_id, period))

    _write_csv("fact_scan_data.csv", headers, rows)


def export_fact_disputes(conn):
    """Dispute records with deduction context."""
    rows = conn.execute("""
        SELECT
            dis.dispute_id,
            dis.deduction_id,
            d.retailer_id,
            d.deduction_type,
            d.amount AS deduction_amount,
            dis.filed_date,
            dis.closed_date,
            dis.filing_method,
            dis.evidence_quality,
            dis.submitted_evidence_count,
            dis.was_within_deadline,
            dis.outcome,
            dis.recovered_amount,
            dis.labor_hours,
            CASE
                WHEN dis.closed_date IS NOT NULL
                THEN (dis.closed_date - dis.filed_date)
                ELSE NULL
            END AS days_to_resolve
        FROM stg_disputes dis
        JOIN stg_deductions d ON d.deduction_id = dis.deduction_id
        ORDER BY dis.filed_date DESC
    """).fetchall()

    headers = [
        "dispute_id", "deduction_id", "retailer_id", "deduction_type",
        "deduction_amount", "filed_date", "closed_date", "filing_method",
        "evidence_quality", "submitted_evidence_count",
        "was_within_deadline", "outcome", "recovered_amount",
        "labor_hours", "days_to_resolve",
    ]
    _write_csv("fact_disputes.csv", headers, rows)
    return len(rows)


def validate(conn, oldest_week, max_scan, ded_count, dispute_count):
    """Spot-check key totals against locked numbers."""
    print("\n=== Validation ===")
    passed = 0
    failed = 0

    def _check(name, actual, expected, tol):
        nonlocal passed, failed
        if abs(actual - expected) <= tol:
            print(f"  PASS  {name}: {actual:,.0f} (expected {expected:,.0f})")
            passed += 1
        else:
            print(f"  FAIL  {name}: {actual:,.0f} (expected {expected:,.0f})")
            failed += 1

    rev = conn.execute(
        "SELECT SUM(dollars_sold) FROM stg_scan_data WHERE week_ending >= %s",
        (oldest_week,)
    ).fetchone()[0]
    _check("Revenue", rev, 25593052, 2000)

    structural = 0
    with open(OUT / "fact_structural_trade.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            structural += float(row["structural_trade_dollars"])
    _check("Structural trade", structural, 4435052, 2000)

    waste = conn.execute("""
        SELECT SUM(amount) FROM stg_deductions
        WHERE deduction_date > (%s::date - interval '365 days')::date AND deduction_date <= %s
          AND deduction_type != 'promo_billback'
    """, (max_scan, max_scan)).fetchone()[0]
    _check("Operational waste", waste, 1010940, 2000)

    trailing_ded_count = 0
    ghost_count = 0
    ghost_total = 0
    dd_count = 0
    dd_total = 0
    with open(OUT / "fact_deductions.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("in_trailing_window") == "1":
                trailing_ded_count += 1
            if row["is_ghost_promo"] == "1":
                ghost_count += 1
                ghost_total += float(row["amount"])
            if row.get("is_double_dip") == "1":
                dd_count += 1
                dd_total += float(row["amount"])
    _check("Deduction count (trailing window)", trailing_ded_count, 2374, 5)
    print(f"  INFO  Total CSV rows (incl. out-of-window): {ded_count}")
    print(f"  INFO  Double-dip: count={dd_count}, total=${dd_total:,.0f}")
    print(f"  INFO  Ghost promos: count={ghost_count}, total=${ghost_total:,.0f}")

    _check("Dispute count", dispute_count, 1409, 2)

    rec = conn.execute("SELECT SUM(recovered_amount) FROM stg_disputes").fetchone()[0]
    _check("Total recovered", rec, 98216, 500)

    print(f"\n  {passed} passed, {failed} failed")
    return failed == 0


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.", file=sys.stderr)
        sys.exit(1)

    OUT.mkdir(parents=True, exist_ok=True)
    conn = _connect()

    print(f"Output: {OUT}")
    print()

    oldest_week, max_scan = _get_trailing_window(conn)
    print(f"Window: {oldest_week} to {max_scan}")
    print()

    print("Exporting...")
    export_dim_retailer(conn, oldest_week, max_scan)
    export_dim_product(conn)
    export_dim_promo(conn)
    ded_count = export_fact_deductions(conn, max_scan)
    export_fact_structural_trade(conn, oldest_week)
    export_fact_scan_data(conn, oldest_week)
    dispute_count = export_fact_disputes(conn)

    success = validate(conn, oldest_week, max_scan, ded_count, dispute_count)
    conn.close()

    if success:
        print("\nAll exports complete. All checks passed.")
    else:
        print("\nExports complete. SOME CHECKS FAILED.")
    return success


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
