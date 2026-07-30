# reference/

Vendored canonical reference data. **Do not edit these files here.**

- `canonical_values.yml` — machine-readable single source of truth (SSOT) for
  Cinderhaven figures, keyed `metric.basis.period`. Vendored verbatim from
  [`cinderhaven-data-platform`](https://github.com/MsShawnP/cinderhaven-data-platform)
  at `reference/canonical_values.yml`
  (VERIFIED-AGAINST-PRODUCTION 2026-07-29, read-only workflow run 30488858977,
  Fly Postgres `cinderhaven-db`).

`tests/test_canonical_regression.py` reads this file so the data contract is
pinned to the SSOT rather than to hardcoded literals. To refresh, re-copy the
file from the platform repo after that repo re-verifies against production.
Reconcile **down** to canonical — never edit canonical to match this repo.
