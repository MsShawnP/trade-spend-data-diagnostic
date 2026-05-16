# Decisions

### 2026-05-16 — Database connection via environment only
- **Why:** `connect()` reads `DATABASE_URL` from env. Passing the URL through every function signature was vestigial from SQLite era and added no value — the param was never used by `connect()`.
- **Scope:** All `workbook/tab_*.py` modules and `workbook/generator.py`
- **Do not:** Re-introduce `database_url` as a function parameter. If connection config needs to vary (e.g., test vs prod), vary the environment variable.

### 2026-05-16 — Merged descriptive cells always get ALIGN_LEFT + row height
- **Why:** openpyxl merged cells default to no wrapping. Without `wrap_text=True` (included in `ALIGN_LEFT`), text clips silently. Even with wrapping, default row height (~15pt) truncates multi-line content.
- **Scope:** All `workbook/tab_*.py` modules — any merged cell with descriptive text
- **Do not:** Set only font on merged text cells. Always pair with `ALIGN_LEFT`. For cells likely to exceed one line, set `ws.row_dimensions[row].height = 42`.
