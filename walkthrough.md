# Trade Spend Diagnostic — Walkthrough

Cinderhaven Provisions budgets 17% for trade spend. The actual cost
is 21%. The gap is $1 million per year — and nobody in the building
knew until the infrastructure to measure it was built.

That is the Monday-morning finding. A mid-market specialty food
company with $25.6M in wholesale revenue is losing 4 points of margin
to operational waste: retailer deductions taken beyond the negotiated
rate card, coded in retailer-specific formats, arriving weeks after
the transactions they reference, and largely uncontested. The
industry benchmark for all-in trade spend in natural/specialty CPG
is 19-23%. Cinderhaven's 17.3% structural rate is competitive. The
21.3% all-in rate is at the high end — not because the rate card is
wrong, but because $1M in unplanned deductions is being absorbed.

This walkthrough explains how the diagnostic was built, what it
found, and what to do about it. It is written for someone evaluating
whether this kind of analysis is worth commissioning for their own
data.

---

## 1. The problem

CPG companies in the $15M–$30M revenue band occupy an uncomfortable
middle ground in trade spend management. They are large enough to
sell through four or five retail channels, each with its own deduction
mechanics, code taxonomies, and billing timelines. They are too small
to justify dedicated trade promotion management software, which
typically requires $50K+ in annual licensing and a full-time analyst
to operate. The controller reconciles trade spend in Excel, working
from mismatched sources: a rate card negotiated by sales, deduction
remittances arriving from retailers in proprietary formats, promotional
calendars maintained in spreadsheets or email threads, and POS scan
data available through retailer portals with varying lag times and
granularity.

The structural result is that most companies at this scale know what
they *planned* to spend on trade but not what they *actually* spent.
The planned rate — the channel-by-channel allowance in the rate
card — is visible because someone negotiated it. The unplanned
cost — compliance fines, short-ship charges, pricing errors, vague
deductions with no clear cause — is invisible because it arrives as
line items on remittance statements that no one has time to
classify, cross-reference, or dispute before the filing window
closes.

The gap between planned and actual is not hypothetical. It is
measurable, and the measurement is the point of this diagnostic.
Cinderhaven's numbers are representative of the pattern: a 17.3%
planned trade rate, a 21.3% actual all-in rate, and $1 million in
the space between them that did not appear in any report until the
infrastructure to calculate it was built.

---

## 2. The methodology

### Two-bucket framing

Trade spend divides into two categories. **Structural trade** is
the planned, negotiated cost of doing business with each retailer —
the rate-card percentage applied to wholesale revenue. It is known
in advance, budgeted, and largely non-negotiable in the short term.
**Operational waste** is everything else: deductions taken by
retailers beyond the rate card, covering compliance fines, logistics
chargebacks, labeling penalties, spoilage claims, and deductions
with vague or missing reason codes.

An earlier version of the analysis attempted a three-bucket model,
separating promotional trade from structural and operational.
Investigation revealed that off-invoice allowances — the primary
promotional funding mechanism in Cinderhaven's contracts — are
already embedded in the rate card. Treating them as a separate
bucket double-counts. The promotions table's direct cost ($20,484
in planned spend) is too small to constitute a meaningful standalone
category at the executive level. The detail tabs break out
promotional performance separately; the executive framing stays at
two buckets.

### Data sources

Six source types feed the diagnostic, unified into 21 staging tables
in the Cinderhaven Postgres data platform:

- **SKU cost tables** — 90 products with COGS, wholesale prices by
  channel, and per-channel trade spend percentages. The structural
  trade calculation uses the channel-average rate (mean across all
  SKUs per channel), not per-SKU rates. The rate card is negotiated
  at the channel level; per-SKU application introduces false
  precision.
- **Deduction log** — 2,374 trailing-365-day deductions across 11
  retailers, each carrying a retailer-specific code, an amount, and
  a date. These are the raw material for the operational waste
  calculation.
- **Promotions calendar** — 188 planned promotions across four types
  (TPR, Feature, Display, BOGO), with planned costs and funding
  mechanisms.
- **POS scan data** — 601,341 weekly point-of-sale records from 11
  retailers, used to measure promotional lift.
- **Dispute records** — 1,410 filed disputes with outcomes and
  recovery amounts.
- **Deduction code crosswalk** — 97 retailer-specific codes mapped
  to a common 8-category taxonomy. The crosswalk handles naming
  inconsistencies across retailers — "WFM" versus "Whole Foods,"
  "short ship" versus "shipping shortage" — achieving a ~68% clean
  match rate. 292 deductions remain unmapped: their retailer codes
  have no entry in the crosswalk table
  (query: `dev/sql/crosswalk/deduction_codes.sql`).

### Promotion measurement

Promotional ROI uses a pre/during/post volume comparison against POS
scan data. Baseline volume is the average weekly units in the
pre-period window (adjustable from 1 to 8 weeks; default 4).
Incremental revenue is the lift in during-period volume over
baseline, multiplied by the average selling price. This is arithmetic
with stated assumptions, not causal inference. It does not control
for seasonality, competitor activity, or distribution changes. The
limitation is acknowledged; it is the appropriate methodology for a
diagnostic-level engagement.

---

## 3. The findings

### The headline

Cinderhaven's structural trade rate is 17.3% of revenue — $4,435,052
on $25,593,052 in trailing-twelve-month wholesale sales. The all-in
trade cost, including operational deductions, is 21.3% —
$5,446,000. The difference is $1,012,455 in operational waste,
representing 4.0% of revenue (see Tab 1: Executive Pulse).

### Where the waste comes from

Eight deduction categories compose the operational waste, led by
three that account for two-thirds of the total (query:
`dev/sql/deductions/waste_by_category.sql`):

| Category | Count | Amount | Share |
|----------|------:|-------:|------:|
| Vague / unclassified | 189 | $293,927 | 29.0% |
| Label fines | 344 | $197,488 | 19.5% |
| Short-ship charges | 814 | $184,411 | 18.2% |
| Spoilage claims | 102 | $92,446 | 9.1% |
| Late delivery | 457 | $87,869 | 8.7% |
| Slotting fees | 22 | $79,160 | 7.8% |
| Damaged goods | 98 | $63,321 | 6.3% |
| Pallet fines | 80 | $13,833 | 1.4% |

The largest single category — vague deductions with missing or
ambiguous reason codes — is the highest priority for investigation.
These are deductions where the retailer's remittance provides no
clear basis for the charge. The first step is requesting supporting
documentation from each retailer: a referenced invoice, a specific
compliance failure, a documented shortage. Deductions without a
specific, documented basis are disputable — the absence of clear
justification is itself the dispute grounds. The prevalence of vague
deductions is itself a diagnostic finding (see Tab 2: Leak
Diagnostic).

### Double-dip detection

Three deduction events totaling $19,306 were identified as
double-payments: the same promotion received both an off-invoice
discount on the original invoice and a subsequent promo-billback
deduction. The dollar amount is small. The finding is significant
because the matching infrastructure to detect double-dips — linking
deductions back to specific promotions by retailer, date window,
and amount — did not exist before this diagnostic was built (query:
`dev/sql/deductions/double_dip_events.sql`).

### Ghost promotions

137 promo-billback deductions totaling $95,826 reference promotions
that do not appear in Cinderhaven's promotion calendar. These "ghost
promos" have two possible explanations: the promotion existed but
was never recorded in the calendar, or the retailer billed for
promotional activity that did not take place. Both explanations
indicate a process gap — either in promotion planning or in
deduction validation (see Tab 3: Promo Efficacy; query:
`dev/sql/promo_roi/ghost_promo_summary.sql`).

### Promotion performance

Of 188 promotions in the trailing period, 160 have sufficient POS
scan data to measure ROI. Data coverage: 82% of promotions have
full pre/during/post POS data, 4% have partial coverage, and 14%
have no usable POS data at all.

Among the 160 measurable promotions, 48 (30%) generated positive
ROI — incremental revenue exceeding the promotion cost. Eight (5%)
were roughly breakeven. The remaining 104 (65%) generated negative
ROI: the cost of the promotion exceeded the incremental revenue it
produced. The distribution varies by promo type; TPRs (temporary
price reductions, 71 promotions) and Features (68) dominate the
calendar, while BOGOs (12) are the smallest category (see Tab 3:
Promo Efficacy; query: `dev/sql/promo_roi/promo_performance.sql`).

### Retailer margin spread

Net-net effective margin — gross margin minus all trade costs as a
percentage of revenue — ranges from 62.5% for DTC (which carries
no trade spend) to 12.5% for Walmart. Excluding DTC as a zero-trade
benchmark, the range is 33.8% (Mountain Pantry Co) to 12.5%
(Walmart). Walmart's position at the bottom reflects its 21.5%
structural trade rate — the highest in the portfolio — combined with
operational deductions that push the all-in rate further (see Tab 4:
Retailer Risk; query: `dev/sql/retailer/net_net_margin.sql`).

Five regional chains (Green Basket Market, Southside Grocers,
Prairie Provisions, Mountain Pantry Co, Harbor Fresh) cluster between
28% and 34% net-net margin, all on a 9.9% structural rate. Their
low trade cost is partly a function of scale — smaller retailers
have less bargaining power to extract allowances — and partly a function of
lower deduction volume. Concentration risk is the inverse concern:
Walmart contributes 51% of revenue but generates a disproportionate
share of deductions.

### Dispute recovery

Cinderhaven filed 1,410 disputes against retailer deductions,
recovering $98,216 — a 13.7% recovery rate by dollar value. The gap
between the amount disputed ($716,082) and the amount recovered
represents either valid deductions that were correctly upheld,
disputes where evidence was insufficient, or disputes that expired
before resolution. An adjustable recovery model in the workbook
shows the addressable improvement at higher target rates (query:
`dev/sql/reconciliation/recovery_rate.sql`).

### Data quality

292 of 2,374 trailing-year deductions (12.3%) have no crosswalk
translation — the retailer's code does not appear in the deduction
code table. These unmapped deductions still carry a dollar amount
and a category assignment from the raw data, but the human-readable
translation is missing. For promotions, the 14% of promotions with
no POS data represent a measurement gap: their ROI cannot be
evaluated at all. Both findings point to the same root cause —
incomplete integration between Cinderhaven's internal records and
retailer-provided data (see Tab 6: Deduction Code Crosswalk).

---

## 4. The deliverables

Four artifacts ship. Each is built for a different reader and a
different moment.

**The Excel workbook** (7 tabs) is the primary diagnostic. It opens
cold — no database connection, no setup. Tab 1 (Executive Pulse)
leads with the punchline: 17.3% structural, 4.0% operational, 21.3%
all-in, benchmarked against the 19-23% industry range. A 12-month
waste trend chart shows whether the problem is stable or accelerating.
Tabs 2 through 4 (Leak Diagnostic, Promo Efficacy, Retailer Risk)
provide supporting detail with adjustable inputs — a target recovery
rate, a promo comparison window, and per-retailer what-if trade
rates. The Retailer Risk tab includes a channel rollup (Walmart,
Costco, Whole Foods, UNFI, Regional, DTC, Distributor). Tab 5 is
the full deduction ledger with taxonomy classification per row. Tab 6
maps retailer codes to plain English. Tab 7 documents every
calculation, including the benchmark source.

**The executive memo** (`EXECUTIVE_MEMO.md`) is the one-page
condensation — the finding, where the money goes, and three things
to do Monday morning. This is the artifact that gets forwarded.

**The defensibility log** (`DEFENSIBILITY.md`) defines the
classification rules for every deduction bucket and provides the
rebuttal text — the answer to "your consultant doesn't understand
our business." Every "waste" or "unknown" tag has a one-line defense.

**The walkthrough** (this document) is the full methodology and
findings narrative for someone evaluating the analysis.

Two additional reference artifacts live in `dev/`: a SQL query
library (25 queries) for analysts who want to run their own cuts,
and Power BI design documentation (dashboard wireframes, 49 DAX
measures, pre-exported CSVs) for a future interactive implementation.

All deliverables are built from the same Postgres data platform. When
the underlying data is updated, the workbook is regenerated
(`python build_workbook.py`) and the numbers stay consistent because
there is one source.

---

## 5. What a real engagement would add

The diagnostic demonstrates that the data exists, the methodology
works, and the findings are quantified. It is a point-in-time
snapshot built from exported files. A live engagement would differ
in five respects.

**Causal promotion modeling.** The pre/during/post methodology
measures volume change during a promotion without controlling for
confounders. A real engagement would build seasonality-adjusted
baselines using 18–24 months of history, controlling for trends,
holidays, distribution changes, and competitor activity. The
difference matters: simple comparison overstates lift for products
that sell well in the promotion's season and understates it for
counter-seasonal items.

**Automated deduction classification.** The diagnostic's crosswalk
covers 97 codes across 11 retailers, with 292 deductions still
unmapped. A production system would ingest retailer EDI feeds
directly, apply ML-based code classification for new or ambiguous
codes, and maintain the crosswalk continuously rather than as a
static lookup table.

**System integration.** The diagnostic works from exported flat
files. A live engagement would connect to the ERP (invoice and
shipment data), the deduction management system (if one exists),
and retailer portals (deduction feeds, POS data, compliance
reports). Integration surfaces double-dips and ghost promos in near
real-time, not after a year of accumulation.

**Dispute workflow automation.** The current 13.7% recovery rate
reflects manual, reactive dispute filing. Automated workflows —
deadline tracking, evidence assembly, escalation rules,
auto-filing for categories with high win rates — typically push
recovery into the 25–35% range. On Cinderhaven's $716,082 in
disputed deductions, the difference between 13.7% and 30% recovery
is roughly $117,000 in additional annual recovery.

**Ongoing monitoring.** The diagnostic answers "where is the money
going?" once. The engagement answers it every month, with trend
reporting, exception alerts, and threshold triggers that flag new
patterns — a retailer whose deduction rate is climbing, a promotion
type whose ROI has turned negative, a compliance category that
spiked after a warehouse change. The value of the diagnostic is
proving the gap exists. The value of the engagement is preventing
it from reopening.
