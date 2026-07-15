"""Generate the `scan_data` table — weekly unit sales for every authorized
SKU x store x week.

Layered model:
  1. Per-SKU base velocity (top/mid/long-tail tier)
  2. Store retailer + volume tier multipliers (Costco bulk, etc.)
  3. Aggregated channel handling for UNFI-AGG and DTC-AGG
  4. Subcategory seasonality scaled by per-SKU seasonality_strength
  5. Per-SKU organic trend (growing / declining / plateau-then-decline)
  6. Cannibalization: new launches dent older same-line SKUs for 8-16 wk
  7. Promo lifts (with muted lift on dirty-data SKUs ~65% of the time)
  8. Launch ramp + pre-deauth decline + post-promo dip
  9. UNFI bulk-order cycle (lumpy 4-6 week peaks at the agg channel)
 10. DTC marketing spikes (6-8 weeks/year, 2-3x baseline)
 11. Stockouts: ~12 (sku, store) episodes of 1-3 weeks at zero units
 12. Multiplicative weekly noise
 13. Retailer-specific wholesale price for revenue calc

Note: this script also UPDATES distribution_log to deauthorize the 2 failed
launch SKUs at a date 16-24 weeks past their launch — that is what makes
"failed launch then deauthorized" consistent across tables.
"""

from __future__ import annotations

import random
import sqlite3
from collections import defaultdict
from datetime import date, timedelta

from shared import DB_PATH, REGIONAL_CHAIN_NAMES, gtin_invalid, upc_missing

SEED = 42

WEEK_1_START = date(2024, 1, 1)   # Monday
WEEK_1_END = date(2024, 1, 6)    # Saturday
TOTAL_WEEKS = 157

# Monthly seasonality multipliers per product line (1=Jan ... 12=Dec)
SAUCE_MONTHLY = {
    1: 1.30, 2: 1.20, 3: 1.00, 4: 0.95, 5: 0.90, 6: 0.80,
    7: 0.75, 8: 0.85, 9: 1.00, 10: 1.25, 11: 1.35, 12: 1.40,
}
COND_MONTHLY = {
    1: 0.85, 2: 0.80, 3: 0.95, 4: 1.05, 5: 1.35, 6: 1.45,
    7: 1.50, 8: 1.40, 9: 1.10, 10: 0.95, 11: 0.90, 12: 0.80,
}
PANTRY_MONTHLY = {
    1: 0.95, 2: 0.95, 3: 1.00, 4: 1.00, 5: 1.00, 6: 1.00,
    7: 1.00, 8: 1.00, 9: 1.05, 10: 1.05, 11: 1.15, 12: 1.20,
}
LINE_SEASONALITY = {
    "Artisan Sauces":       SAUCE_MONTHLY,
    "Specialty Condiments": COND_MONTHLY,
    "Pantry Staples":       PANTRY_MONTHLY,
}

RETAILER_MULT = {
    "Walmart":     1.0,
    "Costco":      3.0,
    "Whole Foods": 0.8,
    # All regional chains
    **{c: 0.7 for c in REGIONAL_CHAIN_NAMES},
}

VOLUME_TIER_MULT = {"A": 1.3, "B": 1.0, "C": 0.7}

PROMO_LIFT_RANGES = {
    "TPR":     (1.8, 2.5),
    "Display": (1.5, 2.0),
    "Feature": (2.0, 3.0),
    "BOGO":    (2.5, 3.5),
}

# UNFI is a distributor, not direct retail — sized at ~15-20% of total business
# (~$4-5M/yr wholesale). 70 equivalent doors lands UNFI in that range given the
# tier'd base velocities below.
UNFI_EQUIVALENT_DOORS = 70

# KeHE: smaller distributor, ~10-12% of total business
KEHE_EQUIVALENT_DOORS = 50

# Direct-to-consumer wholesale-equivalent revenue, split by SKU base velocity.
DTC_ANNUAL_REVENUE = 800_000

# Global multiplier on per-SKU base velocities to land total wholesale revenue
# at ~$23-27M/yr (Cinderhaven's actual scale). Scales physical retail and UNFI/KeHE
# proportionally; DTC is driven by DTC_ANNUAL_REVENUE and is unaffected.
# Recalibrated for 50-SKU catalog (was 0.66 for 90 SKUs).
VELOCITY_SCALE = 1.21


def date_to_week(d_str):
    if d_str is None:
        return None
    d = date.fromisoformat(d_str) if isinstance(d_str, str) else d_str
    return ((d - WEEK_1_START).days // 7) + 1


# ---------------------------------------------------------------------------
# Extracted helpers — each computes one pre-processing step for main().
# ---------------------------------------------------------------------------

def compute_shelf_delays(
    dist_rows: list, sku_defect_count: dict[str, int],
) -> dict[tuple[str, str], int]:
    """Time-to-shelf delay per (sku, store). Uses its own RNG to avoid disturbing main stream."""
    delay_rng = random.Random(SEED + 8)

    def delay_days_for(dc: int) -> int:
        if dc == 0:
            return delay_rng.randint(3, 7)
        if dc <= 2:
            return delay_rng.randint(14, 42)
        if dc <= 4:
            return delay_rng.randint(28, 56)
        return delay_rng.randint(42, 84)

    return {
        (sku, sid): delay_days_for(sku_defect_count.get(sku, 0))
        for sku, sid, _ad, _dd in dist_rows
    }


def find_ghost_pairs(
    dist_rows: list, sku_defect_count: dict[str, int],
) -> tuple[list[str], set[tuple[str, str]]]:
    """Find 2-3 worst-defect SKUs that never make it to shelf at 3-5 stores each."""
    ghost_rng = random.Random(SEED + 7)
    physical_stores_by_sku: dict[str, list[str]] = {}
    for sku, sid, _ad, _dd in dist_rows:
        if sid in ("UNFI-AGG", "KEHE-AGG", "DTC-AGG"):
            continue
        physical_stores_by_sku.setdefault(sku, []).append(sid)
    severe_skus = sorted(
        [s for s, n in sku_defect_count.items()
         if n >= 2 and len(physical_stores_by_sku.get(s, [])) >= 3],
        key=lambda s: (-sku_defect_count[s], s),
    )
    ghost_skus = severe_skus[:ghost_rng.randint(2, 3)]
    ghost_pairs: set[tuple[str, str]] = set()
    for gs in ghost_skus:
        candidates = physical_stores_by_sku.get(gs, [])
        n_stores = ghost_rng.randint(3, 5)
        chosen = ghost_rng.sample(candidates, min(n_stores, len(candidates)))
        for sid in chosen:
            ghost_pairs.add((gs, sid))
    return ghost_skus, ghost_pairs


def assign_organic_trends(
    rng: random.Random, products: dict,
) -> dict[str, tuple[str, float]]:
    """15% growing, 10% declining, 10% plateau-then-decline, rest stable."""
    pool = list(products.keys())
    rng.shuffle(pool)
    n_total = len(pool)
    n_growing = round(n_total * 0.15)
    n_declining = round(n_total * 0.10)
    n_plateau = round(n_total * 0.10)

    trends: dict[str, tuple[str, float]] = {}
    for s in pool[:n_growing]:
        trends[s] = ("growing", rng.uniform(0.10, 0.25))
    for s in pool[n_growing:n_growing + n_declining]:
        trends[s] = ("declining", rng.uniform(0.15, 0.30))
    for s in pool[n_growing + n_declining:n_growing + n_declining + n_plateau]:
        trends[s] = ("plateau_decline", rng.uniform(0.15, 0.30))
    return trends


def organic_trend_factor(
    sku: str, week: int, trends: dict[str, tuple[str, float]],
) -> float:
    info = trends.get(sku)
    if info is None:
        return 1.0
    pattern, mag = info
    progress = (week - 1) / max(1, TOTAL_WEEKS - 1)
    if pattern == "growing":
        return 1.0 + mag * (progress - 0.5)
    if pattern == "declining":
        return 1.0 - mag * (progress - 0.5)
    # plateau_decline: flat first half, then decline in second half
    if progress < 0.5:
        return 1.0
    half = (progress - 0.5) * 2
    return 1.0 - mag * half


def assign_seasonality_strength(
    rng: random.Random, products: dict,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for s in products:
        r = rng.random()
        if r < 0.10:
            result[s] = rng.uniform(0.20, 0.50)
        elif r < 0.25:
            result[s] = rng.uniform(1.40, 1.70)
        else:
            result[s] = rng.uniform(0.85, 1.15)
    return result


def compute_cannibalization(
    rng: random.Random, products: dict, sku_launch_week: dict[str, int],
) -> dict[str, list[tuple[int, int, float]]]:
    periods: dict[str, list[tuple[int, int, float]]] = defaultdict(list)
    for new_sku, lw in sku_launch_week.items():
        if lw <= 60:
            continue
        new_pl = products.get(new_sku, ("", ""))[0]
        targets = [
            t for t, lw_t in sku_launch_week.items()
            if t != new_sku and products.get(t, ("", ""))[0] == new_pl and lw_t < lw
        ]
        if not targets:
            continue
        n_targets = min(len(targets), rng.randint(2, 4))
        chosen = rng.sample(targets, n_targets)
        for tgt in chosen:
            duration = rng.randint(8, 16)
            factor = rng.uniform(0.85, 0.95)
            periods[tgt].append((lw, lw + duration, factor))
    return periods


def compute_unfi_bulk_weeks(rng: random.Random) -> set[int]:
    weeks: set[int] = set()
    nxt = rng.randint(2, 5)
    while nxt <= TOTAL_WEEKS:
        weeks.add(nxt)
        nxt += rng.randint(4, 6)
    return weeks


def compute_kehe_bulk_weeks(rng: random.Random) -> set[int]:
    weeks: set[int] = set()
    nxt = rng.randint(3, 6)
    while nxt <= TOTAL_WEEKS:
        weeks.add(nxt)
        nxt += rng.randint(5, 7)
    return weeks


def compute_dtc_spike_weeks(
    rng: random.Random, week_month: list[int],
) -> set[int]:
    holiday_weeks = [w for w in range(1, TOTAL_WEEKS + 1)
                     if week_month[w - 1] in (3, 5, 11, 12)]
    n_spikes = rng.randint(6, 8)
    pool = list(holiday_weeks) if holiday_weeks else list(range(1, TOTAL_WEEKS + 1))
    rng.shuffle(pool)
    return set(pool[:n_spikes])


def compute_stockout_blocks(
    rng: random.Random, sku_store_windows: dict, stores: dict,
) -> set[tuple[str, str, int]]:
    blocks: set[tuple[str, str, int]] = set()
    physical_pairs = [(sku, sid) for (sku, sid), windows in sku_store_windows.items()
                      if not stores[sid][2]
                      and any(la - aw >= 8 for aw, la in windows)]
    rng.shuffle(physical_pairs)
    for sku, sid in physical_pairs[:14]:
        windows = sku_store_windows.get((sku, sid), [])
        if not windows:
            continue
        aw, la = windows[0]
        duration = rng.randint(1, 3)
        if la - aw < duration + 4:
            continue
        start = rng.randint(aw + 4, la - duration)
        for wk in range(start, start + duration):
            blocks.add((sku, sid, wk))
    return blocks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    rng = random.Random(SEED)
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as con:
        con.execute("PRAGMA journal_mode = WAL")
        con.execute("PRAGMA synchronous = OFF")
        cur = con.cursor()

        # --- Load reference data ---
        products = {
            sku: (pl, subc)
            for sku, pl, subc in cur.execute(
                "SELECT sku, product_line, subcategory FROM product_master"
            ).fetchall()
        }

        wholesale: dict[str, dict[str, float]] = {}
        for sku, w_walmart, w_costco, w_wf, w_regional, w_unfi, w_kehe, w_dtc, w_base in cur.execute("""
            SELECT sku, wholesale_walmart, wholesale_costco, wholesale_whole_foods,
                   wholesale_regional, wholesale_unfi, wholesale_kehe, wholesale_dtc, wholesale_price
            FROM sku_costs
        """).fetchall():
            wholesale[sku] = {
                "Walmart":     w_walmart,
                "Costco":      w_costco,
                "Whole Foods": w_wf,
                "Regional":    w_regional,
                "UNFI":        w_unfi,
                "KeHE":        w_kehe,
                "DTC":         w_dtc,
                "_base":       w_base,
            }
        stores = {
            sid: (ret, vt, bool(is_agg))
            for sid, ret, vt, is_agg in cur.execute(
                "SELECT store_id, retailer, volume_tier, is_aggregated_channel FROM stores"
            ).fetchall()
        }

        def wholesale_for(sku: str, store_retailer: str) -> float:
            if store_retailer in REGIONAL_CHAIN_NAMES:
                cat = "Regional"
            else:
                cat = store_retailer
            return wholesale[sku].get(cat, wholesale[sku].get("_base", 1.0))

        # Per-SKU defect map
        defect_rows = cur.execute("""
            SELECT sku, gtin14, upc, case_length_in, case_width_in, case_height_in,
                   brand_owner, country_of_origin
            FROM product_master
        """).fetchall()
        sku_has_defects: dict[str, bool] = {}
        sku_defect_count: dict[str, int] = {}
        for sku_, gtin, upc, l, ww, h, brand, country in defect_rows:
            n = 0
            if gtin_invalid(gtin):
                n += 1
            if upc_missing(upc):
                n += 1
            if l is None or ww is None or h is None:
                n += 1
            if brand is None or str(brand).strip() == "":
                n += 1
            if country is None or str(country).strip() == "":
                n += 1
            sku_defect_count[sku_] = n
            sku_has_defects[sku_] = n > 0

        dist_rows = cur.execute(
            "SELECT sku, store_id, authorized_date, deauthorized_date FROM distribution_log"
        ).fetchall()

        # --- Pre-compute independent layers ---
        sku_store_delay_days = compute_shelf_delays(dist_rows, sku_defect_count)
        ghost_skus, ghost_pairs = find_ghost_pairs(dist_rows, sku_defect_count)

        # --- Tier inference: rank SKUs by # of distribution rows ---
        sku_row_counts: dict[str, int] = defaultdict(int)
        for sku, _, _, _ in dist_rows:
            sku_row_counts[sku] += 1

        sku_tier = {}
        n_skus = len(sku_row_counts)
        n_top = max(1, round(n_skus * 0.20))
        n_mid = max(1, round(n_skus * 0.50))
        for i, (sku, _) in enumerate(
            sorted(sku_row_counts.items(), key=lambda kv: -kv[1])
        ):
            sku_tier[sku] = "top" if i < n_top else ("mid" if i < n_top + n_mid else "longtail")

        for sku in products:
            sku_tier.setdefault(sku, "longtail")

        # --- Per-SKU base velocity (units / store / week) ---
        base_velocity = {}
        for sku, tier in sku_tier.items():
            if tier == "top":
                base_velocity[sku] = rng.uniform(8, 15) * VELOCITY_SCALE
            elif tier == "mid":
                base_velocity[sku] = rng.uniform(3, 7) * VELOCITY_SCALE
            else:
                base_velocity[sku] = rng.uniform(0.5, 2) * VELOCITY_SCALE

        # --- Per-SKU launch week (min authorized_date) ---
        sku_launch_week: dict[str, int] = {}
        for sku, _, ad, _ in dist_rows:
            wk = date_to_week(ad)
            if sku not in sku_launch_week or wk < sku_launch_week[sku]:
                sku_launch_week[sku] = wk

        late_launch_skus = [s for s, lw in sku_launch_week.items() if lw > 60]

        # Pick 2 "failed launches" weighted by defect count
        failed_candidates = [s for s in sorted(late_launch_skus) if s not in ghost_skus]
        failed_launch_skus: set[str] = set()
        if failed_candidates:
            weights = [1 + 5 * sku_defect_count.get(s, 0) for s in failed_candidates]
            attempts = 0
            while len(failed_launch_skus) < min(2, len(failed_candidates)) and attempts < 50:
                pick = rng.choices(failed_candidates, weights=weights, k=1)[0]
                failed_launch_skus.add(pick)
                attempts += 1

        # --- Update distribution_log to deauthorize failed-launch SKUs ---
        failed_deauth_week = {}
        for sku in sorted(failed_launch_skus):
            lw = sku_launch_week[sku]
            deauth_w = min(TOTAL_WEEKS, lw + rng.randint(16, 24))
            failed_deauth_week[sku] = deauth_w
            deauth_date = (WEEK_1_START + timedelta(weeks=deauth_w - 1)).isoformat()
            active_rows = cur.execute(
                "SELECT rowid FROM distribution_log "
                "WHERE sku = ? AND deauthorized_date IS NULL "
                "AND store_id NOT IN ('UNFI-AGG','KEHE-AGG','DTC-AGG')",
                (sku,)
            ).fetchall()
            if active_rows:
                n_deauth = min(len(active_rows), rng.randint(3, 8))
                chosen_rowids = rng.sample([r[0] for r in active_rows], n_deauth)
                cur.executemany(
                    "UPDATE distribution_log SET deauthorized_date = ? WHERE rowid = ?",
                    [(deauth_date, rid) for rid in chosen_rowids],
                )
        con.commit()

        dist_rows = cur.execute(
            "SELECT sku, store_id, authorized_date, deauthorized_date FROM distribution_log"
        ).fetchall()

        # --- Build (sku, store_id) -> list of promo intervals ---
        sku_authorized_stores: dict[str, set[str]] = defaultdict(set)
        for sku, sid, _, _ in dist_rows:
            sku_authorized_stores[sku].add(sid)

        stores_by_cat: dict[str, list[str]] = defaultdict(list)
        for sid, (ret, _vt, is_agg) in stores.items():
            if is_agg:
                continue
            cat = ret if ret in ("Walmart", "Costco", "Whole Foods", "UNFI", "KeHE", "DTC") else "Regional"
            stores_by_cat[cat].append(sid)
        stores_by_cat["UNFI"].append("UNFI-AGG")
        stores_by_cat["KeHE"].append("KEHE-AGG")
        stores_by_cat["DTC"].append("DTC-AGG")

        promo_rows = cur.execute("""
            SELECT promo_id, sku, retailer, store_scope, start_week, end_week,
                   duration_weeks, discount_depth_pct, promo_type
            FROM promotions
        """).fetchall()

        sku_store_windows: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
        for sku, sid, ad, dd in dist_rows:
            aw = date_to_week(ad)
            last_active = (date_to_week(dd) - 1) if dd else TOTAL_WEEKS
            sku_store_windows[(sku, sid)].append((aw, last_active))

        sku_store_promos: dict[tuple[str, str], list] = defaultdict(list)
        stranded_promos = 0
        promo_eligible_counts = []

        for promo_id, sku, retailer, scope, sw_str, ew_str, _dur, disc, ptype in promo_rows:
            sw = date_to_week(sw_str)
            ew = date_to_week(ew_str)
            eligible = [s for s in stores_by_cat.get(retailer, []) if s in sku_authorized_stores[sku]]
            if scope == "subset" and eligible:
                n = max(1, int(round(len(eligible) * rng.uniform(0.30, 0.50))))
                eligible = rng.sample(eligible, min(n, len(eligible)))

            in_window = []
            for sid in eligible:
                for aw, last_active in sku_store_windows.get((sku, sid), []):
                    if aw <= ew and last_active >= sw:
                        in_window.append(sid)
                        break

            promo_eligible_counts.append((promo_id, sku, len(eligible), len(in_window)))
            if not in_window:
                stranded_promos += 1
                continue

            dip_end = ew + rng.choice([2, 3])
            for sid in in_window:
                sku_store_promos[(sku, sid)].append((sw, ew, ptype, disc, dip_end))

        # --- Decline-end factor per (sku, store_id) for non-failed-launch deauths ---
        decline_end_factor = {}
        for sku, sid, _ad, dd in dist_rows:
            if dd and sku not in failed_launch_skus:
                decline_end_factor[(sku, sid)] = rng.uniform(0.4, 0.6)

        # --- DTC dollar split: weight by base velocity ---
        dtc_skus = {sku for sku, sid, _, _ in dist_rows if sid == "DTC-AGG"}
        dtc_base_total = sum(base_velocity[s] for s in dtc_skus) or 1.0
        dtc_weekly_total = DTC_ANNUAL_REVENUE / 52
        dtc_weekly_dollars = {
            s: dtc_weekly_total * base_velocity[s] / dtc_base_total for s in dtc_skus
        }

        # --- Pre-compute week dates and months ---
        week_end_iso = [(WEEK_1_END + timedelta(weeks=w - 1)).isoformat() for w in range(1, TOTAL_WEEKS + 1)]
        week_month = [(WEEK_1_END + timedelta(weeks=w - 1)).month for w in range(1, TOTAL_WEEKS + 1)]

        # --- Apply extracted helper layers ---
        sku_organic_trend = assign_organic_trends(rng, products)
        sku_seasonality_strength = assign_seasonality_strength(rng, products)
        cannibalization_periods = compute_cannibalization(rng, products, sku_launch_week)
        unfi_bulk_weeks = compute_unfi_bulk_weeks(rng)
        kehe_bulk_weeks = compute_kehe_bulk_weeks(rng)
        dtc_spike_weeks = compute_dtc_spike_weeks(rng, week_month)
        stockout_blocks = compute_stockout_blocks(rng, sku_store_windows, stores)

        # --- Build scan_data ---
        cur.execute("DROP TABLE IF EXISTS scan_data")
        cur.execute("""
            CREATE TABLE scan_data (
                sku          TEXT NOT NULL,
                store_id     TEXT NOT NULL,
                week_ending  TEXT NOT NULL,
                units_sold   INTEGER NOT NULL,
                dollars_sold REAL NOT NULL,
                PRIMARY KEY (sku, store_id, week_ending)
            )
        """)

        BATCH = 100_000
        buffer = []
        n_rows_total = 0

        insert_sql = (
            "INSERT INTO scan_data (sku, store_id, week_ending, units_sold, dollars_sold) "
            "VALUES (?, ?, ?, ?, ?)"
        )

        for sku, sid, ad, dd in dist_rows:
            if (sku, sid) in ghost_pairs:
                continue

            product_line, _subc = products[sku]
            seasonality = LINE_SEASONALITY[product_line]
            store_ret, store_vt, is_agg = stores[sid]
            ws_price = wholesale_for(sku, store_ret)

            deauth_w = date_to_week(dd) if dd else None

            delay_days = sku_store_delay_days.get((sku, sid), 0)
            target_d = date.fromisoformat(ad) + timedelta(days=delay_days)
            delta = (target_d - WEEK_1_END).days
            first_w = 1 if delta <= 0 else (delta + 6) // 7 + 1
            first_w = max(first_w, 1)

            last_w = min(TOTAL_WEEKS, (deauth_w - 1) if deauth_w else TOTAL_WEEKS)
            if first_w > last_w:
                continue

            sku_base = base_velocity[sku]
            is_failed = sku in failed_launch_skus
            sku_launch = sku_launch_week.get(sku, 1)
            sku_dirty = sku_has_defects.get(sku, False)
            season_strength = sku_seasonality_strength.get(sku, 1.0)
            cannib_list = cannibalization_periods.get(sku, [])

            if is_agg:
                if sid == "UNFI-AGG":
                    base_per_week = sku_base * UNFI_EQUIVALENT_DOORS
                elif sid == "KEHE-AGG":
                    base_per_week = sku_base * KEHE_EQUIVALENT_DOORS
                else:
                    base_per_week = dtc_weekly_dollars.get(sku, 0.0) / max(ws_price, 1.0)
            else:
                ret_mult = RETAILER_MULT.get(store_ret, 1.0)
                tier_mult = VOLUME_TIER_MULT.get(store_vt, 1.0)
                base_per_week = sku_base * ret_mult * tier_mult

            promos = sku_store_promos.get((sku, sid), [])
            decline_floor = decline_end_factor.get((sku, sid))

            for w in range(first_w, last_w + 1):
                if (sku, sid, w) in stockout_blocks:
                    buffer.append((sku, sid, week_end_iso[w - 1], 0, 0.0))
                    if len(buffer) >= BATCH:
                        cur.executemany(insert_sql, buffer)
                        n_rows_total += len(buffer)
                        buffer.clear()
                    continue

                seasonal_raw = seasonality[week_month[w - 1]]
                seasonal = 1.0 + (seasonal_raw - 1.0) * season_strength

                trend = organic_trend_factor(sku, w, sku_organic_trend)

                cannib = 1.0
                for cs, ce, cf in cannib_list:
                    if cs <= w <= ce:
                        cannib = cf
                        break

                if sku_launch > 1:
                    wsl = w - sku_launch + 1
                    if is_failed:
                        if wsl <= 4:
                            ramp = rng.uniform(0.30, 0.50)
                        else:
                            ramp = rng.uniform(0.40, 0.50)
                    else:
                        if wsl <= 4:
                            ramp = rng.uniform(0.30, 0.50)
                        elif wsl <= 8:
                            ramp = rng.uniform(0.50, 0.70)
                        elif wsl <= 13:
                            ramp = rng.uniform(0.70, 0.90)
                        else:
                            ramp = 1.0
                else:
                    ramp = 1.0

                decline = 1.0
                if decline_floor is not None and deauth_w is not None:
                    weeks_to_deauth = deauth_w - w
                    if 0 < weeks_to_deauth <= 10:
                        progress = (10 - weeks_to_deauth) / 10
                        decline = 1.0 - progress * (1.0 - decline_floor)

                promo_mult = 1.0
                promo_active = False
                promo_discount = 0.0
                for sw, ew, ptype, disc, dip_end in promos:
                    if sw <= w <= ew:
                        lo, hi = PROMO_LIFT_RANGES[ptype]
                        raw_lift = rng.uniform(lo, hi)
                        if sku_dirty and rng.random() < 0.65:
                            raw_lift = 1.0 + (raw_lift - 1.0) * rng.uniform(0.30, 0.55)
                        promo_mult = raw_lift
                        promo_active = True
                        promo_discount = disc
                        break
                    if ew < w <= dip_end:
                        promo_mult = rng.uniform(0.70, 0.85)
                        break

                agg_cycle = 1.0
                if sid == "UNFI-AGG":
                    if w in unfi_bulk_weeks:
                        agg_cycle = rng.uniform(2.2, 2.8)
                    else:
                        agg_cycle = rng.uniform(0.55, 0.80)
                elif sid == "KEHE-AGG":
                    if w in kehe_bulk_weeks:
                        agg_cycle = rng.uniform(2.0, 2.5)
                    else:
                        agg_cycle = rng.uniform(0.60, 0.85)
                elif sid == "DTC-AGG" and w in dtc_spike_weeks:
                    agg_cycle = rng.uniform(2.0, 3.0)

                noise = rng.uniform(0.75, 1.25)

                v = (base_per_week * seasonal * trend * cannib
                     * ramp * decline * promo_mult * agg_cycle * noise)
                units = max(0, int(round(v)))

                effective_price = ws_price * (1 - promo_discount) if promo_active else ws_price
                dollars = round(units * effective_price, 2)

                buffer.append((sku, sid, week_end_iso[w - 1], units, dollars))

                if len(buffer) >= BATCH:
                    cur.executemany(insert_sql, buffer)
                    n_rows_total += len(buffer)
                    buffer.clear()

        if buffer:
            cur.executemany(insert_sql, buffer)
            n_rows_total += len(buffer)
            buffer.clear()

        cur.execute("CREATE INDEX idx_scan_sku ON scan_data(sku)")
        cur.execute("CREATE INDEX idx_scan_store ON scan_data(store_id)")
        cur.execute("CREATE INDEX idx_scan_week ON scan_data(week_ending)")
        con.commit()

        # --- Summary ---
        print(f"Total scan_data rows inserted: {n_rows_total:,}\n")

        print(f"Failed-launch SKUs (stalled & deauthorized): {sorted(failed_launch_skus)}")
        for sku in sorted(failed_launch_skus):
            lw = sku_launch_week[sku]
            dw = failed_deauth_week[sku]
            launch_d = (WEEK_1_END + timedelta(weeks=lw - 1)).isoformat()
            deauth_d = (WEEK_1_START + timedelta(weeks=dw - 1)).isoformat()
            print(f"  {sku}: launched week {lw} ({launch_d}) -> deauthorized week {dw} ({deauth_d})")

        print(f"\nGhost SKUs (authorized, NO scan data): {sorted(ghost_skus)}")
        by_ghost: dict[str, list[str]] = {}
        for sku, sid in sorted(ghost_pairs):
            by_ghost.setdefault(sku, []).append(sid)
        for sku, sids in by_ghost.items():
            print(f"  {sku}: {len(sids)} stores never scanned ({sku_defect_count[sku]} defects)")

        print("\nFirst-scan gap from auth_date (sample by defect bucket):")
        bucket_gaps: dict[int, list[int]] = {0: [], 1: [], 2: [], 3: []}
        for (sku, sid), delay in sku_store_delay_days.items():
            if (sku, sid) in ghost_pairs:
                continue
            dc = sku_defect_count.get(sku, 0)
            b = 0 if dc == 0 else (1 if dc <= 2 else (2 if dc <= 4 else 3))
            bucket_gaps[b].append(delay)
        labels = {0: "Clean (0)", 1: "Minor (1-2)", 2: "Moderate (3-4)", 3: "Severe (5+)"}
        for b in (0, 1, 2, 3):
            vals = bucket_gaps[b]
            if vals:
                print(
                    f"  {labels[b]:<16} n={len(vals):>5}  delay days"
                    f" mean={sum(vals)/len(vals):>5.1f}  min={min(vals)}  max={max(vals)}"
                )

        print("\nUnits sold by retailer category:")
        rows = cur.execute("""
            SELECT
                CASE
                    WHEN s.is_aggregated_channel = 1 THEN s.retailer || ' (agg)'
                    WHEN s.retailer IN ('Walmart','Costco','Whole Foods') THEN s.retailer
                    ELSE 'Regional'
                END AS cat,
                COUNT(*) AS rows,
                SUM(d.units_sold) AS units,
                ROUND(SUM(d.dollars_sold), 0) AS dollars
            FROM scan_data d JOIN stores s ON d.store_id = s.store_id
            GROUP BY cat ORDER BY units DESC
        """).fetchall()
        print(f"  {'Category':<18} {'Rows':>10} {'Units':>14} {'$ (2yr ws)':>14} {'$ (annual)':>14} {'% of total':>10}")
        total_dollars = sum(d for _, _, _, d in rows)
        for cat, n, u, dol in rows:
            annual = dol / 2.0
            pct = 100.0 * dol / total_dollars if total_dollars else 0
            print(f"  {cat:<18} {n:>10,} {u:>14,} {dol:>14,.0f} {annual:>14,.0f} {pct:>9.1f}%")
        print(f"  {'TOTAL':<18} {'':>10} {'':>14} {total_dollars:>14,.0f} {total_dollars/2:>14,.0f}")

        print("\nUnits sold by tier:")
        tier_units: dict[str, int] = defaultdict(int)
        tier_rows: dict[str, int] = defaultdict(int)
        sku_tier_rows = cur.execute("SELECT sku, SUM(units_sold), COUNT(*) FROM scan_data GROUP BY sku").fetchall()
        for sku, u, n in sku_tier_rows:
            tier_units[sku_tier[sku]] += u or 0
            tier_rows[sku_tier[sku]] += n
        for tier in ("top", "mid", "longtail"):
            print(f"  {tier:<10} units={tier_units[tier]:>12,}  rows={tier_rows[tier]:>10,}")

        print("\nWeekly dollars sold (head and tail of the time window):")
        rows = cur.execute("""
            SELECT week_ending, SUM(units_sold), ROUND(SUM(dollars_sold), 0)
            FROM scan_data GROUP BY week_ending ORDER BY week_ending
        """).fetchall()
        for r in rows[:3]:
            print(f"  {r[0]}  units={r[1]:>8,}  $={r[2]:>12,.0f}")
        print("  ...")
        for r in rows[-3:]:
            print(f"  {r[0]}  units={r[1]:>8,}  $={r[2]:>12,.0f}")

        print(f"\nStranded promos (no in-window stores after guard): {stranded_promos}")
        partially_pruned = sum(1 for _, _, pre, post in promo_eligible_counts if 0 < post < pre)
        print(f"Promos partially pruned by guard:               {partially_pruned}")

        print("\nPromo lift spot-check (10 sample promos at affected retailer stores):")
        print(f"  {'Promo':<12} {'SKU':<10} {'Retailer':<14} {'Type':<8} {'Baseline':>10} {'OnPromo':>10} {'Lift':>7}")
        spot_rows = cur.execute("""
            SELECT pd.promo_id, pd.sku, pd.retailer, pd.promo_type,
                (SELECT AVG(d.units_sold) FROM scan_data d
                 JOIN stores s ON d.store_id = s.store_id
                 WHERE d.sku = pd.sku
                   AND (s.retailer = pd.retailer
                        OR (pd.retailer = 'Regional' AND s.retailer IN
                            ('Kroger','Sprouts','Regional Group')))
                   AND d.week_ending NOT BETWEEN pd.start_week AND pd.end_week) AS base_avg,
                (SELECT AVG(d.units_sold) FROM scan_data d
                 JOIN stores s ON d.store_id = s.store_id
                 WHERE d.sku = pd.sku
                   AND (s.retailer = pd.retailer
                        OR (pd.retailer = 'Regional' AND s.retailer IN
                            ('Kroger','Sprouts','Regional Group')))
                   AND d.week_ending BETWEEN pd.start_week AND pd.end_week) AS promo_avg
            FROM (SELECT DISTINCT promo_id, sku, retailer, start_week, end_week, promo_type FROM promotions) pd
            WHERE pd.retailer NOT IN ('UNFI', 'KeHE', 'DTC')
            ORDER BY pd.promo_id LIMIT 10
        """).fetchall()
        for promo_id, sku, ret, ptype, base, on in spot_rows:
            if base and on and base > 0:
                print(f"  {promo_id:<12} {sku:<10} {ret:<14} {ptype:<8} {base:>10.2f} {on:>10.2f} {on/base:>6.2f}x")
            else:
                print(f"  {promo_id:<12} {sku:<10} {ret:<14} {ptype:<8} {(base or 0):>10.2f} {(on or 0):>10.2f}    n/a")


if __name__ == "__main__":
    main()
