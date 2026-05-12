"""Build the trade spend diagnostic workbook.

Pipeline: build_db → compute CSVs → generate workbook.
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
    parser = argparse.ArgumentParser(description="Build the trade spend diagnostic workbook.")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output path for the .xlsx file",
    )
    args = parser.parse_args()

    # 1. Build or locate the database
    try:
        build()
    except FileNotFoundError:
        find_database()  # Just verify it exists

    # 2. Run computation layer (SQLite → CSVs)
    print("Running computation layer...")
    if not run_compute():
        print("Compute layer validation failed!")
        sys.exit(1)
    print()

    # 3. Generate workbook from computed CSVs
    output_path = generate_workbook(DATA_DIR, args.output)
    print(f"Workbook written: {output_path}")


if __name__ == "__main__":
    main()
