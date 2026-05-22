# Customizing for a New Client

This diagnostic is built around Cinderhaven Provisions' data. To
produce the same analysis for a different CPG company, swap the data
and update the configuration constants described below.

## Database schema

The workbook reads from a SQLite database at
`cinderhaven-data/data/cinderhaven_product_master.db`, shipped as a
git submodule. Load your client's data into these tables, preserving
column names and types.

### Required tables

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `scan_data` | Weekly POS data by store | `sku`, `store_id`, `week_ending`, `units_sold`, `dollars_sold` |
| `stores` | Store/retailer dimension | `store_id`, `retailer`, `chain_name`, `region`, `state`, `volume_tier` |
| `deductions` | Deduction line items | `deduction_id`, `retailer_id`, `deduction_date`, `deduction_type`, `code_id`, `code_as_remitted`, `amount`, `is_vague`, `is_post_audit`, `is_double_dip` |
| `deduction_codes` | Retailer code dictionary | `code_id`, `retailer_id`, `code`, `name`, `deduction_type`, `is_published` |
| `disputes` | Dispute outcomes | `dispute_id`, `deduction_id`, `filed_date`, `outcome`, `recovered_amount`, `closed_date` |
| `promotions` | Promo calendar | `promo_id`, `sku`, `retailer`, `start_week`, `end_week`, `duration_weeks`, `discount_depth_pct`, `promo_type`, `promo_cost`, `funding_mechanism` |
| `retailers` | Retailer lookup | `retailer_id`, `name`, `channel_type` |
| `sku_costs` | COGS and contracted trade rates | `sku`, `cogs_per_unit`, `wholesale_price`, plus per-channel `wholesale_*` and `trade_spend_pct_*` columns |

### Data requirements

- `scan_data` must have at least 52 weeks of `week_ending` values
- `deductions.deduction_type` must use the keys defined in the taxonomy (see below)
- `deductions.retailer_id` must be lowercase with underscores (e.g. `whole_foods`)
- `stores.retailer` uses display format (e.g. `Whole Foods`)
- All monetary values in USD, not cents

## Configuration constants to update

### 1. Channel mapping (`workbook/channel_mapping.py`)

Maps retailers to channels for Tab 1 and Tab 4 aggregation.

```python
RETAILER_TO_CHANNEL = {
    "Walmart": "Walmart",
    "Costco": "Costco",
    # ... your client's retailers
}

CHANNEL_RATE_COLS = {
    "Walmart": "trade_spend_pct_walmart",
    # ... must match columns in sku_costs
}
```

### 2. Industry benchmark (`workbook/tab_executive_pulse.py`)

```python
BENCHMARK_BAND = (0.19, 0.23)  # 19-23% for natural/specialty CPG
```

Adjust for the client's category. Common ranges:
- Mass grocery: 15-20%
- Natural/specialty: 19-23%
- Club/warehouse: 12-16%

### 3. Budgeted rate

The summary sentence on Tab 1 is computed dynamically from the
structural trade rate in the database. No hardcoded value to change.

### 4. Deduction taxonomy (`workbook/deduction_taxonomy.py`)

Maps `deduction_type` values to buckets (Contractual, Probable Waste,
Unknown) and defense text. If the client has additional deduction
types beyond the defaults, add entries here.

### 5. Recoverability (`workbook/tab_leak_diagnostic.py`)

```python
RECOVERABILITY = {
    "short_ship": "Medium",
    "vague": "Low",
    # ...
}
```

Adjust based on the client's dispute history and retailer
relationships.

### 6. Department ownership (`workbook/tab_executive_pulse.py`)

```python
CATEGORY_TO_DEPT = {
    "short_ship": ("Operations", "Fulfillment accuracy"),
    "vague": ("Finance", "Unclear codes — investigate"),
    # ...
}
```

Maps each deduction type to the responsible department. Adjust to
match the client's org structure.

## Build steps

```bash
git clone --recurse-submodules <repo-url>
cd trade-spend-data-diagnostic
pip install -r requirements.txt
python build_workbook.py
python validate_workbook.py  # 60 checks
```

The `--recurse-submodules` flag pulls the SQLite database via git
submodule. If you cloned without it:

```bash
git submodule update --init
```

## Branding

- Company name appears in `build_executive_pulse()` (cell B1 text)
- Output filename in `build_workbook.py` DEFAULT_OUTPUT
- GitHub Release asset name (if distributing via repo)

## What stays the same

The analytical framework, tab structure, taxonomy logic, and
Excel formatting are client-agnostic. You only swap data and
the 6 configuration constants above.
