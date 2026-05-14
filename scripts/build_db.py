"""Build or locate the Cinderhaven SQLite database.

Tries the submodule's build_db.py first. If the submodule is incomplete
(missing deduction pipeline scripts), falls back to the pre-built database
in the active cinderhaven-data repo.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBMODULE = ROOT / "cinderhaven-data"
SUBMODULE_DB = SUBMODULE / "data" / "cinderhaven_product_master.db"

# Optional fallback when the submodule lacks the deduction pipeline scripts.
# Set CINDERHAVEN_DB to point at a pre-built database on disk.
_ACTIVE_DB_ENV = os.environ.get("CINDERHAVEN_DB")
ACTIVE_DB = Path(_ACTIVE_DB_ENV) if _ACTIVE_DB_ENV else None


def find_database() -> Path:
    if SUBMODULE_DB.exists():
        return SUBMODULE_DB
    if ACTIVE_DB and ACTIVE_DB.exists():
        return ACTIVE_DB
    raise FileNotFoundError(
        "No cinderhaven database found. Initialize the submodule, or set "
        "CINDERHAVEN_DB to a pre-built .db file."
    )


def build(force: bool = False) -> Path:
    build_script = SUBMODULE / "scripts" / "build_db.py"
    deduction_script = SUBMODULE / "scripts" / "07_seed_deduction_tables.py"

    if SUBMODULE_DB.exists() and not force:
        size_mb = SUBMODULE_DB.stat().st_size / (1024 * 1024)
        print(f"Database already exists ({size_mb:.1f} MB): {SUBMODULE_DB}")
        return SUBMODULE_DB

    if build_script.exists() and deduction_script.exists():
        print("Building database from submodule...")
        result = subprocess.run(
            [sys.executable, str(build_script), "--force"],
            cwd=SUBMODULE,
            check=False,
        )
        if result.returncode == 0 and SUBMODULE_DB.exists():
            return SUBMODULE_DB
        print(f"Submodule build failed (exit {result.returncode}).")

    if ACTIVE_DB and ACTIVE_DB.exists():
        print(f"Using pre-built database from CINDERHAVEN_DB...")
        SUBMODULE_DB.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ACTIVE_DB, SUBMODULE_DB)
        size_mb = SUBMODULE_DB.stat().st_size / (1024 * 1024)
        print(f"Copied ({size_mb:.1f} MB): {SUBMODULE_DB}")
        return SUBMODULE_DB

    raise FileNotFoundError(
        "Cannot build database: submodule incomplete and no pre-built DB found. "
        "Set CINDERHAVEN_DB to a pre-built .db file."
    )


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    db_path = build(force=args.force)
    print(f"\nDatabase ready: {db_path}")
