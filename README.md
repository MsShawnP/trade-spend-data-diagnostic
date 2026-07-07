# $977K of operational waste is hiding in Cinderhaven's deductions

A trade spend diagnostic for a mid-market natural/specialty CPG
company. Cinderhaven's structural trade rate (9.9% of scan
revenue) is competitive. The problem is operational:
~$977K per year in avoidable deductions — $417K of it vague, with
no clear basis and 33% lacking even a PO reference — that nobody
is classifying, nobody is contesting, and that Cinderhaven recovers
barely a fifth of (20.9%) when it does dispute. All-in trade cost
including waste is 12.2% of revenue — the 3-point delta above the
structural rate is where the recoverable money lives.

The diagnostic quantifies the waste, classifies every deduction
into a defensible taxonomy, identifies addressable waste, and
provides a retailer-by-retailer P&L showing where the margin
erosion concentrates.

## Data Contract

Cinderhaven canonical platform data: 50 SKUs across 5 product lines (Artisan Sauces, Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites), 6 contracted retailers (Walmart, Costco, Whole Foods, Sprouts, Kroger, Regional Group), 3 distributors (UNFI, KeHE, DPI Northwest) + 1 DTC channel (Shopify). Source: `CINDERHAVEN_CANONICAL.md` in `cinderhaven-data-platform`.

This diagnostic consumes the **distressed scenario** dataset —
baseline revenue, structural trade, and chargebacks are unchanged;
the deduction and dispute layers are regenerated with v1-style
operational mess (real vague deductions, explicit double-dips,
low recovery rates). See `CINDERHAVEN_CANONICAL.md` "Distressed
Scenario" section for full figure table.

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
validate_workbook.py        59-check acceptance test suite
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
python validate_workbook.py   # 59 checks
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
