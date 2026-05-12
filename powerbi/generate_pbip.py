"""Generate a complete Power BI .pbip project for the Cinderhaven dashboard.

Creates the folder structure, semantic model (7 CSV tables, 4 calculated
tables, 49 DAX measures, 9 relationships), and a minimal report skeleton.

Usage:
    cd C:\\Users\\mssha\\projects\\active\\trade-spend-data-diagnostic
    python powerbi/generate_pbip.py

Then double-click CinderhavenDashboard.pbip to open in Power BI Desktop.
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_pbix_model import MEASURES

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR = Path(__file__).resolve().parent
PROJECT = "CinderhavenDashboard"

# ── M type mapping ───────────────────────────────────────────────

M_TYPE = {
    "string": "type text",
    "double": "type number",
    "int64": "Int64.Type",
    "dateTime": "type date",
}

# ── Data table schemas ───────────────────────────────────────────
# Each column: (name, bim_dataType, summarizeBy)

DATA_TABLES = [
    {
        "name": "dim_retailer",
        "csv": "dim_retailer.csv",
        "columns": [
            ("retailer_id", "string", "none"),
            ("retailer_name", "string", "none"),
            ("channel_type", "string", "none"),
            ("revenue", "double", "sum"),
            ("trade_rate", "double", "none"),
            ("gross_margin", "double", "none"),
            ("structural_trade_dollars", "double", "sum"),
            ("op_deductions", "double", "sum"),
            ("promo_billback", "double", "sum"),
            ("all_in_trade", "double", "sum"),
            ("all_in_rate", "double", "none"),
            ("net_net_margin", "double", "none"),
        ],
    },
    {
        "name": "dim_product",
        "csv": "dim_product.csv",
        "columns": [
            ("sku", "string", "none"),
            ("product_name", "string", "none"),
            ("product_line", "string", "none"),
            ("subcategory", "string", "none"),
            ("cogs_per_unit", "double", "none"),
            ("wholesale_price", "double", "none"),
            ("wholesale_walmart", "double", "none"),
            ("wholesale_costco", "double", "none"),
            ("wholesale_whole_foods", "double", "none"),
            ("wholesale_regional", "double", "none"),
            ("wholesale_unfi", "double", "none"),
            ("wholesale_dtc", "double", "none"),
        ],
    },
    {
        "name": "dim_promo",
        "csv": "dim_promo.csv",
        "columns": [
            ("promo_id", "string", "none"),
            ("sku", "string", "none"),
            ("retailer", "string", "none"),
            ("store_scope", "string", "none"),
            ("start_week", "dateTime", "none"),
            ("end_week", "dateTime", "none"),
            ("duration_weeks", "int64", "sum"),
            ("discount_depth_pct", "double", "none"),
            ("promo_type", "string", "none"),
            ("planned_cost", "double", "sum"),
            ("actual_cost", "double", "sum"),
            ("funding_mechanism", "string", "none"),
            ("asp", "double", "none"),
            ("baseline_avg_volume", "double", "none"),
            ("during_avg_volume", "double", "none"),
            ("incremental_volume", "double", "sum"),
            ("incremental_revenue", "double", "sum"),
            ("roi", "double", "none"),
            ("cost_source", "string", "none"),
            ("data_quality", "string", "none"),
        ],
    },
    {
        "name": "fact_deductions",
        "csv": "fact_deductions.csv",
        "columns": [
            ("deduction_id", "string", "none"),
            ("retailer_id", "string", "none"),
            ("deduction_date", "dateTime", "none"),
            ("deduction_type", "string", "none"),
            ("amount", "double", "sum"),
            ("code_as_remitted", "string", "none"),
            ("translated_code", "string", "none"),
            ("standardized_category", "string", "none"),
            ("order_id", "string", "none"),
            ("shipment_id", "string", "none"),
            ("remittance_id", "string", "none"),
            ("remittance_description", "string", "none"),
            ("dispute_deadline", "dateTime", "none"),
            ("is_vague", "int64", "none"),
            ("is_post_audit", "int64", "none"),
            ("is_double_dip", "int64", "none"),
            ("dispute_outcome", "string", "none"),
            ("recovered_amount", "double", "sum"),
            ("dispute_filed_date", "dateTime", "none"),
            ("dispute_closed_date", "dateTime", "none"),
            ("days_outstanding", "int64", "none"),
            ("in_trailing_window", "int64", "none"),
            ("is_ghost_promo", "int64", "none"),
        ],
    },
    {
        "name": "fact_structural_trade",
        "csv": "fact_structural_trade.csv",
        "columns": [
            ("retailer_id", "string", "none"),
            ("revenue", "double", "sum"),
            ("trade_rate", "double", "none"),
            ("structural_trade_dollars", "double", "sum"),
        ],
    },
    {
        "name": "fact_scan_data",
        "csv": "fact_scan_data.csv",
        "columns": [
            ("sku", "string", "none"),
            ("retailer", "string", "none"),
            ("store_id", "string", "none"),
            ("week_ending", "dateTime", "none"),
            ("units_sold", "int64", "sum"),
            ("dollars_sold", "double", "sum"),
            ("promo_id", "string", "none"),
            ("promo_period", "string", "none"),
        ],
    },
    {
        "name": "fact_disputes",
        "csv": "fact_disputes.csv",
        "columns": [
            ("dispute_id", "string", "none"),
            ("deduction_id", "string", "none"),
            ("retailer_id", "string", "none"),
            ("deduction_type", "string", "none"),
            ("deduction_amount", "double", "sum"),
            ("filed_date", "dateTime", "none"),
            ("closed_date", "dateTime", "none"),
            ("filing_method", "string", "none"),
            ("evidence_quality", "string", "none"),
            ("submitted_evidence_count", "int64", "sum"),
            ("was_within_deadline", "int64", "none"),
            ("outcome", "string", "none"),
            ("recovered_amount", "double", "sum"),
            ("labor_hours", "double", "sum"),
            ("days_to_resolve", "int64", "none"),
        ],
    },
]

# ── Calculated tables (DAX) ──────────────────────────────────────
# Column names must match what the DAX measures reference.

CALCULATED_TABLES = [
    {
        "name": "dim_date",
        "expression": (
            "VAR MinDate = MIN(fact_deductions[deduction_date])\n"
            "VAR MaxDate = MAX(fact_scan_data[week_ending])\n"
            "RETURN\n"
            "ADDCOLUMNS(\n"
            "    CALENDAR(MinDate, MaxDate),\n"
            "    \"year\", YEAR([Date]),\n"
            "    \"month\", MONTH([Date]),\n"
            "    \"year_month\", FORMAT([Date], \"YYYY-MM\"),\n"
            "    \"week_ending\",\n"
            "        [Date] + (6 - WEEKDAY([Date], 2)),\n"
            "    \"month_name\", FORMAT([Date], \"MMM YYYY\")\n"
            ")"
        ),
    },
    {
        "name": "WaterfallSteps",
        "expression": (
            "DATATABLE(\n"
            "    \"Step\", STRING,\n"
            "    \"SortOrder\", INTEGER,\n"
            "    {\n"
            "        {\"Revenue\", 1},\n"
            "        {\"Structural Trade\", 2},\n"
            "        {\"Operational Waste\", 3}\n"
            "    }\n"
            ")"
        ),
        "columns": [
            {"name": "Step", "dataType": "string",
             "sourceColumn": "Step", "sortByColumn": "SortOrder"},
            {"name": "SortOrder", "dataType": "int64",
             "sourceColumn": "SortOrder"},
        ],
    },
    {
        "name": "WindowWeeks",
        "expression": (
            "SELECTCOLUMNS("
            "GENERATESERIES(1, 8, 1), "
            "\"WindowWeeks Value\", [Value]"
            ")"
        ),
    },
    {
        "name": "TargetAllInRate",
        "expression": (
            "SELECTCOLUMNS("
            "GENERATESERIES(0, 0.50, 0.01), "
            "\"TargetAllInRate Value\", [Value]"
            ")"
        ),
    },
]

# ── Relationships ────────────────────────────────────────────────
# (from_table, from_column, to_table, to_column, is_active)
# Optional 6th element: "m2m" for many-to-many cardinality
# "from" = many side, "to" = one side (dimension/lookup) unless m2m

RELATIONSHIPS = [
    # dim_retailer joins (retailer_name for name-based, retailer_id for slug-based)
    ("fact_scan_data", "retailer", "dim_retailer", "retailer_name", True),
    ("fact_structural_trade", "retailer_id", "dim_retailer", "retailer_name", True),
    ("dim_promo", "retailer", "dim_retailer", "retailer_name", True),
    ("fact_deductions", "retailer_id", "dim_retailer", "retailer_id", True),
    # fact_disputes reaches dim_retailer through fact_deductions (avoids ambiguous path)
    ("fact_disputes", "retailer_id", "dim_retailer", "retailer_id", False),
    # dim_product joins
    ("fact_scan_data", "sku", "dim_product", "sku", True),
    ("dim_promo", "sku", "dim_product", "sku", False),  # inactive to avoid diamond
    # fact_disputes to fact_deductions
    ("fact_disputes", "deduction_id", "fact_deductions", "deduction_id", True),
]


# ── Builder functions ────────────────────────────────────────────

def _m_expression(table_def):
    """Build Power Query M expression to load a CSV with proper types."""
    csv_path = str(DATA_DIR / table_def["csv"])
    type_pairs = ", ".join(
        '{' + f'"{c[0]}", {M_TYPE[c[1]]}' + '}'
        for c in table_def["columns"]
    )
    return [
        "let",
        f'    Source = Csv.Document(File.Contents("{csv_path}"), '
        f'[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),',
        '    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
        '    #"Replaced Empties" = Table.ReplaceValue(#"Promoted Headers", '
        '"", null, Replacer.ReplaceValue, '
        'Table.ColumnNames(#"Promoted Headers")),',
        f'    #"Changed Type" = Table.TransformColumnTypes('
        f'#"Replaced Empties", {{{type_pairs}}})',
        "in",
        '    #"Changed Type"',
    ]


def _build_data_table(table_def):
    """Build a model.bim table object for a CSV-backed table."""
    columns = [
        {
            "name": name,
            "dataType": dtype,
            "sourceColumn": name,
            "summarizeBy": summarize,
        }
        for name, dtype, summarize in table_def["columns"]
    ]
    return {
        "name": table_def["name"],
        "columns": columns,
        "partitions": [
            {
                "name": table_def["name"],
                "mode": "import",
                "source": {
                    "type": "m",
                    "expression": _m_expression(table_def),
                },
            }
        ],
    }


def _build_calculated_table(ct):
    """Build a model.bim table object for a DAX calculated table."""
    tbl = {
        "name": ct["name"],
        "partitions": [
            {
                "name": ct["name"],
                "mode": "import",
                "source": {
                    "type": "calculated",
                    "expression": ct["expression"],
                },
            }
        ],
    }
    if "columns" in ct:
        tbl["columns"] = ct["columns"]
    return tbl


def _build_measures_table():
    """Build the hidden _Measures table containing all 49 DAX measures."""
    measures = []
    for m in MEASURES:
        obj = {"name": m["name"], "expression": m["expression"]}
        if m.get("formatString"):
            obj["formatString"] = m["formatString"]
        if m.get("displayFolder"):
            obj["displayFolder"] = m["displayFolder"]
        measures.append(obj)

    return {
        "name": "_Measures",
        "isHidden": True,
        "measures": measures,
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


def _build_relationships():
    """Build model.bim relationship objects."""
    rels = []
    for r in RELATIONSHIPS:
        from_t, from_c, to_t, to_c, active = r[:5]
        m2m = len(r) > 5 and r[5] == "m2m"
        rel = {
            "name": f"{from_t}_{from_c}___{to_t}_{to_c}",
            "fromTable": from_t,
            "fromColumn": from_c,
            "toTable": to_t,
            "toColumn": to_c,
        }
        if not active:
            rel["isActive"] = False
        if m2m:
            rel["fromCardinality"] = "many"
            rel["toCardinality"] = "many"
            rel["crossFilteringBehavior"] = "bothDirections"
        rels.append(rel)
    return rels


def _build_model_bim():
    """Assemble the complete model.bim (Tabular Object Model JSON)."""
    tables = [_build_data_table(t) for t in DATA_TABLES]
    tables += [_build_calculated_table(ct) for ct in CALCULATED_TABLES]
    tables.append(_build_measures_table())

    return {
        "name": "SemanticModel",
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-US",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "relationships": _build_relationships(),
            "annotations": [
                {
                    "name": "__PBI_TimeIntelligenceEnabled",
                    "value": "0",
                }
            ],
        },
    }


# ── Visual helpers ──────────────────────────────────────────────

SCHEMA_VC = ("https://developer.microsoft.com/json-schemas/fabric/"
             "item/report/definition/visualContainer/2.7.0/schema.json")
SCHEMA_PG = ("https://developer.microsoft.com/json-schemas/fabric/"
             "item/report/definition/page/1.0.0/schema.json")


def _mref(measure, table="_Measures"):
    return {
        "Measure": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": measure,
        }
    }


def _cref(table, column):
    return {
        "Column": {
            "Expression": {"SourceRef": {"Entity": table}},
            "Property": column,
        }
    }


def _lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def _proj(field, qref, nref=None):
    p = {"field": field, "queryRef": qref}
    p["nativeQueryRef"] = nref or qref.split(".")[-1]
    return p


def _sort_desc(measure):
    return {
        "sort": [{"field": _mref(measure), "direction": "Descending"}],
        "isDefaultSort": True,
    }


def _vc(name, x, y, w, h, vtype, query_state, title, z=0,
        sort=None, objects=None):
    vis = {"visualType": vtype}
    if query_state:
        q = {"queryState": query_state}
        if sort:
            q["sortDefinition"] = sort
        vis["query"] = q
    if objects:
        vis["objects"] = objects
    vis["visualContainerObjects"] = {
        "title": [{"properties": {
            "text": _lit(f"'{title}'"),
            "show": _lit("true"),
        }}]
    }
    vis["drillFilterOtherVisuals"] = True
    return {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h,
                      "tabOrder": z},
        "visual": vis,
    }


def _card(name, x, y, w, h, measure, title, z=0):
    return _vc(name, x, y, w, h, "card", {
        "Values": {"projections": [
            _proj(_mref(measure), f"_Measures.{measure}")
        ]}
    }, title, z)


def _col_chart(name, x, y, w, h, cat_tbl, cat_col, measure, title, z=0):
    return _vc(name, x, y, w, h, "clusteredColumnChart", {
        "Category": {"projections": [
            _proj(_cref(cat_tbl, cat_col), f"{cat_tbl}.{cat_col}", cat_col)
        ]},
        "Y": {"projections": [
            _proj(_mref(measure), f"_Measures.{measure}")
        ]},
    }, title, z, sort=_sort_desc(measure))


def _bar_chart(name, x, y, w, h, cat_tbl, cat_col, measure, title, z=0):
    return _vc(name, x, y, w, h, "barChart", {
        "Category": {"projections": [
            _proj(_cref(cat_tbl, cat_col), f"{cat_tbl}.{cat_col}", cat_col)
        ]},
        "Y": {"projections": [
            _proj(_mref(measure), f"_Measures.{measure}")
        ]},
    }, title, z, sort=_sort_desc(measure))


def _waterfall(name, x, y, w, h, cat_tbl, cat_col, sort_col,
               measure, title, z=0):
    return _vc(name, x, y, w, h, "waterfallChart", {
        "Category": {"projections": [
            _proj(_cref(cat_tbl, cat_col), f"{cat_tbl}.{cat_col}", cat_col)
        ]},
        "Y": {"projections": [
            _proj(_mref(measure), f"_Measures.{measure}")
        ]},
    }, title, z, sort={
        "sort": [{"field": _cref(cat_tbl, sort_col),
                  "direction": "Ascending"}],
        "isDefaultSort": True,
    })


def _donut(name, x, y, w, h, cat_tbl, cat_col, measure, title, z=0):
    return _vc(name, x, y, w, h, "donutChart", {
        "Category": {"projections": [
            _proj(_cref(cat_tbl, cat_col), f"{cat_tbl}.{cat_col}", cat_col)
        ]},
        "Y": {"projections": [
            _proj(_mref(measure), f"_Measures.{measure}")
        ]},
    }, title, z)


def _table_vis(name, x, y, w, h, fields, title, z=0):
    """fields: list of (table, property, is_measure) tuples."""
    projections = []
    for tbl, prop, is_m in fields:
        if is_m:
            projections.append(_proj(_mref(prop, tbl), f"{tbl}.{prop}"))
        else:
            projections.append(_proj(_cref(tbl, prop), f"{tbl}.{prop}", prop))
    return _vc(name, x, y, w, h, "tableEx", {
        "Values": {"projections": projections}
    }, title, z)


def _slicer(name, x, y, w, h, table, column, title, z=0):
    return _vc(name, x, y, w, h, "slicer", {
        "Values": {"projections": [
            _proj(_cref(table, column), f"{table}.{column}", column)
        ]}
    }, title, z)


def _textbox(name, x, y, w, h, text, font_size="12pt",
             font_color="#333333", font_weight=None, z=0):
    """Create a text box visual container."""
    text_style = {
        "fontFamily": ("'Segoe UI', wf_segoe-ui_normal, helvetica, "
                       "arial, sans-serif"),
        "fontSize": font_size,
        "color": font_color,
    }
    if font_weight:
        text_style["fontWeight"] = font_weight
    return {
        "$schema": SCHEMA_VC,
        "name": name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h,
                      "tabOrder": z},
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [{
                    "properties": {
                        "paragraphs": [{
                            "textRuns": [{
                                "value": text,
                                "textStyle": text_style,
                            }]
                        }]
                    }
                }]
            },
            "drillFilterOtherVisuals": True,
        },
    }


# ── Takeaway text (verbatim from DESIGN.md) ──────────────────

TAKEAWAYS = {
    "p1": (
        "Cinderhaven budgets 17.3% of revenue for trade spend — "
        "$4.4 million in negotiated rate-card allowances. Actual all-in "
        "cost is 21.3%. The 4-point gap is $1 million in annual "
        "operational waste: retailer deductions beyond the rate card, "
        "largely uncontested."
    ),
    "p2": (
        "Three categories account for two-thirds of operational waste: "
        "vague deductions ($294K), label fines ($197K), and short-ship "
        "charges ($184K). Three deductions totaling $19,306 are "
        "confirmed double-payments — the same promotion billed "
        "twice through different mechanisms."
    ),
    "p3": (
        "Of 160 measurable promotions, 104 destroyed value — the "
        "cost exceeded the incremental revenue. 137 promo-billback "
        "deductions totaling $95,826 reference promotions that don't "
        "appear in the planning calendar."
    ),
    "p4": (
        "Net-net margin ranges from 33.8% (Mountain Pantry Co) to "
        "12.5% (Walmart). Walmart contributes 51% of revenue but its "
        "21.5% structural rate compresses margin to less than half the "
        "portfolio average."
    ),
}

PAGE_TITLES = {
    "p1": "The Gap",
    "p2": "Where the Waste Goes",
    "p3": "Which Promos Work",
    "p4": "The Retailer Problem",
}


def _page_header(prefix, page_key):
    """Generate title text box and takeaway text box for a page."""
    return [
        _textbox(f"{prefix}_title", 10, 5, 1260, 40,
                 PAGE_TITLES[page_key], font_size="16pt",
                 font_color="#2E5090", font_weight="bold", z=0),
        _textbox(f"{prefix}_takeaway", 10, 48, 1260, 55,
                 TAKEAWAYS[page_key], font_size="12pt", z=1),
    ]


# ── Dashboard layout ───────────────────────────────────────────

def _cards(specs, y, prefix, z0=0):
    """Generate a row of equal-width KPI cards."""
    n = len(specs)
    gap = 10
    w = (1280 - gap * (n + 1)) // n
    return [
        _card(f"{prefix}{i}", gap + i * (w + gap), y, w, 100, m, t, z0 + i)
        for i, (m, t) in enumerate(specs)
    ]


def _build_pages():
    """Return list of (page_meta, visuals) for each dashboard page.

    Presentation layout: each page has 1 hero visual, 1–3 KPI cards,
    and a narrative takeaway text box.  No tables, no slicers.
    See DESIGN.md for the full design philosophy.
    """
    pages = []

    # ── Page 1: The Gap ────────────────────────────────────────
    p1 = _page_header("eo", "p1")
    p1.append(
        _waterfall("eo_waterfall", 40, 110, 1200, 380,
                   "WaterfallSteps", "Step", "SortOrder",
                   "WaterfallValue", "Trade Spend Waterfall", 100),
    )
    p1 += [
        _card("eo_c0", 30, 500, 400, 100,
              "AllInTradeRate", "All-In Trade Rate", 200),
        _card("eo_c1", 440, 500, 400, 100,
              "OperationalWasteAmount", "Operational Waste", 201),
        _card("eo_c2", 850, 500, 400, 100,
              "RecoveryRate", "Recovery Rate", 202),
    ]
    pages.append(({"id": "TheGap",
                   "displayName": "The Gap"}, p1))

    # ── Page 2: Where the Waste Goes ───────────────────────────
    p2 = _page_header("dd", "p2")
    p2.append(
        _bar_chart("dd_bars", 40, 110, 1200, 360,
                   "fact_deductions", "standardized_category",
                   "WasteAmount",
                   "Operational Waste by Category", 100),
    )
    p2 += [
        _card("dd_c0", 30, 480, 400, 100,
              "OperationalWasteAmount", "Total Waste", 200),
        _card("dd_c1", 440, 480, 400, 100,
              "DoubleDipTotal", "Double-Dip Total", 201),
        _card("dd_c2", 850, 480, 400, 100,
              "UnmappedCodeCount", "Unmapped Codes", 202),
    ]
    pages.append(({"id": "WasteBreakdown",
                   "displayName": "Where the Waste Goes"}, p2))

    # ── Page 3: Which Promos Work ──────────────────────────────
    p3 = _page_header("pp", "p3")
    # Hero — scatter (cost vs. incremental revenue)
    p3.append(
        _vc("pp_scatter", 20, 110, 820, 380, "scatterChart", {
            "X": {"projections": [
                _proj(_mref("PromoCost"), "_Measures.PromoCost")
            ]},
            "Y": {"projections": [
                _proj(_mref("IncrementalRevenue"),
                      "_Measures.IncrementalRevenue")
            ]},
            "Category": {"projections": [
                _proj(_cref("dim_promo", "promo_id"),
                      "dim_promo.promo_id", "promo_id")
            ]},
        }, "Promo Cost vs. Incremental Revenue", 100),
    )
    # Supporting — data quality donut
    p3.append(
        _donut("pp_donut", 870, 110, 380, 200,
               "dim_promo", "data_quality", "PromoCount",
               "POS Data Coverage", 200),
    )
    # KPI cards stacked vertically (right side)
    p3 += [
        _card("pp_c0", 870, 330, 380, 70,
              "AvgROI", "Avg Promo ROI", 300),
        _card("pp_c1", 870, 410, 380, 70,
              "GhostPromoCount", "Ghost Promos", 301),
        _card("pp_c2", 870, 490, 380, 70,
              "GhostPromoTotal", "Ghost Promo Exposure", 302),
    ]
    pages.append(({"id": "PromoPerformance",
                   "displayName": "Which Promos Work"}, p3))

    # ── Page 4: The Retailer Problem ───────────────────────────
    p4 = _page_header("rc", "p4")
    # Hero — net-net margin by retailer
    p4.append(
        _col_chart("rc_margin", 20, 110, 1240, 320,
                   "dim_retailer", "retailer_name",
                   "NetNetMarginPct",
                   "Net-Net Margin by Retailer", 100),
    )
    # Supporting — concentration risk (revenue share + deduction share)
    p4.append(
        _vc("rc_conc", 20, 450, 780, 250, "barChart", {
            "Category": {"projections": [
                _proj(_cref("dim_retailer", "retailer_name"),
                      "dim_retailer.retailer_name", "retailer_name")
            ]},
            "Y": {"projections": [
                _proj(_mref("RevenueShare"),
                      "_Measures.RevenueShare"),
                _proj(_mref("DeductionShare"),
                      "_Measures.DeductionShare"),
            ]},
        }, "Revenue Share vs. Deduction Share", 200,
        sort=_sort_desc("RevenueShare")),
    )
    # KPI card — highest risk retailer
    p4.append(
        _card("rc_c0", 830, 450, 430, 250,
              "HighestRiskRetailer", "Highest Risk Retailer", 300),
    )
    pages.append(({"id": "RetailerProblem",
                   "displayName": "The Retailer Problem"}, p4))

    return pages


# ── File writers ─────────────────────────────────────────────────

def _write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_project():
    """Generate all .pbip project files including visuals."""
    missing = [t["csv"] for t in DATA_TABLES if not (DATA_DIR / t["csv"]).exists()]
    if missing:
        print(f"ERROR: Missing CSV files in {DATA_DIR}:")
        for f in missing:
            print(f"  - {f}")
        print("\nRun 'python powerbi/export_data.py' first.")
        sys.exit(1)

    sem_dir = OUT_DIR / f"{PROJECT}.SemanticModel"
    rpt_dir = OUT_DIR / f"{PROJECT}.Report"
    rpt_def = rpt_dir / "definition"

    # Clean old pages/visuals from previous runs
    pages_dir = rpt_def / "pages"
    if pages_dir.exists():
        shutil.rmtree(pages_dir)

    # 1  .pbip project file
    _write_json(OUT_DIR / f"{PROJECT}.pbip", {
        "version": "1.0",
        "artifacts": [
            {"report": {"path": f"{PROJECT}.Report"}}
        ],
        "settings": {"enableAutoRecovery": True},
    })

    # 2  Semantic model pointer
    _write_json(sem_dir / "definition.pbism", {
        "version": "4.0",
        "settings": {},
    })

    # 3  model.bim
    _write_json(sem_dir / "model.bim", _build_model_bim())

    # 4  Report pointer
    _write_json(rpt_dir / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/"
                   "item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {
            "byPath": {"path": f"../{PROJECT}.SemanticModel"},
        },
    })

    # 5  Version metadata (2.0.0 required for visual container support)
    _write_json(rpt_def / "version.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/"
                   "item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0",
    })

    # 6  Report definition
    _write_json(rpt_def / "report.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/"
                   "item/report/definition/report/1.2.0/schema.json",
        "themeCollection": {
            "baseTheme": {
                "name": "CY24SU10",
                "reportVersionAtImport": "5.61",
                "type": "SharedResources",
            }
        },
        "layoutOptimization": "None",
        "settings": {
            "useStylableVisualContainerHeader": True,
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "useEnhancedTooltips": True,
            "useDefaultAggregateDisplayName": True,
        },
    })

    # 7  Pages and visuals
    all_pages = _build_pages()
    total_visuals = 0
    page_ids = []
    for page_meta, visuals in all_pages:
        pid = page_meta["id"]
        page_ids.append(pid)
        page_dir = rpt_def / "pages" / pid

        _write_json(page_dir / "page.json", {
            "$schema": SCHEMA_PG,
            "name": pid,
            "displayName": page_meta["displayName"],
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
        })

        for vis in visuals:
            vname = vis["name"]
            _write_json(page_dir / "visuals" / vname / "visual.json", vis)
            total_visuals += 1

    # 8  Page ordering metadata (required for page discovery)
    _write_json(rpt_def / "pages" / "pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/"
                   "item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": page_ids,
        "activePageName": page_ids[0],
    })

    # ── Summary ──
    pbip_path = OUT_DIR / f"{PROJECT}.pbip"
    print(f"Created: {pbip_path}")
    print(f"  Data tables:      {len(DATA_TABLES)}")
    print(f"  Calculated tables: {len(CALCULATED_TABLES)}")
    print(f"  DAX measures:     {len(MEASURES)}")
    print(f"  Relationships:    {len(RELATIONSHIPS)}")
    print(f"  Pages:            {len(all_pages)}")
    print(f"  Visuals:          {total_visuals}")
    print(f"\nData source: {DATA_DIR}")
    print(f"\nNext step: double-click {PROJECT}.pbip to open in Power BI Desktop.")


if __name__ == "__main__":
    write_project()
