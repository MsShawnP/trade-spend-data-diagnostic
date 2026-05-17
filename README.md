# Trade Spend Data Diagnostic — Cinderhaven Provisions

A complete trade spend diagnostic for a mid-market CPG company,
built from simulated data that mirrors the structure and messiness
of real retailer deduction feeds.

## The finding

Cinderhaven Provisions has $27.5M in trailing-twelve-month wholesale
revenue. The company budgets 18.9% for structural trade spend — the
negotiated rate-card cost of shelf access. The actual all-in cost is
26.1%. The 7.2-point gap is $2 million in annual operational waste:
deductions taken beyond the rate card, largely unclassified and
uncontested. Full methodology and detailed findings in
[`walkthrough.md`](walkthrough.md).

## What's in this repo

```
walkthrough.md              Full methodology and findings narrative
build_workbook.py           Generates the 7-tab diagnostic workbook
validate_workbook.py        59-check acceptance test suite
workbook/                   Workbook generation modules (one per tab)
sql/                        25 standalone diagnostic queries
cinderhaven-data/           Simulated dataset (git submodule, 30 tables)
scripts/                    Database build utilities
output/                     Generated workbook (.gitignored)
requirements.txt            Python dependencies
```

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

Output lands at `output/trade_spend_diagnostic.xlsx`.

## Deliverables

**Excel workbook** — 7-tab static diagnostic with the two-bucket
punchline, waste breakdown, promo ROI calculator, retailer P&L,
and full deduction ledger. Run `python build_workbook.py` to
generate.

**SQL query library** — 25 queries answering specific diagnostic
questions, from total revenue to ghost promo identification.
See [`sql/README.md`](sql/README.md).

## Stack

Python 3.10+, openpyxl, pandas, rapidfuzz, SQLite.

## License

Not yet determined.

## Contact

Shawn P — msshawnp@gmail.com
