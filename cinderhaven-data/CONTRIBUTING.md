# Contributing to cinderhaven-data

This repo is the single source of truth for the Cinderhaven Provisions dataset. Several downstream projects consume this data via git submodule.

## Requesting a data change

If a downstream project needs a new table, a new column, modified generation logic, or a bug fix in the data:

1. **Open an issue or pull request here**, not on the consuming project. The data pipeline lives in this repo — changes made elsewhere will drift out of sync.
2. After the change is merged, run `build_db.py` and `06_validate_dataset.py` (or `15_validate_deductions.py` for deduction tables) to confirm the data still validates.
3. Each consuming repo updates on its own schedule by advancing its submodule pin and rebuilding.

## Making changes

1. Fork or branch from `main`.
2. Edit or add scripts in `scripts/`.
3. Run the full build and validation:
   ```bash
   python scripts/build_db.py --force
   ```
4. Open a PR with a description of what changed and why.

## What not to do

- Don't commit the `.db` file — it's ~170 MB and regenerable.
- Don't modify data generation scripts inside a consuming project's repo. Those copies are being removed in favor of this submodule.
