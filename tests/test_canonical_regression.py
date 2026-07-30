"""Canonical regression test for the Cinderhaven baked database.

Follows the TestCinderhavenValidatedRegression pattern: loads the baked
SQLite database and asserts that key figures match the canonical single
source of truth.  This pins the data contract so any re-export or schema
change is caught immediately.

Expected values are read from the vendored canonical SSOT
(``reference/canonical_values.yml``, keyed ``metric.basis.period``) rather
than hardcoded, so the contract tracks the platform's
VERIFIED-AGAINST-PRODUCTION figures.  Tolerances mirror
``cinderhaven-data-platform/scripts/check_canonical.py``: 2% on dollar
figures, 0.5 percentage points on rates.

The default period is ``cy2025`` (== ``trailing_12m`` in this dataset; scan
data ends 2025-12-27).  Every figure names its basis AND period.

The database is not committed (it is >100 MB and gitignored); it is either
extracted from the platform Postgres or rebuilt locally.  When it is absent
these DB-backed tests skip, exactly as they do in CI.
"""

import sqlite3
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "cinderhaven-data" / "data" / "cinderhaven_product_master.db"
CANONICAL_YAML = ROOT / "reference" / "canonical_values.yml"

# --- Canonical SSOT ---------------------------------------------------------

# Dollar figures come straight from the machine-readable SSOT.  Default period
# is cy2025 (== trailing_12m: scan data ends 2025-12-27).
CANONICAL = yaml.safe_load(CANONICAL_YAML.read_text(encoding="utf-8"))
REVENUE_CANONICAL = CANONICAL["revenue"]["retail_scan"]["cy2025"]  # 32,323,139.62
OP_WASTE_CANONICAL = CANONICAL["deductions"]["operational_waste_ex_billback"]["cy2025"]  # 344,655.01

# The rate-card structural / all-in figures are NOT in the YAML: the platform
# derives them in check_canonical.py and records them in
# CINDERHAVEN_CANONICAL.md § Trade Economics (VERIFIED-AGAINST-PRODUCTION
# 2026-07-29, read-only workflow run 30488858977).  They are pinned here as
# literals with that provenance.
#
# NOTE ON DENOMINATOR: these published rates sit on the canonical ~$32.8M
# trailing-52w denominator.  The retail_scan SSOT above is $32.32M (cy2025);
# the ~1.5% denominator gap is flagged in the canonical .md for an explicit
# owner re-rate decision and is intentionally NOT silently rewritten here.
# The 0.5pp tolerance comfortably absorbs the gap.
STRUCTURAL_RATE_CANONICAL = 0.098   # 9.8% of trailing-52w scan revenue
ALL_IN_RATE_CANONICAL = 0.110       # 11.0% of trailing-52w scan revenue
WASTE_RATE_CANONICAL = 0.012        # 1.2% of trailing-52w scan revenue
STRUCTURAL_ANNUAL_CANONICAL = 3_200_000  # ~$3.2M/yr (rate x trailing-52w channel revenue)

TOL_DOLLARS = 0.02      # 2% on dollar figures (check_canonical.py)
TOL_RATE_PP = 0.005     # 0.5 percentage points on rates (check_canonical.py)

# --- Helpers ----------------------------------------------------------------

# Canonical structural methodology (check_canonical.py rate_map): every retail
# scan channel is priced by its OWN trade_spend_pct column — no regional
# fallback for Kroger/Sprouts, which understated the old 9.0% figure.
CHANNEL_RATE_COLS = {
    "Walmart": "trade_spend_pct_walmart",
    "Costco": "trade_spend_pct_costco",
    "Whole Foods": "trade_spend_pct_whole_foods",
    "Sprouts": "trade_spend_pct_sprouts",
    "Kroger": "trade_spend_pct_kroger",
    "Regional Group": "trade_spend_pct_regional",
}


def _sku_cost_columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(sku_costs)").fetchall()}


def _trailing_bounds(conn: sqlite3.Connection) -> tuple[str, str]:
    """Return (oldest_week, max_scan) for trailing 52 weeks."""
    weeks = conn.execute(
        "SELECT DISTINCT week_ending FROM scan_data ORDER BY week_ending DESC LIMIT 52"
    ).fetchall()
    return weeks[-1][0], weeks[0][0]


def _avg_rate(conn: sqlite3.Connection, col: str) -> float:
    return conn.execute(f"SELECT AVG({col}) FROM sku_costs").fetchone()[0] or 0.0


def _compute_structural_trade(conn: sqlite3.Connection, oldest_week: str) -> float:
    """Structural trade = per-channel trailing-52w scan revenue x per-channel rate.

    Mirrors check_canonical.py: each scan channel is priced by its dedicated
    trade_spend_pct column.  Channels without a dedicated column (or absent in
    an older schema) fall back to the regional rate.
    """
    channel_rev = conn.execute(
        "SELECT s.retailer, SUM(sd.dollars_sold) "
        "FROM scan_data sd "
        "JOIN stores s ON sd.store_id = s.store_id "
        "WHERE sd.week_ending >= ? "
        "GROUP BY s.retailer",
        (oldest_week,),
    ).fetchall()

    cols = _sku_cost_columns(conn)
    regional_rate = _avg_rate(conn, "trade_spend_pct_regional") if "trade_spend_pct_regional" in cols else 0.0
    rate_map: dict[str, float] = {}
    for channel, col in CHANNEL_RATE_COLS.items():
        rate_map[channel] = _avg_rate(conn, col) if col in cols else regional_rate

    total = 0.0
    for retailer, rev in channel_rev:
        total += rev * rate_map.get(retailer, regional_rate)
    return total


def _operational_waste(conn: sqlite3.Connection, max_scan: str) -> float:
    """Retailer operational waste (ex promo_billback), trailing-365 day.

    ~= deductions.operational_waste_ex_billback.cy2025 in the SSOT.
    """
    return conn.execute(
        "SELECT SUM(amount) FROM deductions "
        "WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ? "
        "  AND deduction_type != 'promo_billback'",
        (max_scan, max_scan),
    ).fetchone()[0]


# --- Fixtures ---------------------------------------------------------------

@pytest.fixture(scope="module")
def conn():
    """Open a read-only connection to the baked database."""
    if not DB.exists():
        pytest.skip(f"Baked database not found at {DB}")
    connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    yield connection
    connection.close()


# --- Tests ------------------------------------------------------------------

class TestCinderhavenCanonicalRegression:
    """Pin the Cinderhaven data contract against the canonical SSOT.

    Expected values come from reference/canonical_values.yml (dollars) and the
    canonical .md § Trade Economics (rate-card rates), both
    VERIFIED-AGAINST-PRODUCTION 2026-07-29 (workflow run 30488858977).  Any
    change to the baked data that shifts these numbers beyond tolerance must
    be intentional.
    """

    # -- Dimension counts ----------------------------------------------------

    def test_sku_count(self, conn):
        """SKUs in product_master match canonical universe.skus_total."""
        expected = CANONICAL["universe"]["skus_total"]["all_time"]
        count = conn.execute("SELECT COUNT(*) FROM product_master").fetchone()[0]
        assert count == expected, f"Expected {expected} SKUs, got {count}"

    def test_product_line_count(self, conn):
        """Product lines match canonical universe.product_lines."""
        expected = CANONICAL["universe"]["product_lines"]["all_time"]
        lines = conn.execute(
            "SELECT DISTINCT product_line FROM product_master ORDER BY product_line"
        ).fetchall()
        line_names = [row[0] for row in lines]
        assert len(line_names) == expected, (
            f"Expected {expected} product lines, got {len(line_names)}: {line_names}"
        )

    def test_retailer_count(self, conn):
        """Retailers match canonical universe.retailers."""
        expected = CANONICAL["universe"]["retailers"]["all_time"]
        retailers = conn.execute(
            "SELECT name FROM retailers ORDER BY name"
        ).fetchall()
        retailer_names = [row[0] for row in retailers]
        assert len(retailer_names) == expected, (
            f"Expected {expected} retailers, got {len(retailer_names)}: {retailer_names}"
        )

    def test_store_retailers_present(self, conn):
        """Every contracted retailer appears in the stores table."""
        expected = CANONICAL["universe"]["retailers"]["all_time"]
        store_retailers = conn.execute(
            "SELECT DISTINCT retailer FROM stores ORDER BY retailer"
        ).fetchall()
        names = [row[0] for row in store_retailers]
        assert len(names) == expected, f"Expected {expected} store retailers, got {len(names)}: {names}"

    # -- Revenue & trade figures ---------------------------------------------

    @staticmethod
    def _within_pct(actual, expected, tol):
        """True when actual is within tol fraction of expected."""
        if expected == 0:
            return actual == 0
        return abs(actual - expected) / abs(expected) < tol

    @staticmethod
    def _within_pp(actual_rate, expected_rate, tol_pp):
        """True when two rates are within tol_pp percentage points."""
        return abs(actual_rate - expected_rate) <= tol_pp

    def test_revenue(self, conn):
        """Trailing-52w retail scan revenue ~ canonical retail_scan.cy2025 (== CY2025).

        SSOT: reference/canonical_values.yml revenue.retail_scan.cy2025
        = $32,323,139.62 (2% tolerance).
        """
        oldest, _ = _trailing_bounds(conn)
        revenue = conn.execute(
            "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
            (oldest,),
        ).fetchone()[0]
        assert self._within_pct(revenue, REVENUE_CANONICAL, TOL_DOLLARS), (
            f"Revenue {revenue:,.2f} outside 2% of canonical "
            f"retail_scan.cy2025 ${REVENUE_CANONICAL:,.2f}"
        )

    def test_operational_waste(self, conn):
        """Operational waste ~ canonical operational_waste_ex_billback.cy2025.

        SSOT: deductions.operational_waste_ex_billback.cy2025 = $344,655.01
        (retailer, ex promo_billback, 2% tolerance).
        """
        _, max_scan = _trailing_bounds(conn)
        waste = _operational_waste(conn, max_scan)
        assert self._within_pct(waste, OP_WASTE_CANONICAL, TOL_DOLLARS), (
            f"Operational waste {waste:,.2f} outside 2% of canonical "
            f"operational_waste_ex_billback.cy2025 ${OP_WASTE_CANONICAL:,.2f}"
        )

    def test_structural_trade(self, conn):
        """Structural trade ~ ~$3.2M/yr (rate-card x trailing-52w channel revenue).

        Source: CINDERHAVEN_CANONICAL.md § Trade Economics (2% tolerance).
        """
        oldest, _ = _trailing_bounds(conn)
        structural = _compute_structural_trade(conn, oldest)
        assert self._within_pct(structural, STRUCTURAL_ANNUAL_CANONICAL, TOL_DOLLARS), (
            f"Structural trade {structural:,.2f} outside 2% of canonical "
            f"~${STRUCTURAL_ANNUAL_CANONICAL:,.0f}/yr"
        )

    def test_structural_rate(self, conn):
        """Structural trade rate ~ 9.8% of trailing-52w scan revenue.

        Source: CINDERHAVEN_CANONICAL.md § Trade Economics (0.5pp tolerance;
        pinned on the canonical ~$32.8M denominator pending owner re-rate).
        """
        oldest, _ = _trailing_bounds(conn)
        revenue = conn.execute(
            "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
            (oldest,),
        ).fetchone()[0]
        rate = _compute_structural_trade(conn, oldest) / revenue
        assert self._within_pp(rate, STRUCTURAL_RATE_CANONICAL, TOL_RATE_PP), (
            f"Structural rate {rate*100:.1f}% outside 0.5pp of canonical "
            f"{STRUCTURAL_RATE_CANONICAL*100:.1f}%"
        )

    def test_all_in_rate(self, conn):
        """All-in trade rate ~ 11.0% of trailing-52w scan revenue.

        Source: CINDERHAVEN_CANONICAL.md § Trade Economics (0.5pp tolerance;
        pinned on the canonical ~$32.8M denominator pending owner re-rate).
        """
        oldest, max_scan = _trailing_bounds(conn)
        revenue = conn.execute(
            "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
            (oldest,),
        ).fetchone()[0]
        structural = _compute_structural_trade(conn, oldest)
        waste = _operational_waste(conn, max_scan)
        all_in = (structural + waste) / revenue
        assert self._within_pp(all_in, ALL_IN_RATE_CANONICAL, TOL_RATE_PP), (
            f"All-in rate {all_in*100:.1f}% outside 0.5pp of canonical "
            f"{ALL_IN_RATE_CANONICAL*100:.1f}%"
        )

    def test_waste_rate(self, conn):
        """Operational waste rate ~ 1.2% of trailing-52w scan revenue.

        Source: CINDERHAVEN_CANONICAL.md § Trade Economics (0.5pp tolerance;
        pinned on the canonical ~$32.8M denominator pending owner re-rate).
        """
        oldest, max_scan = _trailing_bounds(conn)
        revenue = conn.execute(
            "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
            (oldest,),
        ).fetchone()[0]
        rate = _operational_waste(conn, max_scan) / revenue
        assert self._within_pp(rate, WASTE_RATE_CANONICAL, TOL_RATE_PP), (
            f"Waste rate {rate*100:.2f}% outside 0.5pp of canonical "
            f"{WASTE_RATE_CANONICAL*100:.1f}%"
        )

    def test_disputes_total(self, conn):
        """Disputes present in the deduction lifecycle."""
        count = conn.execute("SELECT COUNT(*) FROM disputes").fetchone()[0]
        assert count > 3000, f"Expected >3,000 disputes, got {count}"
