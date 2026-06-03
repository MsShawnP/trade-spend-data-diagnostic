# Cinderhaven Provisions is leaking $1.1M of margin to operational waste

A trade spend diagnostic for a mid-market natural/specialty CPG
company. Cinderhaven budgets 17% for trade — the negotiated rate-card
cost of shelf access. The actual all-in cost is 20%. The 4-point
gap is $1.1 million per year in deductions taken beyond the rate card:
vague charges with no clear basis, short-ship charges, spoilage claims,
and compliance fines. Industry range is 19-23%. The structural rate
is competitive. The operational waste is not.

The diagnostic quantifies the gap, classifies every deduction into a
defensible taxonomy, identifies addressable waste, and provides a
retailer-by-retailer P&L showing where the margin erosion
concentrates.

## Data Contract

Cinderhaven canonical platform data: 50 SKUs across 5 product lines (Artisan Sauces, Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites), 6 contracted retailers (Walmart, Costco, Whole Foods, Sprouts, Kroger, Regional Group), 3 distributors (UNFI, KeHE, DPI Northwest) + 1 DTC channel (Shopify). Source: `CINDERHAVEN_CANONICAL.md` in `cinderhaven-data-platform`.

> **Note:** Current baked data contains 3 product lines from an earlier platform export. A re-export with all 5 lines is pending.

## Download the workbook

**Download:** trade_spend_diagnostic.xlsx

## Deliverables

**Excel workbook** — 7-tab diagnostic built from a trailing-365-day
dataset. Tab 1 leads with the finding and an industry benchmark.
Tabs 2-4 break down waste by category, promo ROI, and retailer risk
(with channel rollup). Tab 5 is the full deduction ledger. Tabs 6-7
are reference. Interactive inputs: adjustable recovery rate, promo
comparison window, per-retailer what-if trade rates.

**Executive memo** ([`EXECUTIVE_MEMO.md`](EXECUTIVE_MEMO.md)) —
one-page condensation: the finding, where the money goes, what to
do Monday morning.

**Defensibility log** ([`DEFENSIBILITY.md`](DEFENSIBILITY.md)) —
classification rules and rebuttal text for every deduction bucket.
Pre-empts the "your consultant doesn't understand our business"
pushback.

**Walkthrough** ([`walkthrough.md`](walkthrough.md)) — full
methodology, findings, and deliverable orientation for someone
evaluating whether this analysis is worth commissioning.

**SQL query library** — 25 queries answering specific diagnostic
questions, from total revenue to ghost promo identification.
See [`sql/README.md`](sql/README.md).

## What's in this repo

```
EXECUTIVE_MEMO.md           One-page CEO summary
DEFENSIBILITY.md            Deduction classification rules + rebuttals
walkthrough.md              Full methodology and findings narrative
build_workbook.py           Generates the 7-tab diagnostic workbook
validate_workbook.py        60-check acceptance test suite
workbook/                   Workbook generation modules (one per tab)
sql/                        25 standalone diagnostic queries
cinderhaven-data/           Simulated dataset (git submodule, 22 tables)
output/                     Generated workbook (.gitignored)
requirements.txt            Python dependencies
```

## Quick start

```bash
git clone --recurse-submodules <repo-url>
cd trade-spend-data-diagnostic
pip install -r requirements.txt
python build_workbook.py
python validate_workbook.py   # 60 checks
```

The `--recurse-submodules` flag is required — the `cinderhaven-data`
submodule contains the SQLite database. If you cloned without it:

```bash
git submodule update --init
```

Output lands at `output/trade_spend_diagnostic.xlsx`.

## Stack

Python 3.10+, openpyxl, pandas, rapidfuzz, SQLite.

## License

MIT. See [LICENSE](LICENSE).

## Contact

Shawn P — msshawnp@gmail.com

---
Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
