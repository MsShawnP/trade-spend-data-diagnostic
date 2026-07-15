"""Generate the `orders` and `order_lines` tables.

Seeds purchase orders from each retailer to Cinderhaven across the
36-month window (Jan 2024 - Jan 2027). Counts are calibrated so that
total annualized line value lands in the $20-30M range (consistent with
the base dataset's $25M revenue target).

Per-retailer SKU authorization:
  - Walmart, Costco, Whole Foods, UNFI, regional chains: derived from
    base distribution_log joined to stores.
  - KeHE: not in base stores. Uses UNFI's authorized SKU set as a
    proxy (similar natural-foods distribution profile). Synthetic
    assumption — flagged in retailers.notes.
  - DTC: skipped — DTC is not in the deduction model (no PO grain).

Pricing: pulled from sku_costs.unit_wholesale × retailer-specific
multiplier where available; falls back to msrp × 0.55 if the SKU has
no sku_costs row for the retailer.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from shared import DB_PATH

SEED = 42

WINDOW_START = date(2024, 1, 1)
WINDOW_END   = date(2027, 1, 2)

# Per-retailer order-generation config:
#   orders_per_month        — Poisson mean
#   avg_lines_per_order     — uniform 2..N range center
#   avg_units_per_line      — order line size in cases (mean of triangular dist)
#   units_min, units_max    — clamp
RETAILER_CONFIG = {
    "walmart":              {"per_month": 95, "lines": (3, 6),  "units": (5,  35,  18)},
    "unfi":                 {"per_month": 55, "lines": (4, 9),  "units": (3,  20,   7)},
    "kehe":                 {"per_month": 45, "lines": (4, 9),  "units": (3,  18,   6)},
    "whole_foods":          {"per_month": 55, "lines": (3, 7),  "units": (2,  15,   5)},
    "costco":               {"per_month":  6, "lines": (2, 4),  "units": (30, 150,  70)},
    "kroger":               {"per_month": 22, "lines": (3, 6),  "units": (2,  12,   4)},
    "sprouts":              {"per_month": 16, "lines": (3, 6),  "units": (2,  12,   4)},
    "regional_group":       {"per_month": 16, "lines": (3, 5),  "units": (2,  10,   3)},
}

# Map our slugs to base table retailer names (stores.retailer / sku_costs columns).
BASE_NAME = {
    "walmart": "Walmart",
    "costco": "Costco",
    "whole_foods": "Whole Foods",
    "unfi": "UNFI",
    "kroger": "Kroger",
    "sprouts": "Sprouts",
    "regional_group": "Regional Group",
}

# sku_costs has retailer-specific wholesale columns (lowercase + underscore).
COSTS_COL = {
    "walmart": "wholesale_walmart",
    "costco": "wholesale_costco",
    "whole_foods": "wholesale_whole_foods",
    "unfi": "wholesale_unfi",
    "kehe": "wholesale_kehe",
    "kroger": "wholesale_regional",
    "sprouts": "wholesale_regional",
    "regional_group": "wholesale_regional",
}


def months_in_window() -> list[tuple[int, int]]:
    out = []
    y, m = WINDOW_START.year, WINDOW_START.month
    while (y, m) <= (WINDOW_END.year, WINDOW_END.month):
        out.append((y, m))
        m += 1
        if m > 12:
            y += 1
            m = 1
    return out


def authorized_skus(con: sqlite3.Connection) -> dict[str, list[str]]:
    """Return {retailer_id: [sku, ...]} based on base distribution_log.
    KeHE proxies off UNFI's authorized set."""
    cur = con.cursor()
    rows = cur.execute("""
        SELECT DISTINCT s.retailer, d.sku
        FROM distribution_log d
        JOIN stores s ON s.store_id = d.store_id
    """).fetchall()
    by_base_name: dict[str, set[str]] = {}
    for retailer, sku in rows:
        by_base_name.setdefault(retailer, set()).add(sku)
    result: dict[str, list[str]] = {}
    for slug, name in BASE_NAME.items():
        result[slug] = sorted(by_base_name.get(name, set()))
    # KeHE: proxy via UNFI
    result["kehe"] = list(result.get("unfi", []))
    return result


def first_auth_date(con: sqlite3.Connection) -> dict[tuple[str, str], date]:
    """Earliest authorization date per (retailer_id, sku) — orders dated before
    this should not exist for that pair."""
    cur = con.cursor()
    rows = cur.execute("""
        SELECT s.retailer, d.sku, MIN(d.authorized_date)
        FROM distribution_log d
        JOIN stores s ON s.store_id = d.store_id
        GROUP BY s.retailer, d.sku
    """).fetchall()
    out: dict[tuple[str, str], date] = {}
    base_name_to_slug = {v: k for k, v in BASE_NAME.items()}
    for retailer, sku, authd in rows:
        slug = base_name_to_slug.get(retailer)
        if not slug or not authd:
            continue
        out[(slug, sku)] = date.fromisoformat(authd)
    # KeHE: use UNFI's first-auth dates
    for (slug, sku), d in list(out.items()):
        if slug == "unfi":
            out[("kehe", sku)] = d
    return out


def load_prices(con: sqlite3.Connection) -> dict[tuple[str, str], float]:
    """Return {(retailer_slug, sku): per-CASE wholesale price}. Per-unit
    wholesale × case_pack_qty. Falls back to msrp × 0.55 × pack_qty when
    the retailer's wholesale column is NULL."""
    cur = con.cursor()
    cols = [c[1] for c in cur.execute("PRAGMA table_info(sku_costs)").fetchall()]
    needed = list({COSTS_COL[s] for s in COSTS_COL})
    select_cols = ["sku"] + [c for c in needed if c in cols]
    rows = cur.execute(f"SELECT {', '.join(select_cols)} FROM sku_costs").fetchall()
    by_sku: dict[str, dict[str, float]] = {}
    for row in rows:
        sku = row[0]
        d = {}
        for col, val in zip(select_cols[1:], row[1:]):
            d[col] = val
        by_sku[sku] = d
    pack_msrp = {
        sku: (pack or 12, msrp or 10.0)
        for sku, pack, msrp in cur.execute(
            "SELECT sku, case_pack_qty, msrp FROM product_master"
        ).fetchall()
    }
    out: dict[tuple[str, str], float] = {}
    for slug, col in COSTS_COL.items():
        for sku, costs in by_sku.items():
            pack, msrp = pack_msrp.get(sku, (12, 10.0))
            v = costs.get(col)
            if v is None:
                v = msrp * 0.55
            out[(slug, sku)] = float(v) * pack
    return out


def random_date_in_month(rng: random.Random, year: int, month: int) -> date:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    days_in_month = (next_month - date(year, month, 1)).days
    return date(year, month, rng.randint(1, days_in_month))


def make_po_number(rng: random.Random, slug: str, seq: int) -> str:
    """Retailer-flavored PO number for realism in the UI."""
    if slug == "walmart":
        return f"{6_000_000_000 + seq:010d}"
    if slug == "costco":
        return f"C{500_000_000 + seq:09d}"
    if slug == "whole_foods":
        regions = ["NA", "MA", "MW", "RM", "NC", "SP", "FL", "SO", "SW"]
        return f"{rng.choice(regions)}-{800_000 + seq}"
    if slug == "unfi":
        return f"{1_500_000 + seq:07d}"
    if slug == "kehe":
        return f"K{900_000 + seq:07d}"
    return f"{slug.upper()[:4]}-{100_000 + seq}"


def main() -> None:
    rng = random.Random(SEED)
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()

        # Wipe any prior orders/lines (idempotent regen)
        cur.execute("DELETE FROM order_lines")
        cur.execute("DELETE FROM orders")

        auth = authorized_skus(con)
        first_auth = first_auth_date(con)
        prices = load_prices(con)

        # Sanity: warn about retailers with no authorized SKUs
        for slug in RETAILER_CONFIG:
            if not auth.get(slug):
                print(f"  [WARN] {slug}: no authorized SKUs; skipping.")

        months = months_in_window()
        orders: list[tuple] = []
        order_lines: list[tuple] = []
        seq = {slug: 0 for slug in RETAILER_CONFIG}

        for slug, cfg in RETAILER_CONFIG.items():
            sku_pool = auth.get(slug, [])
            if not sku_pool:
                continue
            for y, m in months:
                n = max(0, int(rng.gauss(cfg["per_month"], cfg["per_month"] ** 0.5)))
                for _ in range(n):
                    seq[slug] += 1
                    po_date = random_date_in_month(rng, y, m)
                    po_number = make_po_number(rng, slug, seq[slug])
                    order_id = f"{slug.upper()[:4]}-{po_date.year}-{seq[slug]:06d}"

                    # Filter SKU pool to those authorized as of po_date
                    eligible = [
                        sku for sku in sku_pool
                        if (slug, sku) not in first_auth or first_auth[(slug, sku)] <= po_date
                    ]
                    if not eligible:
                        seq[slug] -= 1
                        continue

                    n_lines = rng.randint(cfg["lines"][0], cfg["lines"][1])
                    n_lines = min(n_lines, len(eligible))
                    line_skus = rng.sample(eligible, n_lines)

                    u_min, u_max, u_mode = cfg["units"]
                    total_units = 0
                    total_value = 0.0
                    line_rows = []
                    for sku in line_skus:
                        units = max(u_min, int(rng.triangular(u_min, u_max, u_mode)))
                        price = prices.get((slug, sku), 5.50)
                        line_total = round(units * price, 2)
                        total_units += units
                        total_value += line_total
                        line_rows.append((order_id, sku, units, round(price, 2), line_total))

                    ship_lead = rng.randint(5, 14)
                    requested_ship = po_date + timedelta(days=ship_lead)
                    window_start = requested_ship + timedelta(days=2)
                    window_end   = requested_ship + timedelta(days=5)

                    orders.append((
                        order_id, slug, po_number,
                        po_date.isoformat(),
                        requested_ship.isoformat(),
                        window_start.isoformat(),
                        window_end.isoformat(),
                        None,  # dc_id — populated later if needed
                        total_units,
                        round(total_value, 2),
                    ))
                    order_lines.extend(line_rows)

        cur.executemany("""
            INSERT INTO orders (
                order_id, retailer_id, po_number, po_date, requested_ship_date,
                requested_delivery_window_start, requested_delivery_window_end,
                dc_id, total_units, total_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, orders)
        cur.executemany("""
            INSERT INTO order_lines (order_id, sku, units_ordered, unit_price, line_total)
            VALUES (?, ?, ?, ?, ?)
        """, order_lines)
        con.commit()

        # Summary
        n_orders = len(orders)
        n_lines = len(order_lines)
        total_value = sum(o[9] for o in orders)
        months_in_window_count = len(months)
        annualized = total_value * 12 / months_in_window_count

        print(f"\nInserted {n_orders:,} orders and {n_lines:,} order_lines.")
        print(f"Total order value: ${total_value:,.0f}")
        print(f"Annualized:        ${annualized:,.0f}  (target $20–30M)")
        print()
        print("Orders by retailer:")
        by_ret: dict[str, list[float]] = {}
        for o in orders:
            by_ret.setdefault(o[1], []).append(o[9])
        for slug in RETAILER_CONFIG:
            vals = by_ret.get(slug, [])
            if not vals:
                continue
            ann = sum(vals) * 12 / months_in_window_count
            print(f"  {slug:<22} {len(vals):>5}  ${sum(vals):>12,.0f}   ann ${ann:>11,.0f}")



if __name__ == "__main__":
    main()
