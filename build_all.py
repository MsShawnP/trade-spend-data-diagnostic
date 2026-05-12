"""Single entry point: build_db -> compute CSVs -> workbook -> validate.

Usage:
    python build_all.py              # full pipeline
    python build_all.py --skip-db    # skip DB rebuild (use existing)
    python build_all.py -o out.xlsx  # custom output path
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.build_db import build, find_database
from scripts.compute import main as run_compute
from workbook.generator import generate_workbook

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "trade_spend_diagnostic.xlsx"
DATA_DIR = Path(__file__).resolve().parent / "powerbi" / "data"


def main():
    parser = argparse.ArgumentParser(
        description="Full pipeline: build DB, compute CSVs, generate workbook, validate."
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=DEFAULT_OUTPUT,
        help="Output path for the .xlsx file",
    )
    parser.add_argument(
        "--skip-db", action="store_true",
        help="Skip database rebuild (use existing DB)",
    )
    parser.add_argument(
        "--skip-validate", action="store_true",
        help="Skip workbook validation",
    )
    args = parser.parse_args()

    # ── Step 1: Build or locate the database ──
    print("=" * 60)
    print("Step 1: Database")
    print("=" * 60)
    if args.skip_db:
        db_path = find_database()
        print(f"Using existing DB: {db_path}")
    else:
        try:
            db_path = build()
        except FileNotFoundError:
            db_path = find_database()
            print(f"CSV sources not found; using existing DB: {db_path}")
    print()

    # ── Step 2: Compute CSVs ──
    print("=" * 60)
    print("Step 2: Compute CSVs")
    print("=" * 60)
    if not run_compute():
        print("\nCompute layer validation FAILED!")
        sys.exit(1)
    print()

    # ── Step 3: Generate workbook ──
    print("=" * 60)
    print("Step 3: Generate Workbook")
    print("=" * 60)
    output_path = generate_workbook(DATA_DIR, args.output)
    print(f"Workbook written: {output_path}")
    print()

    # ── Step 4: Validate workbook ──
    if not args.skip_validate:
        print("=" * 60)
        print("Step 4: Validate Workbook")
        print("=" * 60)
        from validate_workbook import main as validate_main
        success = validate_main()
        if not success:
            print("\nWorkbook validation FAILED!")
            sys.exit(1)
    else:
        print("Step 4: Skipped (--skip-validate)")

    print()
    print("=" * 60)
    print("Pipeline complete. All steps passed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
