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

## Download the workbook

**[Cinderhaven_Trade_Diagnostic.xlsx](https://github.com/MsShawnP/trade-spend-data-diagnostic/releases/latest/download/Cinderhaven_Trade_Diagnostic.xlsx)** — 7-tab Excel diagnostic. Open it cold; Tab 1 has the punchline.

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
```

## For developers

The workbook is generated from a PostgreSQL database containing
Cinderhaven's simulated trade data (21 tables, trailing-365 window).

```bash
pip install -r requirements.txt
export DATABASE_URL=postgresql://...
python build_workbook.py
python validate_workbook.py   # 62 checks
```

Stack: Python 3.10+, openpyxl, psycopg2, PostgreSQL.

## License

MIT. See [LICENSE](LICENSE).

## Contact

Shawn P — msshawnp@gmail.com
