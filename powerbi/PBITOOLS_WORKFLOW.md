# pbi-tools Automation Workflow

Automates DAX measure creation for the Cinderhaven dashboard using
pbi-tools. Measures and calculated tables are generated as JSON files,
then injected into the .pbix via extract/compile. Visual layout is
still manual in Power BI Desktop.

---

## What Gets Automated

- 49 DAX measures with format strings and display folders
- 4 calculated tables (dim_date, WaterfallSteps, WindowWeeks,
  TargetAllInRate)
- Correct dependency ordering (built into the measure definitions)

## What Stays Manual

- Data import (CSV → Power BI via Get Data)
- Relationship creation (drag-and-drop in Model view)
- Visual layout, slicers, conditional formatting, drill-through
- See `BUILD_GUIDE.md` for the manual steps

---

## Prerequisites

1. **Power BI Desktop** — June 2024 or later
2. **pbi-tools** — install via one of:
   ```
   winget install pbi-tools
   ```
   or download from https://pbi.tools/downloads
3. **Python 3.10+** — for the generate script
4. Power BI Desktop must be **closed** when running pbi-tools
   extract/compile

Verify pbi-tools is installed:
```
pbi-tools info
```

---

## Step-by-Step

### Step 1: Export data files

If not already done:

```
python powerbi/export_data.py
```

Verify 7 CSVs in `powerbi/data/` and all validation checks pass.

### Step 2: Create the seed .pbix

Open Power BI Desktop and build the data model manually:

1. **Import CSVs**: Home → Get Data → Text/CSV for each file in
   `powerbi/data/`. Set column types per `BUILD_GUIDE.md` § 2.
2. **Create relationships**: In Model view, create all 10
   relationships per `BUILD_GUIDE.md` § 3.
3. **Save** as `powerbi/trade_spend_diagnostic.pbix`
4. **Close** Power BI Desktop (pbi-tools requires exclusive access)

Do NOT add measures or calculated tables — the script handles those.

### Step 3: Extract the .pbix

```
pbi-tools extract powerbi/trade_spend_diagnostic.pbix
```

This creates a folder alongside the .pbix:

```
powerbi/
  trade_spend_diagnostic.pbix
  trade_spend_diagnostic/
    .pbixproj.json
    Model/
      database.json
      tables/
        dim_retailer/
        dim_product/
        ...
    Report/
    ...
```

### Step 4: Generate measures

```
python powerbi/generate_pbix_model.py powerbi/trade_spend_diagnostic
```

Pass the extracted folder path as the argument. The script writes:

```
trade_spend_diagnostic/
  Model/
    tables/
      _Measures/
        table.json              ← hidden calculated table hosting measures
        measures/
          TotalRevenue.json
          StructuralTradeRate.json
          WaterfallValue.json
          ... (49 measure files)
      dim_date/
        table.json              ← calendar calculated table
      WaterfallSteps/
        table.json              ← waterfall category labels
      WindowWeeks/
        table.json              ← what-if parameter (1–8)
      TargetAllInRate/
        table.json              ← what-if parameter (0–50%)
```

### Step 5: Compile back to .pbix

```
pbi-tools compile powerbi/trade_spend_diagnostic.pbix
```

This reads the folder and rewrites the .pbix with the injected
measures and calculated tables.

### Step 6: Open and verify

Open `trade_spend_diagnostic.pbix` in Power BI Desktop.

Verify:
- In Model view, the `_Measures` table exists (hidden) with 49
  measures organized into 6 display folders
- Calculated tables exist: dim_date, WaterfallSteps, WindowWeeks,
  TargetAllInRate
- Create a test card visual with `TotalRevenue` — should show
  $25,593,052

### Step 7: Build the visual layout

Follow `BUILD_GUIDE.md` § 4 (Page-by-Page Assembly) for manual
visual creation. All measures are already available in the Fields
pane under `_Measures`.

---

## Updating Measures

To change a measure:

1. Edit the `MEASURES` list in `generate_pbix_model.py`
2. Close Power BI Desktop
3. Re-run steps 3–6 (extract → generate → compile → open)

Or edit the measure directly in Power BI Desktop — the generated
JSON is a starting point, not a constraint.

---

## Troubleshooting

**"pbi-tools" not found**: Ensure it's on your PATH. Try the full
path: `C:\Users\<you>\.dotnet\tools\pbi-tools.exe`

**Compile fails with schema errors**: The generated JSON follows the
Tabular Model Scripting Language (TMSL) spec. If pbi-tools uses a
different serialization mode (TMDL vs. Legacy), run:
```
pbi-tools extract trade_spend_diagnostic.pbix -modelSerialization Legacy
```
Then re-run the generate script.

**Measures don't appear after compile**: Check that the _Measures
table.json was written to the correct path inside the extracted
folder. The `Model/tables/_Measures/` directory must exist.

**Power BI shows errors on calculated tables**: The dim_date table
requires fact_deductions and fact_scan_data to be loaded first. If
you see evaluation errors, refresh all data (Home → Refresh).
