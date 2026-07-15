# Project Audit

## Phase 1: Baseline Assessment
**Date:** 2026-05-16
**Project:** cinderhaven-data

### What Was Intended
The original data backbone for a portfolio of business-facing demo tools (velocity decision tool, deduction recovery dashboard, product data audit). Generates a realistic synthetic dataset for a fictional ~$25M specialty food brand (Cinderhaven Provisions) with 90 SKUs across multiple retail channels.

### What Exists Today
A synthetic dataset generator that now serves as a **seed source** for the newer `cinderhaven-data-platform` repo. The generation pipeline (15 Python scripts + 3 SQL seed files) produces a ~164MB SQLite database with 23+ tables covering product master, stores, distribution, costs, promotions, scan data, and a full deduction/dispute lifecycle. Three downstream repos still reference this as their data source.

- **Scripts:** 15 Python generators + 1 orchestrator (`build_db.py`) + 3 SQL seed files
- **Research:** 7 retailer markdown files (Costco, KeHE, Sprouts, UNFI, Walmart, Wegmans, Whole Foods)
- **Size:** ~5,500 LOC Python, ~670 LOC SQL
- **Tests:** Zero. Two validation scripts (`06_validate_dataset.py`, `15_validate_deductions.py`) exist but no unit/integration test suite.
- **Dependencies:** Python stdlib only (sqlite3, random, datetime, pathlib). No third-party packages.

### Tech Stack
- Python (stdlib only)
- SQLite
- No framework, no CI, no linting config

### Project Health Indicators
- **Activity:** Active — 8 commits over May 6-14 2026, single contributor
- **Documentation:** Good README, CONTRIBUTING.md, retailer research files. No CLAUDE.md, PLAN.md, or architecture docs.
- **Test coverage:** None (validation scripts are not tests — they check generated output, not code correctness)
- **Dependencies:** Current (no third-party deps to go stale)
- **CI/CD:** None
- **Linting/formatting:** No config (no pyproject.toml, no ruff/black/flake8 setup)

### Gap Analysis
| Area | Intended | Actual | Gap |
|---|---|---|---|
| Role | Primary data source for portfolio | Seed for cinderhaven-data-platform | Role has narrowed — README and downstream repo references may be stale |
| Quality assurance | Correct, reproducible dataset | No tests, no CI, no linting | No way to verify correctness except manual inspection or running validation scripts |
| Code standards | N/A (pre-workflow) | Unknown — built before workflow was established | Needs code quality review (Phase 2) |
| Downstream contract | Three repos consume the DB | Unknown if seed output matches platform expectations | Contract between this repo and platform is implicit, not validated |
| Reproducibility | Deterministic builds | Unknown — uses `random` module, seed handling unclear | May produce different output on each run |

### Audit Motivation
Built before the user had a solid development workflow in place. This audit is a retroactive quality check to verify the code is correctly structured and the generation pipeline is sound, now that standards are higher.

## Phase 2: Internal Review
**Date:** 2026-05-16
**Dimensions reviewed:** Code quality

### Top Opportunities (by leverage)

| # | Finding | Dimension | Impact | Effort | Leverage | Severity |
|---|---------|-----------|--------|--------|----------|----------|
| 1 | `gtin_invalid`/`upc_missing` copy-pasted across 3 scripts | Duplication | 4 | 1 | 4.0 | important |
| 2 | Regional chain names defined 5 times, 4 variable names, 3 data types | Duplication | 3 | 1 | 3.0 | important |
| 3 | `DB_PATH` constant hardcoded in all 17 scripts | Duplication | 3 | 1 | 3.0 | important |
| 4 | Mixed RNG pattern: 7 scripts use `random.seed()` (global), 7 use `random.Random()` (instance) | Consistency / Correctness | 4 | 2 | 2.0 | important |
| 5 | Three identical weighted-choice helpers in `01_generate_stores.py` | Duplication | 2 | 1 | 2.0 | minor |
| 6 | No context managers for SQLite connections (bare `con.close()`) | Robustness | 3 | 2 | 1.5 | important |
| 7 | `05_generate_scan_data.py` — 700+ line monolithic `main()` | Readability | 3 | 3 | 1.0 | important |
| 8 | Inconsistent type annotations (`from __future__ import annotations`, `-> None` on `main()`) | Consistency | 2 | 2 | 1.0 | minor |
| 9 | f-string SQL interpolation in validation scripts (safe but fragile pattern) | Fragility | 1 | 1 | 1.0 | minor |
| 10 | Global mutable `PASS_COUNT`/`FAIL_COUNT` in `06_validate_dataset.py` | Code smell | 1 | 1 | 1.0 | minor |

### Detailed Findings

#### Duplication

**1. `gtin_invalid` / `upc_missing` — 3 identical copies (important)**
These defect-detection functions are copy-pasted in:
- [02_generate_distribution.py:66-81](scripts/02_generate_distribution.py:66)
- [02b_generate_chargebacks.py:47-58](scripts/02b_generate_chargebacks.py:47)
- [05_generate_scan_data.py:96-108](scripts/05_generate_scan_data.py:96)

If the defect logic ever changes, you'd need to update 3 files and hope you don't miss one. Extract to a shared module.

**2. Regional chain names — 5 definitions, 4 names, 3 types (important)**
The same 5 chain names appear in:
- `REGIONAL_CHAINS` as a `list` in `02_generate_distribution.py`
- `REGIONAL_CHAINS` as a `tuple` in `04b_generate_price_history.py`
- `REGIONAL_CHAIN_NAMES` as a `set` in `05_generate_scan_data.py`
- `REGIONAL_CHAIN_NAMES` as a `set` in `04_generate_promos.py`
- `REGIONAL_CHAINS` as a SQL string literal in `06_validate_dataset.py`

Adding or renaming a chain requires editing 5 files. One source of truth would eliminate drift.

**3. `DB_PATH` — 17 identical definitions (important)**
Every script independently computes `DB_PATH = Path(__file__).resolve().parent.parent / "data" / "cinderhaven_product_master.db"`. Moving the database file requires 17 edits.

#### Consistency

**4. Mixed RNG patterns (important)**
The base pipeline scripts (01-06) use `random.seed(SEED)` — seeding the **global** random state. The deduction pipeline scripts (08-14) use `rng = random.Random(SEED)` — isolated instances.

The instance-based approach is strictly better:
- Global state can be silently corrupted if any imported module calls `random.*`
- Instance-based makes it explicit which RNG is used where
- Script 05 already partially migrated — it uses global seed for main logic but creates `random.Random(SEED + 7)` and `random.Random(SEED + 8)` for sub-generators

Current seeds are intentionally varied (42 for base, 43-48 for deduction), and the subprocess isolation means this isn't causing bugs today. But standardizing on instance-based would be more robust.

**8. Inconsistent type annotations (minor)**
Some scripts use `from __future__ import annotations` (build_db, 05, 08, 11, 14), most don't. Some have `-> None` on `main()`, others have no return annotation. Not functional but inconsistent.

#### Robustness

**6. No context managers for DB connections (important)**
All 17 scripts use bare `con = sqlite3.connect(DB_PATH)` / `con.close()`. If an exception is thrown between connect and close, the connection leaks and the DB may be left in a partial state with uncommitted WAL data. Only `build_db.py:seed_product_master()` uses try/finally.

Fix: use `with sqlite3.connect(DB_PATH) as con:` or wrap in try/finally.

#### Readability

**7. `05_generate_scan_data.py` — 700+ line `main()` (important)**
This is the largest and most complex script. Its `main()` function handles:
- Loading reference data (products, wholesale prices, stores, defects, distribution)
- Computing time-to-shelf delays
- Computing ghost pairs
- Tier inference
- Base velocity assignment
- Launch week computation
- Failed launch selection and deauth updates
- Promo interval mapping
- Decline-end factors
- DTC dollar splits
- Organic trends, seasonality strength, cannibalization
- UNFI/DTC cycles, stockout episodes
- The actual scan_data generation loop
- Summary printing

Each of these could be a named function. The inner loop (lines 597-694) compounds ~13 multiplicative factors in a single pass — correct, but hard to verify by reading.

#### Code Smells (minor)

**5. Three identical weighted-choice functions in `01_generate_stores.py` (minor)**
`weighted_state()`, `weighted_region()`, `weighted_tier()` on lines 40-55 are structurally identical — all do `random.choices(keys, weights, k=1)[0]` from a dict. One `weighted_pick(distribution)` function would suffice.

**9. f-string SQL interpolation in validation (minor)**
`06_validate_dataset.py` embeds `REGIONAL_CHAINS` as a string literal directly into SQL via f-strings. The value is a hardcoded constant so there's no injection vulnerability, but the pattern would be flagged by any linter.

**10. Global mutable counters in validation (minor)**
`PASS_COUNT` and `FAIL_COUNT` as module globals with `global` keyword is a code smell. A dataclass or simple counter object would be cleaner.

### What's Actually Good

The codebase has real strengths worth noting:

- **Thoughtful domain modeling.** The layered velocity model (13 multiplicative factors), defect-driven narratives, and retailer-specific profiles show deep domain understanding. This isn't cookie-cutter synthetic data.
- **Deterministic builds.** Every script seeds its RNG, and the subprocess pipeline ensures isolation. Builds are reproducible.
- **Clear docstrings.** Each script's module docstring explains what it generates and why. The comments in scan_data's layered model are genuinely helpful.
- **Good orchestrator.** `build_db.py` handles force rebuilds, WAL cleanup, output redirection, and error propagation cleanly.
- **Validation scripts exist.** While not unit tests, the behavioral checks in `06_validate_dataset.py` and `15_validate_deductions.py` catch real problems (revenue targets, lift ratios, referential integrity).
- **Consistent structure.** Every script follows the same pattern: constants at top, helpers in middle, `main()` at bottom, summary print at end. Easy to navigate.

### Summary

The code is **functionally sound and well-structured** — the pipeline works, builds are reproducible, and the domain modeling is sophisticated. The main issues are maintenance-oriented: duplicated constants and utility functions across 17 scripts that should be in a shared module, and inconsistent RNG patterns between the base and deduction pipelines. The highest-leverage fix is extracting shared code (`DB_PATH`, `gtin_invalid`/`upc_missing`, regional chain names) into a common module — low effort, eliminates the most dangerous drift vectors.

## Phase 3: Landscape Scan
**Date:** 2026-05-16
**Category:** Synthetic dataset generator for realistic business/retail (CPG) data — deterministic pipeline producing a multi-table relational database with domain-specific causal narratives.

### Competitors / Similar Projects

| # | Name | Type | Description | Traction |
|---|------|------|-------------|----------|
| 1 | Faker | OSS library | Single-field fake data (names, addresses, etc.). Seeded, no relational logic. | 19.3k stars |
| 2 | Mimesis | OSS library | Fast locale-aware fake data. Schema system but no FK consistency. | ~4k stars |
| 3 | SDV (Synthetic Data Vault) | OSS library | ML-based multi-table synthesis. Learns distributions from real data. | 3.5k stars |
| 4 | DATAMIMIC CE | OSS pipeline | Model-driven deterministic pipeline with referential integrity. XML/Python. | 33 stars |
| 5 | Mostly AI SDK | OSS + commercial | ML-based synthesis with differential privacy. Requires training data. | 773 stars |
| 6 | dbldatagen (Databricks) | OSS library | PySpark generator for billions of rows. FK support. Requires Spark. | 465 stars |
| 7 | Gretel Relational | Commercial SaaS | Cloud multi-table synthesis from uploaded schemas. $295/mo team tier. | Funded startup |
| 8 | Tonic Fabricate | Commercial SaaS | LLM-powered "describe your data" relational generation. | Funded startup |
| 9 | Northwind / AdventureWorks | Sample DBs | Static pre-built demo databases. Not regenerable. | Decades of use |
| 10 | Dunnhumby Complete Journey | Static dataset | Real retail transaction data (Kaggle). Retailer-side only. | Academic standard |

**Cross-domain analog:** Synthea (healthcare) — generates longitudinal synthetic patient records with causal pathways, seeded RNG, multi-table relational output. The structural parallel to this project is direct: domain logic encoded as rules, not learned from data. Synthea is widely used in EHR research and medical school curricula.

### Feature Matrix

| Feature | cinderhaven-data | Faker | Mimesis | SDV | DATAMIMIC | Mostly AI | dbldatagen | Gretel | Tonic | Northwind |
|---------|-----------------|-------|---------|-----|-----------|-----------|------------|--------|-------|-----------|
| Multi-table relational output | ✅ 23+ tables | ❌ | ❌ | ✅ ~5 tables | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ static |
| Cross-table FK consistency | ✅ | ❌ | ❌ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ static |
| Deterministic / reproducible | ✅ seeded RNG | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ➖ static |
| Domain-specific business logic | ✅ deep CPG | ❌ generic | ❌ generic | ❌ statistical | 🟡 finance/health | ❌ statistical | ❌ generic | ❌ | ❌ | 🟡 basic |
| Causal narratives across tables | ✅ defect→chargeback→deauth | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Retail/CPG domain | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Zero external dependencies | ✅ stdlib only | ❌ pip | ❌ pip | ❌ PyTorch | ❌ | ❌ ML stack | ❌ Spark | ❌ cloud | ❌ cloud | ➖ |
| Learns from real data | ❌ rules-based | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | 🟡 LLM | ❌ |
| Scale (1M+ rows) | ✅ 1.19M scan_data | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ billions | ✅ | ✅ | ❌ small |
| Configurable parameters | 🟡 code-level | ✅ API | ✅ API | ✅ API | ✅ XML/API | ✅ API | ✅ API | ✅ UI | ✅ UI | ❌ |
| Validation / sanity checks | ✅ 2 scripts | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Portfolio / demo use case | ✅ primary purpose | ❌ testing | ❌ testing | ❌ ML | ❌ compliance | ❌ ML | ❌ testing | ❌ ML | 🟡 demos | ✅ |
| Deduction/dispute lifecycle | ✅ full pipeline | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Seasonal/trend patterns | ✅ 13 factors | ❌ | ❌ | 🟡 if in source | ❌ | 🟡 if in source | ❌ | 🟡 | ❌ | ❌ |

### Landscape Position

#### Table Stakes (standard in category)
Features most competitors have that this project should maintain:
- ✅ Multi-table relational output — **has it**
- ✅ Reproducible output — **has it**
- 🟡 Configurable parameters — **partial.** Parameters are embedded in code (constants at top of each script), not exposed via CLI args or config file. Every competitor with an API or UI does this better.
- ❌ Programmatic API — **missing.** No way to `import cinderhaven` and generate a subset. Every library-style competitor offers this.

#### Where This Project Is Stronger
- **Causal narrative depth.** No competitor encodes multi-hop causal chains (data defect → delayed shelf setup → muted promo lift → chargeback → deauthorization). This is the project's defining capability. SDV can statistically reproduce correlations it's trained on, but it can't generate a narrative it hasn't seen.
- **CPG domain realism.** Retailer-specific profiles (Walmart SQEP fines, UNFI MCB billbacks, KeHE 48hr UDR), 13-factor velocity model, deduction/dispute lifecycle with evidence quality branching. No competitor covers this domain at all.
- **Zero-dependency portability.** stdlib-only Python + SQLite. No Spark, no PyTorch, no cloud account, no API key. Clone and run.
- **Built-in validation.** Two validation scripts that check behavioral invariants (revenue targets, promo lift, seasonality, referential integrity). No competitor includes this.

#### Where This Project Is Weaker
- **No API / no library interface.** You can't `from cinderhaven import generate(tables=["scan_data"], weeks=52)`. It's a monolithic pipeline — all or nothing.
- **Configuration is code-level.** Changing the number of stores, the revenue target, or the date window means editing Python constants across multiple files. Competitors offer config files, CLI args, or GUIs.
- **Single domain, single scenario.** Faker/SDV/Gretel can generate data for any domain. This only generates Cinderhaven.
- **No privacy/compliance features.** ML-based tools (SDV, Mostly AI, Gretel) offer differential privacy guarantees. Not relevant for synthetic-from-scratch data, but it's a category trend.
- **No incremental generation.** The pipeline is all-or-nothing rebuild. Can't add 10 more weeks of scan data without regenerating from scratch.

#### Unique Differentiators
Things only this project does:
- **Trade deduction lifecycle.** No synthetic data tool — open-source or commercial — generates deduction codes, dispute filings, evidence quality branching, or post-audit clawbacks. This is a greenfield domain.
- **Defect-driven narratives.** The thesis that data-quality defects in `product_master` causally drive downstream failures (chargebacks, slow launches, delistings) is encoded as simulation logic, not just described in docs.
- **Retailer-aware behavioral profiles.** Walmart's OTIF penalties work differently from UNFI's flat fines, and the data reflects this.
- **Portfolio-native.** Built specifically to make downstream demo tools look real. The data isn't just statistically plausible — it tells a story.

#### Category Trends
Based on what newer/popular projects emphasize:
1. **ML-based synthesis is mainstream** — SDV, Mostly AI, Gretel all learn from real data. Rules-based generation (this project's approach) is less common but has the advantage of not requiring real data input.
2. **Privacy is a selling point** — differential privacy, GDPR compliance. Not relevant when generating from scratch, but it's where funding goes.
3. **Multi-table is table stakes** — single-table generation is now considered basic. The market has moved to relational-aware tools.
4. **LLM-powered generation emerging** — Tonic Fabricate uses LLMs to generate from natural language descriptions. Early but growing.
5. **No CPG/retail-specific tools exist** — Dunnhumby and Instacart datasets are static exports of real data. No one is building synthetic generators for this vertical. The closest cross-domain analog is Synthea (healthcare).

### Summary

**cinderhaven-data occupies an empty niche.** There is no open-source or commercial tool that generates synthetic CPG brand data with trade deduction lifecycles, retailer-specific behavioral profiles, and causal narrative chains. The closest structural analog is Synthea in healthcare — same pattern (domain rules → deterministic multi-table output), different vertical. The project's weaknesses (no API, code-level config, single-scenario) are typical of early-stage domain generators and are the natural areas to improve if the project ever expands beyond personal seed use. For its current purpose — a realistic, regenerable seed database for portfolio demos — it has no direct competition.

## Phase 4: Differentiation & Next Moves
**Date:** 2026-05-16

### Cross-Reference Summary

The Phase 2 internal findings and Phase 3 landscape position tell a clear story: **the domain modeling is the asset; the code hygiene is the liability.** Every competitor either generates shallow generic data (Faker, Mimesis) or requires real data input to learn from (SDV, Gretel, Mostly AI). This project's unique value — deterministic causal narratives for CPG trade deductions — is not threatened by any competitor. What *is* at risk is maintainability: duplicated code across 17 scripts means any future change to the seed logic (new retailer, new defect type, schema change for the platform) requires touching many files with no safety net.

The project's current role as a **seed generator for cinderhaven-data-platform** means most of the Phase 3 competitive gaps (no API, no config, single scenario) are irrelevant to fix right now. You don't need a library interface for a pipeline that runs once to seed a downstream platform. The right moves are almost entirely foundational: clean up the code so it's correct, maintainable, and aligned with your current workflow standards — then leave it alone.

The one strategic move worth considering is protecting the reproducibility advantage. The mixed RNG patterns (global vs instance) are a latent risk: if you ever import a shared module or change script execution order, global `random.seed()` could produce different output silently. Standardizing on instance-based RNG is cheap insurance for the one property that matters most in a seed generator.

### Ranked Next Moves

| # | Move | Category | Strategic | Internal | Effort | Score | Description |
|---|------|----------|-----------|----------|--------|-------|-------------|
| 1 | Extract `scripts/shared.py` | Foundational | 2 | 5 | 1 | 7.0 | Move `DB_PATH`, `gtin_invalid`, `upc_missing`, `REGIONAL_CHAIN_NAMES` into one shared module. Eliminates Phase 2 findings #1, #2, #3 in a single move. |
| 2 | Update README to reflect seed role | Close gap | 3 | 3 | 1 | 6.0 | README still describes this as the primary data source for 3 downstream repos. Update to reflect its actual role as a seed for cinderhaven-data-platform. |
| 3 | Add `pyproject.toml` + ruff config | Close gap | 2 | 3 | 1 | 5.0 | Every maintained project has linting. A minimal pyproject.toml with ruff catches issues automatically. Zero third-party runtime deps still holds — ruff is dev-only. |
| 4 | Add context managers for DB connections | Foundational | 1 | 3 | 1 | 4.0 | Replace bare `con.close()` with `with` statements. Prevents resource leaks on error. Mechanical find-and-replace across all scripts. |
| 5 | Add `CLAUDE.md` for this project | Foundational | 1 | 3 | 1 | 4.0 | You have a workflow now. This project should have a CLAUDE.md with tier, stack, and current focus so future sessions start informed. |
| 6 | Standardize RNG to instance-based | Double down | 3 | 4 | 2 | 3.5 | Migrate the 7 base scripts from `random.seed(SEED)` to `rng = random.Random(SEED)`. Protects the reproducibility advantage that competitors can't match. |
| 7 | Break up `05_generate_scan_data.py` | Foundational | 1 | 4 | 3 | 1.7 | Extract the ~15 logical sections of the 700-line `main()` into named functions. Correct but hard to verify as-is. |
| 8 | Consistent type annotations | Foundational | 1 | 2 | 2 | 1.5 | Standardize `from __future__ import annotations` and `-> None` across all scripts. |

### Recommended Sequence

**Batch 1 — Quick wins (1 session, ~30 min):**
1. Extract `scripts/shared.py` (finding #1-3 resolved)
2. Add context managers (finding #6 resolved)
3. Add `CLAUDE.md`

**Batch 2 — Standards alignment (1 session, ~30 min):**
4. Add `pyproject.toml` + ruff, fix any lint issues
5. Update README
6. Consistent type annotations (finding #8 resolved)

**Batch 3 — Robustness (1 session, ~45 min):**
7. Standardize RNG to instance-based (finding #4 resolved)
8. Rebuild and verify output matches expectations

**Batch 4 — If time permits:**
9. Break up `scan_data.py` (finding #7 — optional, high effort relative to payoff for a seed generator)

### What NOT to Do

- **Don't build an API/library interface.** Phase 3 flagged this as a gap vs competitors, but it doesn't matter for a seed generator. You run the pipeline once, it produces the DB, the platform consumes it. An importable `cinderhaven.generate()` would be premature abstraction for a single-consumer pipeline.
- **Don't add CLI configuration.** Same reasoning. Editing constants in code is fine when the consumer is just you and the pipeline runs infrequently. Config files add indirection without value here.
- **Don't chase ML-based synthesis.** SDV/Gretel/Mostly AI learn from real data. Your approach (rules-based, domain-encoded) is a *different tool for a different job*, not an inferior version of theirs. Don't try to converge.
- **Don't add incremental generation.** Full rebuild is fine for a seed. The pipeline takes minutes, not hours. Incremental generation adds complexity for a scenario (weekly appends) that doesn't exist.
- **Don't over-invest in the validation scripts.** They work. Converting them to pytest would be nice but adds a third-party dep and doesn't catch new bugs — the validation logic itself is the value, not the test framework.
