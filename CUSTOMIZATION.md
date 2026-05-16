# Customizing for a New Client

This diagnostic is built around Cinderhaven Provisions' data. To
produce the same analysis for a different CPG company, swap the data
and update the configuration constants described below.

## Database schema

The workbook reads from 8 tables in the `public_staging` schema.
Load your client's data into these tables, preserving column names
and types.

### Required tables

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `stg_scan_data` | Weekly POS data by store | `store_id`, `sku`, `week_ending`, `units_sold`, `dollars_sold` |
| `stg_stores` | Store/retailer dimension | `store_id`, `retailer` |
| `stg_deductions` | Deduction line items | `deduction_id`, `deduction_date`, `retailer_id`, `code_as_remitted`, `code_id`, `deduction_type`, `amount`, `order_id`, `shipment_id`, `remittance_id`, `remittance_description`, `dispute_deadline`, `is_vague`, `is_post_audit`, `is_double_dip` |
| `stg_deduction_codes` | Retailer code dictionary | `code_id`, `retailer_id`, `code`, `name`, `deduction_type`, `is_published` |
| `stg_disputes` | Dispute outcomes | `deduction_id`, `outcome`, `recovered_amount`, `filed_date`, `closed_date` |
| `stg_promotions` | Promo calendar | `promo_id`, `sku`, `retailer`, `start_week`, `end_week`, `duration_weeks`, `discount_depth_pct`, `promo_type`, `promo_cost`, `funding_mechanism` |
| `stg_retailers` | Retailer lookup | `name` (display name, e.g. "Walmart") |
| `stg_sku_costs` | COGS and contracted trade rates | `cogs_per_unit`, plus one `trade_spend_pct_*` column per channel |

### Data requirements

- `stg_scan_data` must have at least 52 weeks of `week_ending` values
- `stg_deductions.deduction_type` must use the keys defined in the taxonomy (see below)
- `stg_deductions.retailer_id` must be lowercase with underscores (e.g. `whole_foods`)
- `stg_stores.retailer` uses display format (e.g. `Whole Foods`)
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
    # ... must match columns in stg_sku_costs
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

The summary sentence on Tab 1 says "You budgeted 17%." This is
hardcoded in the text template in `build_executive_pulse()`. Replace
`17` with the client's planned structural rate.

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
pip install -r requirements.txt
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
python build_workbook.py -o output/ClientName_Trade_Diagnostic.xlsx
python validate_workbook.py  # 62 checks
```

## Branding

- Company name appears in `build_executive_pulse()` (cell B1 text)
- Output filename in `build_workbook.py` DEFAULT_OUTPUT
- GitHub Release asset name (if distributing via repo)

## What stays the same

The analytical framework, tab structure, taxonomy logic, and
Excel formatting are client-agnostic. You only swap data and
the 6 configuration constants above.
