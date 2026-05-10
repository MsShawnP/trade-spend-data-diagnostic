"""Build the trade spend diagnostic workbook.

Ensures the cinderhaven database is current, then generates the
7-tab Excel workbook.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.build_db import build, find_database
from workbook.generator import generate_workbook

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "trade_spend_diagnostic.xlsx"


def main():
    parser = argparse.ArgumentParser(description="Build the trade spend diagnostic workbook.")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output path for the .xlsx file",
    )
    args = parser.parse_args()

    try:
        db_path = build()
    except FileNotFoundError:
        db_path = find_database()

    output_path = generate_workbook(db_path, args.output)
    print(f"Workbook written: {output_path}")


if __name__ == "__main__":
    main()
