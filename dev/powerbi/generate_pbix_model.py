"""Generate pbi-tools model artifacts for the Cinderhaven dashboard.

Creates measure JSON files and calculated table definitions in the
pbi-tools folder structure. These can be merged into an extracted
.pbix to inject all DAX measures automatically.

Usage:
    python powerbi/generate_pbix_model.py [output_dir]

    output_dir defaults to powerbi/pbi-model/
"""

import json
import sys
from pathlib import Path

DEFAULT_OUT = Path(__file__).resolve().parent / "pbi-model"

# ── Measures ────────────────────────────────────────────────────────

MEASURES = [
    # ── What-If Parameters ──────────────────────────────────────
    {
        "name": "WindowWeeks Value",
        "expression": "SELECTEDVALUE(WindowWeeks[WindowWeeks Value], 4)",
        "formatString": "#,##0",
        "displayFolder": "What-If Parameters",
    },
    {
        "name": "TargetAllInRate Value",
        "expression": "SELECTEDVALUE(TargetAllInRate[TargetAllInRate Value], 0.18)",
        "formatString": "0.0%",
        "displayFolder": "What-If Parameters",
    },

    # ── Global / Shared ────────────────────────────────────────
    {
        "name": "TotalRevenue",
        "expression": "SUM(fact_scan_data[dollars_sold])",
        "formatString": "$#,##0",
        "displayFolder": "Global",
    },
    {
        "name": "StructuralTradeAmount",
        "expression": "SUM(fact_structural_trade[structural_trade_dollars])",
        "formatString": "$#,##0",
        "displayFolder": "Global",
    },
    {
        "name": "StructuralTradeRate",
        "expression": "DIVIDE([StructuralTradeAmount], [TotalRevenue], 0)",
        "formatString": "0.0%",
        "displayFolder": "Global",
    },
    {
        "name": "OperationalWasteAmount",
        "expression": (
            "CALCULATE(\n"
            "    SUM(fact_deductions[amount]),\n"
            '    fact_deductions[deduction_type] <> "promo_billback",\n'
            "    fact_deductions[in_trailing_window] = 1\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Global",
    },
    {
        "name": "OperationalWasteRate",
        "expression": "DIVIDE([OperationalWasteAmount], [TotalRevenue], 0)",
        "formatString": "0.0%",
        "displayFolder": "Global",
    },
    {
        "name": "PromoBillbackAmount",
        "expression": (
            "CALCULATE(\n"
            "    SUM(fact_deductions[amount]),\n"
            '    fact_deductions[deduction_type] = "promo_billback",\n'
            "    fact_deductions[in_trailing_window] = 1\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Global",
    },
    {
        "name": "AllInTradeCost",
        "expression": "[StructuralTradeAmount] + [OperationalWasteAmount]",
        "formatString": "$#,##0",
        "displayFolder": "Global",
    },
    {
        "name": "AllInTradeRate",
        "expression": "DIVIDE([AllInTradeCost], [TotalRevenue], 0)",
        "formatString": "0.0%",
        "displayFolder": "Global",
    },
    {
        "name": "DeductionCount",
        "expression": (
            "CALCULATE(\n"
            "    COUNTROWS(fact_deductions),\n"
            "    fact_deductions[in_trailing_window] = 1\n"
            ")"
        ),
        "formatString": "#,##0",
        "displayFolder": "Global",
    },
    {
        "name": "TotalRecovered",
        "expression": "SUM(fact_disputes[recovered_amount])",
        "formatString": "$#,##0",
        "displayFolder": "Global",
    },
    {
        "name": "DisputeCount",
        "expression": "COUNTROWS(fact_disputes)",
        "formatString": "#,##0",
        "displayFolder": "Global",
    },
    {
        "name": "RecoveryRate",
        "expression": (
            "DIVIDE(\n"
            "    [TotalRecovered],\n"
            "    SUM(fact_disputes[deduction_amount]),\n"
            "    0\n"
            ")"
        ),
        "formatString": "0.0%",
        "displayFolder": "Global",
    },

    # ── Page 1: Executive Overview ─────────────────────────────
    {
        "name": "RetailerRevenue",
        "expression": "SUM(fact_scan_data[dollars_sold])",
        "formatString": "$#,##0",
        "displayFolder": "Executive Overview",
    },
    {
        "name": "WasteAmount",
        "expression": (
            "CALCULATE(\n"
            "    SUM(fact_deductions[amount]),\n"
            '    fact_deductions[deduction_type] <> "promo_billback",\n'
            "    fact_deductions[in_trailing_window] = 1\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Executive Overview",
    },
    {
        "name": "WaterfallValue",
        "expression": (
            "SWITCH(\n"
            "    SELECTEDVALUE(WaterfallSteps[Step]),\n"
            '    "01 Revenue", [TotalRevenue],\n'
            '    "02 Structural Trade", -[StructuralTradeAmount],\n'
            '    "03 Operational Waste", -[OperationalWasteAmount]\n'
            ")"
        ),
        "formatString": "",
        "displayFolder": "Executive Overview",
    },

    # ── Page 2: Deduction Deep-Dive ────────────────────────────
    {
        "name": "DeductionAmount",
        "expression": (
            "CALCULATE(\n"
            "    SUM(fact_deductions[amount]),\n"
            "    fact_deductions[in_trailing_window] = 1\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Deduction Deep-Dive",
    },
    {
        "name": "DoubleDipCount",
        "expression": (
            "CALCULATE(\n"
            "    COUNTROWS(fact_deductions),\n"
            "    fact_deductions[is_double_dip] = 1\n"
            ")"
        ),
        "formatString": "#,##0",
        "displayFolder": "Deduction Deep-Dive",
    },
    {
        "name": "DoubleDipTotal",
        "expression": (
            "CALCULATE(\n"
            "    SUM(fact_deductions[amount]),\n"
            "    fact_deductions[is_double_dip] = 1\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Deduction Deep-Dive",
    },
    {
        "name": "UnmappedCodeCount",
        "expression": (
            "CALCULATE(\n"
            "    COUNTROWS(fact_deductions),\n"
            '    fact_deductions[translated_code] = "Unmapped",\n'
            "    fact_deductions[in_trailing_window] = 1\n"
            ")"
        ),
        "formatString": "#,##0",
        "displayFolder": "Deduction Deep-Dive",
    },
    {
        "name": "AvgDaysToResolve",
        "expression": (
            "CALCULATE(\n"
            "    AVERAGE(fact_deductions[days_outstanding]),\n"
            "    fact_deductions[in_trailing_window] = 1\n"
            ")"
        ),
        "formatString": "0",
        "displayFolder": "Deduction Deep-Dive",
    },

    # ── Page 3: Promo Performance ──────────────────────────────
    {
        "name": "PromoCost",
        "expression": (
            "SUMX(\n"
            "    dim_promo,\n"
            "    IF(\n"
            "        NOT(ISBLANK(dim_promo[actual_cost])),\n"
            "        dim_promo[actual_cost],\n"
            "        dim_promo[planned_cost]\n"
            "    )\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "IncrementalRevenue",
        "expression": "SUM(dim_promo[incremental_revenue])",
        "formatString": "$#,##0",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "BaselineVolume",
        "expression": "AVERAGE(dim_promo[baseline_avg_volume])",
        "formatString": "0.00",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "BaselineVolumeDynamic",
        "expression": (
            "VAR SelectedWindow = [WindowWeeks Value]\n"
            "VAR CurrentPromoStart = SELECTEDVALUE(dim_promo[start_week])\n"
            "VAR CurrentSKU = SELECTEDVALUE(dim_promo[sku])\n"
            "VAR CurrentRetailer = SELECTEDVALUE(dim_promo[retailer])\n"
            "RETURN\n"
            "AVERAGEX(\n"
            "    FILTER(\n"
            "        fact_scan_data,\n"
            "        fact_scan_data[sku] = CurrentSKU\n"
            "            && fact_scan_data[retailer] = CurrentRetailer\n"
            '            && fact_scan_data[promo_period] = "pre"\n'
            "            && fact_scan_data[week_ending] >= DATE(\n"
            "                YEAR(DATEVALUE(CurrentPromoStart)),\n"
            "                MONTH(DATEVALUE(CurrentPromoStart)),\n"
            "                DAY(DATEVALUE(CurrentPromoStart))\n"
            "            ) - (SelectedWindow * 7)\n"
            "            && fact_scan_data[week_ending] < DATEVALUE(CurrentPromoStart)\n"
            "    ),\n"
            "    fact_scan_data[units_sold]\n"
            ")"
        ),
        "formatString": "0.00",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "IncrementalRevenueDynamic",
        "expression": (
            "VAR Baseline = [BaselineVolumeDynamic]\n"
            "VAR DuringAvg = AVERAGE(dim_promo[during_avg_volume])\n"
            "VAR Duration = SELECTEDVALUE(dim_promo[duration_weeks], 1)\n"
            "VAR ASP = SELECTEDVALUE(dim_promo[asp])\n"
            "RETURN\n"
            "IF(\n"
            "    NOT(ISBLANK(Baseline)) && NOT(ISBLANK(DuringAvg)) && NOT(ISBLANK(ASP)),\n"
            "    (DuringAvg - Baseline) * Duration * ASP,\n"
            "    BLANK()\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "PromoROI",
        "expression": "AVERAGE(dim_promo[roi])",
        "formatString": "0.00",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "PromoROIDynamic",
        "expression": "DIVIDE([IncrementalRevenueDynamic], [PromoCost], BLANK())",
        "formatString": "0.00",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "AvgROI",
        "expression": (
            "AVERAGEX(\n"
            "    FILTER(dim_promo, NOT(ISBLANK(dim_promo[roi]))),\n"
            "    dim_promo[roi]\n"
            ")"
        ),
        "formatString": "0.00",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "PromoCount",
        "expression": "COUNTROWS(dim_promo)",
        "formatString": "#,##0",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "GhostPromoCount",
        "expression": (
            "CALCULATE(\n"
            "    COUNTROWS(fact_deductions),\n"
            "    fact_deductions[is_ghost_promo] = 1\n"
            ")"
        ),
        "formatString": "#,##0",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "GhostPromoTotal",
        "expression": (
            "CALCULATE(\n"
            "    SUM(fact_deductions[amount]),\n"
            "    fact_deductions[is_ghost_promo] = 1\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "FullDataCount",
        "expression": (
            "CALCULATE(\n"
            "    COUNTROWS(dim_promo),\n"
            '    dim_promo[data_quality] = "Full"\n'
            ")"
        ),
        "formatString": "#,##0",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "PartialDataCount",
        "expression": (
            "CALCULATE(\n"
            "    COUNTROWS(dim_promo),\n"
            '    dim_promo[data_quality] = "Partial"\n'
            ")"
        ),
        "formatString": "#,##0",
        "displayFolder": "Promo Performance",
    },
    {
        "name": "NoPOSCount",
        "expression": (
            "CALCULATE(\n"
            "    COUNTROWS(dim_promo),\n"
            '    dim_promo[data_quality] = "No POS"\n'
            ")"
        ),
        "formatString": "#,##0",
        "displayFolder": "Promo Performance",
    },

    # ── Page 4: Retailer Comparison ────────────────────────────
    {
        "name": "GrossMarginPct",
        "expression": (
            "IF(\n"
            "    HASONEVALUE(dim_retailer[retailer_name]),\n"
            "    SELECTEDVALUE(dim_retailer[gross_margin], 0),\n"
            "    DIVIDE(\n"
            "        SUMX(dim_retailer, dim_retailer[gross_margin] * dim_retailer[revenue]),\n"
            "        SUM(dim_retailer[revenue]),\n"
            "        0\n"
            "    )\n"
            ")"
        ),
        "formatString": "0.0%",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "StructuralRate",
        "expression": (
            "IF(\n"
            "    HASONEVALUE(dim_retailer[retailer_name]),\n"
            "    SELECTEDVALUE(dim_retailer[trade_rate], 0),\n"
            "    DIVIDE(\n"
            "        SUM(fact_structural_trade[structural_trade_dollars]),\n"
            "        [TotalRevenue],\n"
            "        0\n"
            "    )\n"
            ")"
        ),
        "formatString": "0.0%",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "OpDedRate",
        "expression": (
            "VAR OpDed =\n"
            "    CALCULATE(\n"
            "        SUM(fact_deductions[amount]),\n"
            '        fact_deductions[deduction_type] <> "promo_billback",\n'
            "        fact_deductions[in_trailing_window] = 1\n"
            "    )\n"
            "RETURN\n"
            "IF(\n"
            "    HASONEVALUE(dim_retailer[retailer_name]),\n"
            "    DIVIDE(OpDed, SELECTEDVALUE(dim_retailer[revenue], 1), 0),\n"
            "    DIVIDE(OpDed, [TotalRevenue], 0)\n"
            ")"
        ),
        "formatString": "0.0%",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "PromoBBRate",
        "expression": (
            "VAR PromoBB =\n"
            "    CALCULATE(\n"
            "        SUM(fact_deductions[amount]),\n"
            '        fact_deductions[deduction_type] = "promo_billback",\n'
            "        fact_deductions[in_trailing_window] = 1\n"
            "    )\n"
            "RETURN\n"
            "IF(\n"
            "    HASONEVALUE(dim_retailer[retailer_name]),\n"
            "    DIVIDE(PromoBB, SELECTEDVALUE(dim_retailer[revenue], 1), 0),\n"
            "    DIVIDE(PromoBB, [TotalRevenue], 0)\n"
            ")"
        ),
        "formatString": "0.0%",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "NetNetMargin",
        "expression": "[GrossMarginPct] - [StructuralRate] - [OpDedRate] - [PromoBBRate]",
        "formatString": "0.0%",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "NetNetMarginPct",
        "expression": "[NetNetMargin]",
        "formatString": "0.0%",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "RevenueShare",
        "expression": (
            "DIVIDE(\n"
            "    SUM(fact_scan_data[dollars_sold]),\n"
            "    CALCULATE(SUM(fact_scan_data[dollars_sold]), ALL(dim_retailer)),\n"
            "    0\n"
            ")"
        ),
        "formatString": "0.0%",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "DeductionShare",
        "expression": (
            "DIVIDE(\n"
            "    CALCULATE(SUM(fact_deductions[amount]), fact_deductions[in_trailing_window] = 1),\n"
            "    CALCULATE(SUM(fact_deductions[amount]), ALL(dim_retailer), fact_deductions[in_trailing_window] = 1),\n"
            "    0\n"
            ")"
        ),
        "formatString": "0.0%",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "SavingsAtTarget",
        "expression": (
            "VAR CurrentAllIn = [StructuralRate] + [OpDedRate] + [PromoBBRate]\n"
            "VAR Target = [TargetAllInRate Value]\n"
            "VAR Rev = SELECTEDVALUE(dim_retailer[revenue], 0)\n"
            "RETURN\n"
            "IF(\n"
            "    HASONEVALUE(dim_retailer[retailer_name]),\n"
            "    IF(CurrentAllIn > Target, (CurrentAllIn - Target) * Rev, 0),\n"
            "    [TotalSavingsAtTarget]\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "TotalSavingsAtTarget",
        "expression": (
            "SUMX(\n"
            "    dim_retailer,\n"
            "    VAR CurrentAllIn =\n"
            "        CALCULATE([StructuralRate]) +\n"
            "        CALCULATE([OpDedRate]) +\n"
            "        CALCULATE([PromoBBRate])\n"
            "    VAR Target = [TargetAllInRate Value]\n"
            "    VAR Rev = dim_retailer[revenue]\n"
            "    RETURN\n"
            "    IF(CurrentAllIn > Target, (CurrentAllIn - Target) * Rev, 0)\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "HighestRiskRetailer",
        "expression": (
            "VAR MinMargin =\n"
            "    MINX(\n"
            "        FILTER(dim_retailer, dim_retailer[revenue] > 0),\n"
            "        dim_retailer[net_net_margin]\n"
            "    )\n"
            "RETURN\n"
            "CALCULATE(\n"
            "    SELECTEDVALUE(dim_retailer[retailer_name]),\n"
            "    FILTER(dim_retailer, dim_retailer[net_net_margin] = MinMargin)\n"
            ")"
        ),
        "formatString": "",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "Revenue",
        "expression": (
            "IF(\n"
            "    HASONEVALUE(dim_retailer[retailer_name]),\n"
            "    SELECTEDVALUE(dim_retailer[revenue], 0),\n"
            "    SUM(dim_retailer[revenue])\n"
            ")"
        ),
        "formatString": "$#,##0",
        "displayFolder": "Retailer Comparison",
    },
    {
        "name": "RetailerWaterfallValue",
        "expression": (
            "SWITCH(\n"
            "    SELECTEDVALUE(WaterfallSteps[Step]),\n"
            '    "01 Revenue", [GrossMarginPct],\n'
            '    "02 Structural Trade", -[StructuralRate],\n'
            '    "03 Operational Waste", -[OpDedRate] - [PromoBBRate]\n'
            ")"
        ),
        "formatString": "",
        "displayFolder": "Retailer Comparison",
    },
]


# ── Calculated Tables ──────────────────────────────────────────────

CALCULATED_TABLES = [
    {
        "name": "dim_date",
        "expression": (
            "VAR MinDate = MIN(fact_deductions[deduction_date])\n"
            "VAR MaxDate = MAX(fact_scan_data[week_ending])\n"
            "RETURN\n"
            "ADDCOLUMNS(\n"
            "    CALENDAR(MinDate, MaxDate),\n"
            '    "year", YEAR([Date]),\n'
            '    "month", MONTH([Date]),\n'
            '    "year_month", FORMAT([Date], "YYYY-MM"),\n'
            '    "week_ending",\n'
            "        [Date] + (6 - WEEKDAY([Date], 2)),\n"
            '    "month_name", FORMAT([Date], "MMM YYYY")\n'
            ")"
        ),
    },
    {
        "name": "WaterfallSteps",
        "expression": (
            "DATATABLE(\n"
            '    "Step", STRING,\n'
            '    "SortOrder", INTEGER,\n'
            "    {\n"
            '        {"01 Revenue", 1},\n'
            '        {"02 Structural Trade", 2},\n'
            '        {"03 Operational Waste", 3}\n'
            "    }\n"
            ")"
        ),
    },
    {
        "name": "WindowWeeks",
        "expression": "GENERATESERIES(1, 8, 1)",
    },
    {
        "name": "TargetAllInRate",
        "expression": "GENERATESERIES(0, 0.50, 0.01)",
    },
]


def _safe_filename(name: str) -> str:
    """Convert measure name to a filesystem-safe filename."""
    return name.replace(" ", "_").replace("/", "_")


def generate(out_dir: Path):
    """Write pbi-tools model artifacts to out_dir."""
    measures_dir = out_dir / "Model" / "tables" / "_Measures" / "measures"
    tables_dir = out_dir / "Model" / "tables"
    measures_dir.mkdir(parents=True, exist_ok=True)

    # Write measure JSON files
    for m in MEASURES:
        obj = {"name": m["name"], "expression": m["expression"]}
        if m.get("formatString"):
            obj["formatString"] = m["formatString"]
        if m.get("displayFolder"):
            obj["displayFolder"] = m["displayFolder"]

        filename = _safe_filename(m["name"]) + ".json"
        path = measures_dir / filename
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write _Measures table definition (empty calculated table to host measures)
    measures_table = {
        "name": "_Measures",
        "isHidden": True,
        "partitions": [
            {
                "name": "_Measures",
                "mode": "import",
                "source": {
                    "type": "calculated",
                    "expression": 'ROW("x", 0)',
                },
            }
        ],
    }
    table_dir = tables_dir / "_Measures"
    table_dir.mkdir(parents=True, exist_ok=True)
    (table_dir / "table.json").write_text(
        json.dumps(measures_table, indent=2), encoding="utf-8"
    )

    # Write calculated table definitions
    for t in CALCULATED_TABLES:
        tdir = tables_dir / t["name"]
        tdir.mkdir(parents=True, exist_ok=True)
        obj = {
            "name": t["name"],
            "partitions": [
                {
                    "name": t["name"],
                    "mode": "import",
                    "source": {
                        "type": "calculated",
                        "expression": t["expression"],
                    },
                }
            ],
        }
        (tdir / "table.json").write_text(
            json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # Summary
    by_folder = {}
    for m in MEASURES:
        folder = m.get("displayFolder", "(none)")
        by_folder.setdefault(folder, []).append(m["name"])

    print(f"Output: {out_dir}")
    print(f"\nMeasures: {len(MEASURES)} total")
    for folder, names in sorted(by_folder.items()):
        print(f"  {folder}: {len(names)}")
        for n in names:
            print(f"    - {n}")

    print(f"\nCalculated tables: {len(CALCULATED_TABLES)}")
    for t in CALCULATED_TABLES:
        print(f"  - {t['name']}")

    print(f"\nFiles written to {measures_dir}")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    generate(out)
