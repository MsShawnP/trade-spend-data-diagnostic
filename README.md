# Cinderhaven Provisions is leaking $1M of margin to operational waste

A trade spend diagnostic for a mid-market natural/specialty CPG
company. Cinderhaven budgets 17% for trade — the negotiated rate-card
cost of shelf access. The actual all-in cost is 21%. The 4-point gap
is $1 million per year in deductions taken beyond the rate card:
compliance fines, logistics chargebacks, spoilage claims, and
charges with no clear basis. Industry range is 19-23%. The structural
rate is fine. The operational waste is not.

The diagnostic quantifies the gap, classifies every deduction into a
defensible taxonomy, identifies $933K in addressable waste, and
provides a retailer-by-retailer P&L showing where the margin erosion
concentrates.

## What ships

**Excel workbook** — 7-tab diagnostic built from a trailing-365-day
dataset. Tab 1 leads with the punchline and an industry benchmark.
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

## What's in this repo

```
EXECUTIVE_MEMO.md           One-page CEO summary
DEFENSIBILITY.md            Deduction classification rules + rebuttals
walkthrough.md              Full methodology and findings narrative
build_workbook.py           Generates the 7-tab diagnostic workbook
validate_workbook.py        62-check acceptance test suite
workbook/                   Workbook generation modules (one per tab)
dev/sql/                    25 standalone diagnostic queries (reference)
dev/powerbi/                Dashboard design docs + DAX measures (reference)
cinderhaven-data/           Simulated dataset (git submodule, 21 tables)
scripts/                    Database build utilities
output/                     Generated workbook (.gitignored)
```

## Reference artifacts (in `dev/`)

**SQL query library** — 25 queries in 6 categories answering specific
diagnostic questions, from total revenue to ghost promo detection.
See [`dev/sql/README.md`](dev/sql/README.md).

**Power BI design** — dashboard design docs, pre-exported CSVs, and
49 auto-generated DAX measures for a future interactive implementation.
See [`dev/powerbi/README.md`](dev/powerbi/README.md).

## Stack

Python 3.10+, openpyxl, pandas, rapidfuzz, SQLite.

## Quick start

```bash
git clone --recurse-submodules <repo-url>
cd trade-spend-data-diagnostic
pip install -r requirements.txt
python build_workbook.py
```

The `--recurse-submodules` flag is required — the `cinderhaven-data`
submodule contains the SQLite database. If you cloned without it:

```bash
git submodule update --init
```

Output: `output/trade_spend_diagnostic.xlsx`. Validation:
`python validate_workbook.py` (62 checks).

## License

Not yet determined.

## Contact

Shawn P — msshawnp@gmail.com
