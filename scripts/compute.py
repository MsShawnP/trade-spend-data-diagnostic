"""Single computation layer — reads SQLite, writes all CSVs.

This is THE contract between the database and every downstream consumer
(workbook, Power BI dashboard, validation scripts).  No business logic
lives in DAX measures or in the workbook generator's SQL queries.
Python computes everything here; CSVs are the single source of truth.

Outputs (written to ``powerbi/data/``):
    Existing star-schema tables (Power BI + workbook):
        dim_retailer.csv        — retailer dimension with margins & rates
        dim_product.csv         — product/SKU dimension
        dim_promo.csv           — promo dimension with ROI + volume arrays
        fact_deductions.csv     — deduction records with flags
        fact_structural_trade.csv — structural trade by retailer
        fact_scan_data.csv      — weekly POS data with promo tags
        fact_disputes.csv       — dispute records

    New workbook-specific tables:
        computed_kpis.csv       — single-row global KPIs
        waste_by_category.csv   — deduction type breakdown + owner
        double_dips.csv         — double-dip events
        deduction_codes.csv     — code crosswalk for Tab 6
        ghost_promos.csv        — ghost promo deductions (top 20)
"""

import bisect
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.build_db import find_database

OUT = ROOT / "powerbi" / "data"

# ── Reference data ───────────────────────────────────────────────

RECOVERABILITY = {
    "vague": "Low",
    "label_fine": "Low",
    "short_ship": "Medium",
    "spoilage": "Low",
    "late_delivery": "Medium",
    "slotting": "Low",
    "damaged": "Medium",
    "pallet_fine": "Low",
}

CATEGORY_TO_DEPT = {
    "slotting": ("Sales", "Negotiated trade terms"),
    "short_ship": ("Operations", "Fulfillment accuracy"),
    "late_delivery": ("Operations", "Logistics/carrier management"),
    "damaged": ("Operations", "Packaging/handling"),
    "pallet_fine": ("Operations", "Compliance with retailer specs"),
    "label_fine": ("Operations", "Labeling/packaging compliance"),
    "spoilage": ("Operations", "Shelf-life/inventory management"),
    "vague": ("Finance", "Unclear codes — investigate"),
}

CHANNEL_RATE_COLS = {
    "Walmart": "trade_spend_pct_walmart",
    "Costco": "trade_spend_pct_costco",
    "Whole Foods": "trade_spend_pct_whole_foods",
    "UNFI": "trade_spend_pct_unfi",
    "DTC": "trade_spend_pct_dtc",
}

_MAX_WINDOW = 12          # max pre/post weeks for promo volume arrays
_QC_WINDOW = 12           # quality-classification lookback
_DEFAULT_BASELINE = 4     # default baseline window for pre-computed ROI


# ── Helpers ──────────────────────────────────────────────────────

def _write_csv(filename: str, headers: list[str], rows: list[tuple]):
    path = OUT / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print(f"  {filename}: {len(rows):,} rows")


def _round_or_none(val, digits=2):
    return round(val, digits) if val is not None else None


def _nearest_week_idx(all_weeks, target):
    idx = bisect.bisect_left(all_weeks, target)
    if idx >= len(all_weeks):
        return len(all_weeks) - 1 if all_weeks else None
    if idx == 0:
        return 0
    if abs(ord(all_weeks[idx][8]) - ord(target[8])) <= \
       abs(ord(all_weeks[idx - 1][8]) - ord(target[8])):
        return idx
    return idx - 1


def _nearest_week(all_weeks, target):
    idx = _nearest_week_idx(all_weeks, target)
    return all_weeks[idx] if idx is not None else None


# ── Trailing window ──────────────────────────────────────────────

def get_trailing_window(conn):
    weeks = conn.execute(
        "SELECT DISTINCT week_ending FROM scan_data "
        "ORDER BY week_ending DESC LIMIT 52"
    ).fetchall()
    oldest_week = weeks[-1][0]
    max_scan = weeks[0][0]
    return oldest_week, max_scan


# ── Export functions ─────────────────────────────────────────────

def export_computed_kpis(conn, oldest_week, max_scan):
    """Single-row global KPIs consumed by every workbook tab."""

    revenue = conn.execute(
        "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
        (oldest_week,),
    ).fetchone()[0]

    # Channel revenue + structural trade
    channel_rev = dict(conn.execute("""
        SELECT s.retailer, SUM(sd.dollars_sold)
        FROM scan_data sd JOIN stores s ON sd.store_id = s.store_id
        WHERE sd.week_ending >= ?
        GROUP BY s.retailer
    """, (oldest_week,)).fetchall())

    rates = {}
    for channel, col in CHANNEL_RATE_COLS.items():
        rates[channel] = conn.execute(
            f"SELECT AVG({col}) FROM sku_costs"
        ).fetchone()[0]
    regional_rate = conn.execute(
        "SELECT AVG(trade_spend_pct_regional) FROM sku_costs"
    ).fetchone()[0]

    structural_trade = sum(
        rev * rates.get(retailer, regional_rate)
        for retailer, rev in channel_rev.items()
    )

    operational_waste = conn.execute("""
        SELECT SUM(amount) FROM deductions
        WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ?
          AND deduction_type != 'promo_billback'
    """, (max_scan, max_scan)).fetchone()[0] or 0

    all_in_trade = structural_trade + operational_waste

    dispute_stats = conn.execute(
        "SELECT COUNT(*), SUM(recovered_amount) FROM disputes"
    ).fetchone()
    dispute_count = dispute_stats[0]
    total_recovered = dispute_stats[1] or 0

    # Hardcoded 14.3% — see DECISIONS.md (data rebuild nondeterminism)
    recovery_rate = 0.143

    # Ghost promo summary
    ghost_summary = conn.execute("""
        SELECT COUNT(*), COALESCE(SUM(d.amount), 0)
        FROM deductions d
        WHERE d.deduction_type = 'promo_billback'
          AND NOT EXISTS (
              SELECT 1 FROM promotions p
              WHERE LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
                AND d.deduction_date BETWEEN date(p.start_week, '-14 days')
                                         AND date(p.end_week, '+90 days')
          )
    """).fetchone()

    headers = [
        "revenue", "structural_trade", "operational_waste",
        "all_in_trade_cost", "all_in_trade_rate",
        "structural_trade_rate", "waste_rate",
        "dispute_count", "total_recovered", "recovery_rate",
        "ghost_promo_count", "ghost_promo_total",
        "oldest_week", "max_scan",
    ]
    row = [(
        round(revenue, 2),
        round(structural_trade, 2),
        round(operational_waste, 2),
        round(all_in_trade, 2),
        round(all_in_trade / revenue, 6) if revenue else 0,
        round(structural_trade / revenue, 6) if revenue else 0,
        round(operational_waste / revenue, 6) if revenue else 0,
        dispute_count,
        round(total_recovered, 2),
        recovery_rate,
        ghost_summary[0],
        round(ghost_summary[1], 2),
        oldest_week,
        max_scan,
    )]
    _write_csv("computed_kpis.csv", headers, row)
    return {
        "revenue": revenue,
        "structural_trade": structural_trade,
        "operational_waste": operational_waste,
    }


def export_waste_by_category(conn, max_scan, operational_waste):
    """Deduction type breakdown with recoverability and ownership."""

    categories = conn.execute("""
        SELECT
            d.deduction_type,
            COUNT(*) as cnt,
            SUM(d.amount) as total,
            AVG(
                CASE WHEN dis.closed_date IS NOT NULL
                     THEN julianday(dis.closed_date) - julianday(d.deduction_date)
                END
            ) as avg_days
        FROM deductions d
        LEFT JOIN disputes dis ON dis.deduction_id = d.deduction_id
        WHERE d.deduction_date > date(?, '-365 days') AND d.deduction_date <= ?
          AND d.deduction_type != 'promo_billback'
        GROUP BY d.deduction_type
        ORDER BY SUM(d.amount) DESC
    """, (max_scan, max_scan)).fetchall()

    headers = [
        "deduction_type", "label", "count", "total_amount",
        "pct_of_waste", "avg_days_to_resolve", "recoverability",
        "owner", "root_cause",
    ]
    rows = []
    for dtype, cnt, total, avg_days in categories:
        label = dtype.replace("_", " ").title()
        pct = total / operational_waste if operational_waste else 0
        recov = RECOVERABILITY.get(dtype, "Low")
        owner, cause = CATEGORY_TO_DEPT.get(dtype, ("Unclassified", ""))
        rows.append((
            dtype, label, cnt,
            round(total, 2),
            round(pct, 6),
            round(avg_days) if avg_days else None,
            recov, owner, cause,
        ))

    _write_csv("waste_by_category.csv", headers, rows)


def export_double_dips(conn):
    """Double-dip events (all-time, no date filter)."""

    rows = conn.execute("""
        SELECT deduction_id, retailer_id, amount, deduction_date, deduction_type
        FROM deductions
        WHERE is_double_dip = 1
        ORDER BY amount DESC
    """).fetchall()

    formatted = []
    for ded_id, retailer_id, amount, ded_date, dtype in rows:
        retailer_name = retailer_id.replace("_", " ").title()
        formatted.append((
            ded_id, retailer_id, retailer_name,
            round(amount, 2), ded_date,
            dtype.replace("_", " ").title(),
        ))

    headers = [
        "deduction_id", "retailer_id", "retailer_name",
        "amount", "deduction_date", "deduction_type",
    ]
    _write_csv("double_dips.csv", headers, formatted)


def export_deduction_codes(conn):
    """Deduction code crosswalk for Tab 6."""

    rows = conn.execute("""
        SELECT
            retailer_id,
            code,
            name,
            deduction_type,
            CASE WHEN is_published = 1 THEN 'Verified' ELSE 'Inferred' END
        FROM deduction_codes
        ORDER BY retailer_id, deduction_type, code
    """).fetchall()

    formatted = []
    for retailer_id, code, name, dtype, status in rows:
        retailer_name = retailer_id.replace("_", " ").title()
        formatted.append((
            retailer_id, retailer_name, code, name,
            dtype.replace("_", " ").title(), status,
        ))

    headers = [
        "retailer_id", "retailer_name", "code", "name",
        "deduction_type", "status",
    ]
    _write_csv("deduction_codes.csv", headers, formatted)


def export_ghost_promos(conn):
    """Top 20 ghost promo deductions (all-time)."""

    rows = conn.execute("""
        SELECT d.deduction_id, d.retailer_id, d.amount, d.deduction_date
        FROM deductions d
        WHERE d.deduction_type = 'promo_billback'
          AND NOT EXISTS (
              SELECT 1 FROM promotions p
              WHERE LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
                AND d.deduction_date BETWEEN date(p.start_week, '-14 days')
                                         AND date(p.end_week, '+90 days')
          )
        ORDER BY d.amount DESC
        LIMIT 20
    """).fetchall()

    formatted = []
    for ded_id, retailer_id, amount, ded_date in rows:
        retailer_name = retailer_id.replace("_", " ").title()
        formatted.append((
            ded_id, retailer_id, retailer_name,
            round(amount, 2), ded_date,
        ))

    headers = [
        "deduction_id", "retailer_id", "retailer_name",
        "amount", "deduction_date",
    ]
    _write_csv("ghost_promos.csv", headers, formatted)


def export_dim_retailer(conn, oldest_week, max_scan):
    """Retailer dimension with trade rates, margins, deduction totals.

    Enhanced with rev_share, op_ded_rate, ded_share for workbook Tab 4.
    """
    retailers = conn.execute("""
        SELECT retailer_id, name, channel_type
        FROM retailers ORDER BY name
    """).fetchall()

    channel_rev = dict(conn.execute("""
        SELECT s.retailer, SUM(sd.dollars_sold)
        FROM scan_data sd JOIN stores s ON sd.store_id = s.store_id
        WHERE sd.week_ending >= ?
        GROUP BY s.retailer
    """, (oldest_week,)).fetchall())

    rates_row = conn.execute("""
        SELECT AVG(trade_spend_pct_walmart), AVG(trade_spend_pct_costco),
               AVG(trade_spend_pct_whole_foods), AVG(trade_spend_pct_unfi),
               AVG(trade_spend_pct_dtc), AVG(trade_spend_pct_regional)
        FROM sku_costs
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
        FROM sku_costs
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
        FROM deductions
        WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ?
          AND deduction_type != 'promo_billback'
        GROUP BY retailer_id
    """, (max_scan, max_scan)).fetchall())

    pb_ded = dict(conn.execute("""
        SELECT retailer_id, SUM(amount)
        FROM deductions
        WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ?
          AND deduction_type = 'promo_billback'
        GROUP BY retailer_id
    """, (max_scan, max_scan)).fetchall())

    total_revenue = sum(channel_rev.values())

    # Build rows with pre-computed shares
    raw_rows = []
    for rid, name, channel in retailers:
        display = name
        rev = channel_rev.get(display, 0)
        rate = rate_map.get(display, regional_rate) if rev > 0 else 0
        gm = gm_map.get(display, gm_map["Regional"])
        structural = rev * rate
        op = op_ded.get(rid, 0)
        pb = pb_ded.get(rid, 0)
        all_in = structural + op + pb
        all_in_rate = all_in / rev if rev else 0
        net_net = gm - (all_in / rev) if rev else 0
        rev_share = rev / total_revenue if total_revenue else 0
        op_ded_rate = op / rev if rev else 0
        total_ded = op + pb

        raw_rows.append({
            "rid": rid, "display": display, "channel": channel,
            "rev": rev, "rev_share": rev_share, "rate": rate, "gm": gm,
            "structural": structural, "op": op, "op_ded_rate": op_ded_rate,
            "pb": pb, "all_in": all_in, "all_in_rate": all_in_rate,
            "net_net": net_net, "total_ded": total_ded,
        })

    total_ded_all = sum(r["total_ded"] for r in raw_rows)

    headers = [
        "retailer_id", "retailer_name", "channel_type", "revenue",
        "rev_share", "trade_rate", "gross_margin",
        "structural_trade_dollars", "op_deductions", "op_ded_rate",
        "promo_billback", "all_in_trade", "all_in_rate", "net_net_margin",
        "total_deductions", "ded_share",
    ]
    rows = []
    for r in raw_rows:
        ded_share = r["total_ded"] / total_ded_all if total_ded_all else 0
        rows.append((
            r["rid"], r["display"], r["channel"],
            round(r["rev"], 2),
            round(r["rev_share"], 6),
            round(r["rate"], 6),
            round(r["gm"], 6),
            round(r["structural"], 2),
            round(r["op"], 2),
            round(r["op_ded_rate"], 6),
            round(r["pb"], 2),
            round(r["all_in"], 2),
            round(r["all_in_rate"], 6),
            round(r["net_net"], 6),
            round(r["total_ded"], 2),
            round(ded_share, 6),
        ))

    _write_csv("dim_retailer.csv", headers, rows)


def export_dim_product(conn):
    """Product/SKU dimension from product_master + sku_costs."""
    rows = conn.execute("""
        SELECT
            pm.sku, pm.product_name, pm.product_line, pm.subcategory,
            sc.cogs_per_unit, sc.wholesale_price,
            sc.wholesale_walmart, sc.wholesale_costco,
            sc.wholesale_whole_foods, sc.wholesale_regional,
            sc.wholesale_unfi, sc.wholesale_dtc
        FROM product_master pm
        LEFT JOIN sku_costs sc ON pm.sku = sc.sku
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
    """Promo dimension with pre-computed ROI and volume arrays.

    Volume arrays (12 pre + 12 during + 12 post) are embedded as columns
    so the workbook's interactive OFFSET formulas can read them directly.
    Pre-computed ROI uses the default 4-week baseline window.
    """
    all_weeks = [r[0] for r in conn.execute(
        "SELECT DISTINCT week_ending FROM scan_data ORDER BY week_ending"
    ).fetchall()]

    promos = conn.execute("""
        SELECT promo_id, sku, retailer, store_scope, start_week, end_week,
               duration_weeks, discount_depth_pct, promo_type, promo_cost,
               funding_mechanism
        FROM promotions ORDER BY promo_id
    """).fetchall()

    actual_costs = dict(conn.execute("""
        SELECT p.promo_id || '|' || p.sku || '|' || p.retailer, SUM(d.amount)
        FROM promotions p
        JOIN deductions d ON LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
            AND d.deduction_type = 'promo_billback'
            AND d.deduction_date BETWEEN date(p.start_week, '-14 days')
                                     AND date(p.end_week, '+90 days')
        GROUP BY p.promo_id, p.sku, p.retailer
    """).fetchall())

    asp_map = dict(conn.execute("""
        SELECT sd.sku || '|' || s.retailer,
               AVG(sd.dollars_sold * 1.0 / sd.units_sold)
        FROM scan_data sd JOIN stores s ON sd.store_id = s.store_id
        WHERE sd.units_sold > 0
        GROUP BY sd.sku, s.retailer
    """).fetchall())

    vol_map = {}
    for sku, retailer, week, units in conn.execute("""
        SELECT sd.sku, s.retailer, sd.week_ending, SUM(sd.units_sold)
        FROM scan_data sd JOIN stores s ON sd.store_id = s.store_id
        GROUP BY sd.sku, s.retailer, sd.week_ending
    """).fetchall():
        vol_map.setdefault(f"{sku}|{retailer}", {})[week] = units

    # Volume column headers
    vol_headers = (
        [f"pre_vol_{i:02d}" for i in range(1, _MAX_WINDOW + 1)]
        + [f"during_vol_{i:02d}" for i in range(1, _MAX_WINDOW + 1)]
        + [f"post_vol_{i:02d}" for i in range(1, _MAX_WINDOW + 1)]
    )

    headers = [
        "promo_id", "sku", "retailer", "store_scope", "start_week",
        "end_week", "duration_weeks", "discount_depth_pct", "promo_type",
        "planned_cost", "actual_cost", "funding_mechanism",
        "asp", "baseline_avg_volume", "during_avg_volume",
        "incremental_volume", "incremental_revenue", "roi",
        "cost_source", "data_quality",
    ] + vol_headers

    window = _DEFAULT_BASELINE
    rows = []
    for (pid, sku, retailer, scope, start_wk, end_wk, dur,
         discount, ptype, pcost, funding) in promos:

        key = f"{pid}|{sku}|{retailer}"
        vol_key = f"{sku}|{retailer}"
        actual = actual_costs.get(key)
        asp = asp_map.get(vol_key)
        weekly = vol_map.get(vol_key, {})

        start_idx = _nearest_week_idx(all_weeks, start_wk)
        end_idx = _nearest_week_idx(all_weeks, end_wk)

        # Collect 12-week pre/during/post volumes
        pre_vols = []
        for offset in range(_QC_WINDOW, 0, -1):
            idx = start_idx - offset if start_idx is not None else -1
            if 0 <= idx < len(all_weeks):
                pre_vols.append(weekly.get(all_weeks[idx], 0))
            else:
                pre_vols.append(None)

        during_vols_raw = []
        if start_idx is not None:
            for idx in range(start_idx,
                             min((end_idx or start_idx) + 1, len(all_weeks))):
                during_vols_raw.append(weekly.get(all_weeks[idx], 0))

        post_vols = []
        for offset in range(1, _QC_WINDOW + 1):
            idx = (end_idx or 0) + offset
            if idx < len(all_weeks):
                post_vols.append(weekly.get(all_weeks[idx], 0))
            else:
                post_vols.append(None)

        # Quality classification (12-week lookback, check first 4 entries)
        has_pre = any(v is not None and v > 0 for v in pre_vols[:4])
        has_during = len(during_vols_raw) > 0 and any(
            v > 0 for v in during_vols_raw
        )
        has_post = any(v is not None and v > 0 for v in post_vols[:4])

        if start_idx is None or not weekly:
            quality = "No POS"
        elif has_pre and has_during and has_post:
            quality = "Full"
        elif has_during and (has_pre or has_post):
            quality = "Partial"
        else:
            quality = "No POS"

        # Pre-computed ROI at default window
        pre_for_baseline = [
            v for v in pre_vols[-window:] if v is not None and v > 0
        ]
        during_positive = [v for v in during_vols_raw if v > 0]

        baseline = (sum(pre_for_baseline) / len(pre_for_baseline)
                    if pre_for_baseline else None)
        during_avg = (sum(during_positive) / len(during_positive)
                      if during_positive else None)

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

        # Pad volume arrays to exactly _MAX_WINDOW entries
        pre_padded = (pre_vols + [None] * _MAX_WINDOW)[:_MAX_WINDOW]
        during_padded = (during_vols_raw + [None] * _MAX_WINDOW)[:_MAX_WINDOW]
        post_padded = (post_vols + [None] * _MAX_WINDOW)[:_MAX_WINDOW]

        # Format volumes: None → "" for CSV
        def _vol(v):
            return v if v is not None else ""

        vol_values = (
            [_vol(v) for v in pre_padded]
            + [_vol(v) for v in during_padded]
            + [_vol(v) for v in post_padded]
        )

        rows.append((
            pid, sku, retailer, scope, start_wk, end_wk, dur,
            discount, ptype, pcost, actual, funding,
            _round_or_none(asp, 4),
            _round_or_none(baseline, 2),
            _round_or_none(during_avg, 2),
            _round_or_none(incr_vol, 2),
            _round_or_none(incr_rev, 2),
            _round_or_none(roi, 4),
            cost_source, quality,
            *vol_values,
        ))

    _write_csv("dim_promo.csv", headers, rows)


def export_fact_deductions(conn, max_scan):
    """Deductions: trailing-365 window + all-time double-dip + ghost promos.

    Includes rows outside trailing window for double-dip and ghost promo
    KPIs.  ``in_trailing_window`` flag scopes aggregations to trailing period.
    """
    ghost_ids = set(r[0] for r in conn.execute("""
        SELECT d.deduction_id
        FROM deductions d
        WHERE d.deduction_type = 'promo_billback'
          AND NOT EXISTS (
              SELECT 1 FROM promotions p
              WHERE LOWER(REPLACE(p.retailer, ' ', '_')) = d.retailer_id
                AND d.deduction_date BETWEEN date(p.start_week, '-14 days')
                                         AND date(p.end_week, '+90 days')
          )
    """).fetchall())

    raw = conn.execute("""
        SELECT
            d.deduction_id, d.retailer_id, d.deduction_date,
            d.deduction_type, d.amount, d.code_as_remitted,
            COALESCE(dc.name, 'Unmapped') AS translated_code,
            COALESCE(dc.deduction_type, d.deduction_type) AS standardized_category,
            d.order_id, d.shipment_id, d.remittance_id,
            d.remittance_description, d.dispute_deadline,
            d.is_vague, d.is_post_audit, d.is_double_dip,
            dis.outcome, dis.recovered_amount,
            dis.filed_date, dis.closed_date,
            CASE
                WHEN dis.closed_date IS NOT NULL
                THEN CAST(julianday(dis.closed_date)
                          - julianday(d.deduction_date) AS INTEGER)
                WHEN dis.filed_date IS NOT NULL
                THEN CAST(julianday(?)
                          - julianday(d.deduction_date) AS INTEGER)
                ELSE NULL
            END AS days_outstanding,
            CASE
                WHEN d.deduction_date > date(?, '-365 days')
                     AND d.deduction_date <= ?
                THEN 1 ELSE 0
            END AS in_trailing_window
        FROM deductions d
        LEFT JOIN deduction_codes dc ON d.code_id = dc.code_id
        LEFT JOIN disputes dis ON dis.deduction_id = d.deduction_id
        WHERE (d.deduction_date > date(?, '-365 days') AND d.deduction_date <= ?)
           OR d.is_double_dip = 1
        ORDER BY d.deduction_date DESC, d.amount DESC
    """, (max_scan, max_scan, max_scan, max_scan, max_scan)).fetchall()

    ghost_outside = conn.execute("""
        SELECT
            d.deduction_id, d.retailer_id, d.deduction_date,
            d.deduction_type, d.amount, d.code_as_remitted,
            COALESCE(dc.name, 'Unmapped'), COALESCE(dc.deduction_type, d.deduction_type),
            d.order_id, d.shipment_id, d.remittance_id,
            d.remittance_description, d.dispute_deadline,
            d.is_vague, d.is_post_audit, d.is_double_dip,
            dis.outcome, dis.recovered_amount,
            dis.filed_date, dis.closed_date,
            CASE
                WHEN dis.closed_date IS NOT NULL
                THEN CAST(julianday(dis.closed_date)
                          - julianday(d.deduction_date) AS INTEGER)
                WHEN dis.filed_date IS NOT NULL
                THEN CAST(julianday(?)
                          - julianday(d.deduction_date) AS INTEGER)
                ELSE NULL
            END,
            0
        FROM deductions d
        LEFT JOIN deduction_codes dc ON d.code_id = dc.code_id
        LEFT JOIN disputes dis ON dis.deduction_id = d.deduction_id
        WHERE d.deduction_type = 'promo_billback'
          AND NOT (d.deduction_date > date(?, '-365 days')
                   AND d.deduction_date <= ?)
          AND d.is_double_dip = 0
        ORDER BY d.deduction_date DESC
    """, (max_scan, max_scan, max_scan)).fetchall()

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
            SELECT s.retailer, SUM(sd.dollars_sold) AS revenue
            FROM scan_data sd
            JOIN stores s ON sd.store_id = s.store_id
            WHERE sd.week_ending >= ?
            GROUP BY s.retailer
        ),
        channel_rates AS (
            SELECT
                AVG(trade_spend_pct_walmart)     AS rate_walmart,
                AVG(trade_spend_pct_costco)      AS rate_costco,
                AVG(trade_spend_pct_whole_foods)  AS rate_whole_foods,
                AVG(trade_spend_pct_unfi)         AS rate_unfi,
                AVG(trade_spend_pct_dtc)          AS rate_dtc,
                AVG(trade_spend_pct_regional)     AS rate_regional
            FROM sku_costs
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

    all_weeks = [r[0] for r in conn.execute(
        "SELECT DISTINCT week_ending FROM scan_data ORDER BY week_ending"
    ).fetchall()]

    promos = conn.execute("""
        SELECT promo_id, sku, retailer, start_week, end_week, duration_weeks
        FROM promotions
    """).fetchall()

    scan_rows = conn.execute("""
        SELECT sd.sku, s.retailer, sd.store_id, sd.week_ending,
               sd.units_sold, sd.dollars_sold
        FROM scan_data sd
        JOIN stores s ON sd.store_id = s.store_id
        WHERE sd.week_ending >= ?
        ORDER BY sd.sku, s.retailer, sd.week_ending
    """, (oldest_week,)).fetchall()

    promo_windows = {}
    for pid, sku, retailer, start_wk, end_wk, dur in promos:
        key = f"{sku}|{retailer}"
        if key not in promo_windows:
            promo_windows[key] = []
        promo_windows[key].append((pid, start_wk, end_wk))

    headers = [
        "sku", "retailer", "store_id", "week_ending",
        "units_sold", "dollars_sold", "promo_id", "promo_period",
    ]

    window = _DEFAULT_BASELINE
    rows = []
    for sku, retailer, store_id, week, units, dollars in scan_rows:
        key = f"{sku}|{retailer}"
        promo_id = None
        period = "none"

        if key in promo_windows:
            for pid, start_wk, end_wk in promo_windows[key]:
                nearest_start = _nearest_week(all_weeks, start_wk)
                nearest_end = _nearest_week(all_weeks, end_wk)

                if nearest_start is None or nearest_end is None:
                    continue

                start_i = all_weeks.index(nearest_start)
                end_i = all_weeks.index(nearest_end)
                week_i = all_weeks.index(week) if week in all_weeks else -1

                if week_i < 0 or start_i < 0:
                    continue

                if start_i <= week_i <= end_i:
                    promo_id, period = pid, "during"
                    break
                elif start_i - window <= week_i < start_i:
                    promo_id, period = pid, "pre"
                    break
                elif end_i < week_i <= end_i + window:
                    promo_id, period = pid, "post"
                    break

        rows.append((sku, retailer, store_id, week, units, dollars,
                      promo_id, period))

    _write_csv("fact_scan_data.csv", headers, rows)


def export_fact_disputes(conn):
    """Dispute records with deduction context."""
    rows = conn.execute("""
        SELECT
            dis.dispute_id, dis.deduction_id, d.retailer_id,
            d.deduction_type, d.amount AS deduction_amount,
            dis.filed_date, dis.closed_date, dis.filing_method,
            dis.evidence_quality, dis.submitted_evidence_count,
            dis.was_within_deadline, dis.outcome, dis.recovered_amount,
            dis.labor_hours,
            CASE
                WHEN dis.closed_date IS NOT NULL
                THEN CAST(julianday(dis.closed_date)
                          - julianday(dis.filed_date) AS INTEGER)
                ELSE NULL
            END AS days_to_resolve
        FROM disputes dis
        JOIN deductions d ON d.deduction_id = dis.deduction_id
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


# ── Validation ───────────────────────────────────────────────────

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
        "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
        (oldest_week,)
    ).fetchone()[0]
    _check("Revenue", rev, 25_593_052, 2000)

    structural = 0
    with open(OUT / "fact_structural_trade.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            structural += float(row["structural_trade_dollars"])
    _check("Structural trade", structural, 4_435_052, 2000)

    waste = conn.execute("""
        SELECT SUM(amount) FROM deductions
        WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ?
          AND deduction_type != 'promo_billback'
    """, (max_scan, max_scan)).fetchone()[0]
    _check("Operational waste", waste, 1_010_940, 2000)

    trailing_ded_count = 0
    ghost_count = 0
    dd_count = 0
    dd_total = 0
    with open(OUT / "fact_deductions.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("in_trailing_window") == "1":
                trailing_ded_count += 1
            if row["is_ghost_promo"] == "1":
                ghost_count += 1
            if row.get("is_double_dip") == "1":
                dd_count += 1
                dd_total += float(row["amount"])
    _check("Deduction count (trailing)", trailing_ded_count, 2374, 5)
    print(f"  INFO  Total CSV rows (incl. out-of-window): {ded_count}")
    print(f"  INFO  Double-dip: count={dd_count}, total=${dd_total:,.0f}")
    print(f"  INFO  Ghost promos: count={ghost_count}")

    _check("Dispute count", dispute_count, 1409, 2)

    rec = conn.execute(
        "SELECT SUM(recovered_amount) FROM disputes"
    ).fetchone()[0]
    _check("Total recovered", rec, 98_216, 500)

    # Validate new workbook CSVs
    import json as _json  # noqa: F811

    with open(OUT / "computed_kpis.csv", encoding="utf-8") as f:
        kpi = next(csv.DictReader(f))
    _check("KPI revenue", float(kpi["revenue"]), rev, 1)
    _check("KPI waste", float(kpi["operational_waste"]), waste, 1)

    waste_cat_total = 0
    with open(OUT / "waste_by_category.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            waste_cat_total += float(row["total_amount"])
    _check("Category waste sums to total", waste_cat_total, waste, 1)

    dd_csv_count = 0
    with open(OUT / "double_dips.csv", encoding="utf-8") as f:
        dd_csv_count = sum(1 for _ in csv.DictReader(f))
    _check("Double-dip CSV count", dd_csv_count, 3, 0)

    code_count = 0
    with open(OUT / "deduction_codes.csv", encoding="utf-8") as f:
        code_count = sum(1 for _ in csv.DictReader(f))
    print(f"  INFO  Deduction codes: {code_count} rows")

    print(f"\n  {passed} passed, {failed} failed")
    return failed == 0


# ── Main ─────────────────────────────────────────────────────────

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    db_path = find_database()
    conn = sqlite3.connect(db_path)

    print(f"Database: {db_path}")
    print(f"Output:   {OUT}")
    print()

    oldest_week, max_scan = get_trailing_window(conn)
    print(f"Window: {oldest_week} to {max_scan}")
    print()

    print("Exporting...")
    kpi_data = export_computed_kpis(conn, oldest_week, max_scan)
    export_waste_by_category(conn, max_scan, kpi_data["operational_waste"])
    export_double_dips(conn)
    export_deduction_codes(conn)
    export_ghost_promos(conn)
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
    success = main()
    sys.exit(0 if success else 1)
