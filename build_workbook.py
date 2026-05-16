"""Build the trade spend diagnostic workbook.

Connects to the Cinderhaven Data Platform (Postgres) and generates
the 7-tab Excel workbook.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

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

    if not os.environ.get("DATABASE_URL"):
        print("Error: DATABASE_URL environment variable not set.", file=sys.stderr)
        print("See .env.example for connection string templates.", file=sys.stderr)
        sys.exit(1)

    output_path = generate_workbook(args.output)
    print(f"Workbook written: {output_path}")


if __name__ == "__main__":
    main()
