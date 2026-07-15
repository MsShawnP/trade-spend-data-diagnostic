# cinderhaven-data

**Tier:** Quick
**Stack:** Python 3.10+ (stdlib only), SQLite
**Role:** Seed dataset generator for [cinderhaven-data-platform](https://github.com/MsShawnP/cinderhaven-data-platform)

## What this is

A deterministic pipeline that generates a ~164 MB SQLite database for a fictional ~$25M specialty food brand. 17 scripts run in order via `build_db.py`, producing 23+ tables spanning product master, retail distribution, scan data, and a full deduction/dispute lifecycle.

## Key conventions

- **No third-party dependencies.** Everything uses Python stdlib (sqlite3, random, datetime, pathlib).
- **Seeded RNG.** Every script uses `rng = random.Random(SEED)` for reproducible output. Never use `random.seed()` at module level.
- **Shared module.** `scripts/shared.py` owns `DB_PATH`, `REGIONAL_CHAIN_NAMES`, `gtin_invalid()`, `upc_missing()`. Import from there, don't redefine.
- **Context managers.** Use `with sqlite3.connect(DB_PATH) as con:` for all database connections.
- **Line length.** 120 chars (configured in `pyproject.toml`). `ruff check scripts/` must pass clean.
- **Pipeline order matters.** Each script reads tables built by earlier ones. See `PIPELINE` list in `build_db.py`.

## Running

```bash
python scripts/build_db.py          # build if missing
python scripts/build_db.py --force  # rebuild from scratch
```

## Validation

Two validation scripts run as part of the pipeline:
- `06_validate_dataset.py` — base table checks (24 assertions)
- `15_validate_deductions.py` — deduction table checks (35+ assertions)

Both exit non-zero on structural failures. Warnings (row counts near range edges) are expected and not failures.
