"""Export data files for Power BI consumption.

DEPRECATED — this module now delegates to scripts/compute.py which is
the single computation layer for both the workbook and Power BI dashboard.
Kept as a thin wrapper for backward compatibility.

Usage (unchanged):
    python powerbi/export_data.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.compute import main as compute_main  # noqa: E402


def main():
    """Run the unified computation layer."""
    print("NOTE: powerbi/export_data.py now delegates to scripts/compute.py")
    print("      All CSV exports are produced by the unified compute layer.")
    print()
    return compute_main()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
