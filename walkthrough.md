# Trade Spend Diagnostic — Walkthrough

Cinderhaven Provisions, a specialty food company with $32.8 million
in trailing-52-week scan revenue, carries a structural trade rate
of 9.9% (~$3.2M) — competitive for natural/specialty CPG. All-in
trade cost including operational deductions is 12.2%. The rate card
is not the problem. The 3-point gap above it is: $977K per year in
operational waste buried inside the deductions — vague charges with
no clear basis ($417K, 33% lacking even a PO reference),
uncontested spoilage and short-ship claims, compliance fines, and
duplicate payments. Cinderhaven recovers 20.9% of what it
disputes. The rest expires unclassified.

This walkthrough explains how the diagnostic was built, what it
found, and what each deliverable does. It is written for someone
evaluating whether this kind of analysis is worth commissioning for
their own data.

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
they *planned* to spend on trade but not what they *actually* lost
to operational waste. The planned rate — the channel-by-channel
allowance in the rate card — is visible because someone negotiated
it. The unplanned cost — compliance fines, short-ship charges,
pricing errors, vague deductions with no clear cause — is invisible
because it arrives as line items on remittance statements that no
one has time to classify, cross-reference, or dispute before the
filing window closes.

The waste is measurable, and the measurement is the point of this
diagnostic. Cinderhaven's numbers are representative of the pattern:
a 9.9% structural trade rate that is competitive, and $977K per
year in operational waste (3.0% of scan revenue) that did not
appear in any report until the infrastructure to calculate it was
built. The all-in trade cost is 12.2% — the 3-point delta above
the structural rate is not a rate problem, but a magnitude problem
hiding in the noise.

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
bucket double-counts. The promotions table's direct cost ($16,357
in planned spend) is too small to constitute a meaningful standalone
category at the executive level. The detail tabs break out
promotional performance separately; the executive framing stays at
two buckets.

### Data sources

Six source types feed the diagnostic, unified into 22 tables in a
single SQLite database:

- **SKU cost tables** — 50 products with COGS, wholesale prices by
  channel, and per-channel trade spend percentages. The structural
  trade calculation uses the channel-average rate (mean across all
  SKUs per channel), not per-SKU rates. The rate card is negotiated
  at the channel level; per-SKU application introduces false
  precision.
- **Deduction log** — 5,375 trailing-365-day deductions across 9
  retailers, each carrying a retailer-specific code, an amount, and
  a date. These are the raw material for the operational waste
  calculation.
- **Promotions calendar** — 138 planned promotions across four types
  (TPR, Feature, Display, BOGO), with planned costs and funding
  mechanisms.
- **POS scan data** — weekly point-of-sale records from 9
  retailers, used to measure promotional lift.
- **Dispute records** — 5,395 filed disputes with outcomes and
  recovery amounts.
- **Deduction code crosswalk** — retailer-specific codes mapped
  to a common taxonomy. Fuzzy matching (via rapidfuzz)
  handles naming inconsistencies across retailers — "WFM" versus
  "Whole Foods," "short ship" versus "shipping shortage."

### Promotion measurement

Promotional ROI uses a pre/during/post volume comparison against POS
scan data. Baseline volume is the average weekly units in the
pre-period window (adjustable from 1 to 12 weeks; default 4).
Incremental revenue is the lift in during-period volume over
baseline, multiplied by the average selling price. This is arithmetic
with stated assumptions, not causal inference. It does not control
for seasonality, competitor activity, or distribution changes. The
limitation is acknowledged; it is the appropriate methodology for a
diagnostic-level engagement.

---

## 3. The findings

### The headline

Cinderhaven's structural trade rate is 9.9% of trailing-52-week
scan revenue ($32.8M) — ~$3.2M in planned trade. The all-in trade
cost, including operational deductions, is 12.2% ($3.98M). The
operational waste layer is $977K trailing-365-day, representing
3.0% of scan revenue — the 3-point gap between the structural
rate and the all-in rate (see Tab 1: Executive Pulse).

The rate is not the story. The magnitude of waste — nearly $1M per
year in charges that are avoidable, contestable, or unjustifiable —
is the story.

### Where the waste comes from

Nine deduction categories compose the operational waste, led by
one that accounts for 43% of the total (query:
`deductions/waste_by_category.sql`):

| Category | Count | Amount | Share |
|----------|------:|-------:|------:|
| Vague / unclassified | 318 | $416,967 | 42.7% |
| Spoilage claims | 728 | $153,212 | 15.7% |
| Label fines | 322 | $105,522 | 10.8% |
| Short-ship charges | 756 | $96,323 | 9.9% |
| Damaged goods | 734 | $95,527 | 9.8% |
| Pallet fines | 252 | $45,440 | 4.6% |
| Late delivery | 607 | $30,925 | 3.2% |
| Slotting fees | 6 | $27,680 | 2.8% |
| Pricing errors | 157 | $5,704 | 0.6% |

The dominant category — vague deductions with missing or
ambiguous reason codes — is $417K. These are deductions where the
retailer's remittance provides no clear basis for the charge. Of
the 318 vague deductions in the trailing year, 106 (33%) lack
even a PO reference, making them untraceable to a specific order.
The prevalence of vague deductions is itself a diagnostic finding:
it means the deduction pipeline has no classification layer, so the
largest category of waste is the least understood (see Tab 2: Leak
Diagnostic).

### Double-dip detection

Three deduction events totaling $19,062 were identified as
double-payments: the same promotion received both an off-invoice
discount on the original invoice and a subsequent promo-billback
deduction. The dollar amount is not the point. The finding is
significant because the matching infrastructure to detect
double-dips — linking deductions back to specific promotions by
retailer, date window, and amount — did not exist before this
diagnostic was built (query: `deductions/double_dip_events.sql`).

### Ghost promotions

3,258 promo-billback deductions totaling $361K reference promotions
that do not appear in Cinderhaven's promotion calendar. These "ghost
promos" have two possible explanations: the promotion existed but
was never recorded in the calendar, or the retailer billed for
promotional activity that did not take place. Both explanations
indicate a process gap — either in promotion planning or in
deduction validation (see Tab 3: Promo Efficacy; query:
`promo_roi/ghost_promo_summary.sql`).

### Retailer margin spread

Net-net effective margin — gross margin minus all trade costs as a
percentage of revenue — varies significantly across the retailer
portfolio. DTC carries no trade spend and represents the zero-trade
benchmark. Excluding DTC, the spread reflects both the structural
rate negotiated with each channel and the operational deductions
layered on top (see Tab 4: Retailer Risk; query:
`retailer/net_net_margin.sql`).

### Dispute recovery

Cinderhaven filed 5,395 disputes against retailer deductions,
recovering $232K — a 20.9% recovery rate by dollar value.
An adjustable recovery model in the workbook shows the addressable
improvement at higher target rates (query:
`reconciliation/recovery_rate.sql`).

### Data quality

Some trailing-year deductions have no crosswalk translation — the
retailer's code does not appear in the deduction code table. These
unmapped deductions still carry a dollar amount and a category
assignment from the raw data, but the human-readable translation is
missing. Both this and any promotions with no POS data represent
measurement gaps that point to incomplete integration between
Cinderhaven's internal records and retailer-provided data (see
Tab 6: Deduction Code Crosswalk).

---

## 4. The deliverables

Three artifacts consume the same underlying database. Each is built
for a different user and a different moment.

**The Excel workbook** (7 tabs) is the static diagnostic. It opens
cold — no database connection, no setup. Tab 1 (Executive Pulse)
leads with the waste-magnitude punchline: 9.9% structural,
3.0% operational waste, $977K trailing-365, 12.2% all-in. Tabs 2 through 4
(Leak Diagnostic, Promo Efficacy, Retailer Risk) provide the
supporting detail with adjustable inputs — a target recovery rate,
a promo comparison window, and per-retailer what-if trade rates.
Tab 5 (Deduction Ledger) is the full trailing-year data with
auto-filters and freeze panes. Tab 6 maps retailer codes to plain
English. Tab 7 documents every calculation. Color-coded: navy for
analysis tabs, teal for data, gray for reference.

**The SQL query library** (25 queries in 6 categories) is for the
analyst who wants to run their own cuts. Each `.sql` file answers
one diagnostic question — from "What is total revenue?" to "Which
promo-billback deductions have no matching promotion?" A 10-step
suggested execution order mirrors the diagnostic narrative, from
revenue through waste, promotions, retailer risk, and recovery.

All deliverables are built from the same SQLite database, maintained
as a git submodule. When the underlying data is updated, the workbook
is regenerated (`python build_workbook.py`) and the numbers stay
consistent because there is one source.

---

## 5. What a real engagement would add

The diagnostic demonstrates that the data exists, the methodology
works, and the findings are quantified. It is a point-in-time
snapshot built from exported files. A live engagement would differ
in five respects.

**Causal promotion modeling.** The pre/during/post methodology
measures volume change during a promotion without controlling for
confounders. A real engagement would build seasonality-adjusted
baselines using 18-24 months of history, controlling for trends,
holidays, distribution changes, and competitor activity. The
difference matters: simple comparison overstates lift for products
that sell well in the promotion's season and understates it for
counter-seasonal items.

**Automated deduction classification.** The diagnostic's crosswalk
covers retailer-specific codes across 9 retailers. A production
system would ingest retailer EDI feeds directly, apply ML-based
code classification for new or ambiguous codes, and maintain the
crosswalk continuously rather than as a static lookup table.

**System integration.** The diagnostic works from exported flat
files. A live engagement would connect to the ERP (invoice and
shipment data), the deduction management system (if one exists),
and retailer portals (deduction feeds, POS data, compliance
reports). Integration surfaces double-dips and ghost promos in near
real-time, not after a year of accumulation.

**Dispute workflow automation.** The current 20.9% recovery rate
reflects manual, reactive dispute filing. Automated workflows —
deadline tracking, evidence assembly, escalation rules,
auto-filing for categories with high win rates — typically push
recovery into the 25-35% range.

**Ongoing monitoring.** The diagnostic answers "where is the money
going?" once. The engagement answers it every month, with trend
reporting, exception alerts, and threshold triggers that flag new
patterns — a retailer whose deduction rate is climbing, a promotion
type whose ROI has turned negative, a compliance category that
spiked after a warehouse change. The value of the diagnostic is
proving $977K of recoverable, contestable waste exists where it
was invisible. The value of the engagement is preventing it from
reopening.
