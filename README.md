# Trade Spend Data Diagnostic — Cinderhaven Provisions

A complete trade spend diagnostic for a mid-market CPG company,
built from simulated data that mirrors the structure and messiness
of real retailer deduction feeds.

## The finding

Cinderhaven Provisions has $25.6M in trailing-twelve-month wholesale
revenue. The company budgets 17.3% for structural trade spend — the
negotiated rate-card cost of shelf access. The actual all-in cost is
21.3%. The 4-point gap is $1 million in annual operational waste:
deductions taken beyond the rate card, largely unclassified and
uncontested. Full methodology and detailed findings in
[`walkthrough.md`](walkthrough.md).

## What's in this repo

```
walkthrough.md              Full methodology and findings narrative
build_workbook.py           Generates the 7-tab diagnostic workbook
validate_workbook.py        43-check acceptance test suite
workbook/                   Workbook generation modules (one per tab)
  db.py                     Database connection wrapper (Postgres)
sql/                        25 standalone diagnostic queries
powerbi/                    Dashboard design, data exports, DAX measures, build guide
scripts/                    Database connectivity utilities
output/                     Generated workbook (.gitignored)
requirements.txt            Python dependencies
```

## Data Source

This project reads from the **Cinderhaven Data Platform** — a Postgres
database with dbt-managed staging, intermediate, and mart tables,
hosted on Fly.io with local Docker for development.

To run locally, start the shared Docker Postgres from
[refactor-older-cinderhaven-projects](https://github.com/MsShawnP/refactor-older-cinderhaven-projects):

```bash
# In the refactor-older-cinderhaven-projects repo:
docker compose up

# Then in this repo:
cp .env.example .env
python build_workbook.py
```

The original SQLite database and `cinderhaven-data` git submodule have
been replaced. See git tag `v1.0-sqlite` for the pre-migration state.

## Quick start

```bash
git clone <repo-url>
cd trade-spend-data-diagnostic
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL if not using local Docker
python build_workbook.py
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

**Power BI dashboard** — 4-page interactive companion with
cross-filtering, drill-through, and what-if parameters. Assembled
manually in Power BI Desktop from pre-exported CSVs and 49
auto-generated DAX measures. See
[`powerbi/README.md`](powerbi/README.md).

## Stack

Python 3.10+, openpyxl, psycopg2, Postgres (Cinderhaven Data Platform).

## License

MIT — see [LICENSE](LICENSE).

## Contact

Shawn P — msshawnp@gmail.com
