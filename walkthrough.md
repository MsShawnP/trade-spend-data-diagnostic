# Trade Spend Diagnostic — Walkthrough

Cinderhaven Provisions, a specialty food company with $29.9 million
in trailing-twelve-month wholesale revenue, budgets 16.7% of that
revenue for trade spend — the rate-card allowances negotiated with
retailers as a cost of shelf access. The actual all-in cost is 20.4%.
The 3.8-point gap represents $1.1 million in annual operational
waste: deductions taken by retailers beyond the negotiated trade
rate, flowing through in retailer-specific codes, weeks after the
transactions they reference, and largely uncontested.

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
Cinderhaven's numbers are representative of the pattern: a 16.7%
planned trade rate, a 20.4% actual all-in rate, and $1.1 million in
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
- **Deduction log** — 2,731 trailing-365-day deductions across 9
  retailers, each carrying a retailer-specific code, an amount, and
  a date. These are the raw material for the operational waste
  calculation.
- **Promotions calendar** — 138 planned promotions across four types
  (TPR, Feature, Display, BOGO), with planned costs and funding
  mechanisms.
- **POS scan data** — weekly point-of-sale records from 9
  retailers, used to measure promotional lift.
- **Dispute records** — 3,581 filed disputes with outcomes and
  recovery amounts.
- **Deduction code crosswalk** — 79 retailer-specific codes mapped
  to a common 8-category taxonomy. Fuzzy matching (via rapidfuzz)
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

Cinderhaven's structural trade rate is 16.7% of revenue — $4,972,381
on $29,854,750 in trailing-twelve-month wholesale sales. The all-in
trade cost, including operational deductions, is 20.4% —
$6,103,524. The difference is $1,131,144 in operational waste,
representing 3.8% of revenue (see Tab 1: Executive Pulse).

### Where the waste comes from

Eight deduction categories compose the operational waste, led by
three that account for the majority of the total (query:
`deductions/waste_by_category.sql`):

| Category | Count | Amount | Share |
|----------|------:|-------:|------:|
| Vague / unclassified | 283 | $405,698 | 35.9% |
| Label fines | 393 | $196,417 | 17.4% |
| Short-ship charges | 811 | $184,914 | 16.4% |
| Spoilage claims | 158 | $147,838 | 13.1% |
| Late delivery | 392 | $84,769 | 7.5% |
| Damaged goods | 95 | $54,109 | 4.8% |
| Slotting fees | 10 | $41,114 | 3.6% |
| Pallet fines | 93 | $16,284 | 1.4% |

The largest single category — vague deductions with missing or
ambiguous reason codes — is the least actionable. These are
deductions where the retailer's remittance provides no clear basis
for the charge. They are also the hardest to dispute: without a
specific claim to contest, the burden of proof shifts entirely to
the manufacturer. The prevalence of vague deductions is itself a
diagnostic finding (see Tab 2: Leak Diagnostic).

### Double-dip detection

Three deduction events totaling $18,795 were identified as
double-payments: the same promotion received both an off-invoice
discount on the original invoice and a subsequent promo-billback
deduction. The dollar amount is small. The finding is significant
because the matching infrastructure to detect double-dips — linking
deductions back to specific promotions by retailer, date window,
and amount — did not exist before this diagnostic was built (query:
`deductions/double_dip_events.sql`).

### Ghost promotions

405 promo-billback deductions totaling $245,441 reference promotions
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

Cinderhaven filed 3,581 disputes against retailer deductions,
recovering $295,872 — an 18.6% recovery rate by dollar value.
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
leads with the two-bucket punchline: 16.7% structural, 3.8%
operational, 20.4% all-in. Tabs 2 through 4 (Leak Diagnostic,
Promo Efficacy, Retailer Risk) provide the supporting detail with
adjustable inputs — a target recovery rate, a promo comparison
window, and per-retailer what-if trade rates. Tab 5 (Deduction
Ledger) is the full trailing-year data with auto-filters and freeze
panes. Tab 6 maps retailer codes to plain English. Tab 7 documents
every calculation. Color-coded: navy for analysis tabs, teal for
data, gray for reference.

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
covers 79 codes across 9 retailers. A production system would ingest
retailer EDI feeds directly, apply ML-based code classification for
new or ambiguous codes, and maintain the crosswalk continuously
rather than as a static lookup table.

**System integration.** The diagnostic works from exported flat
files. A live engagement would connect to the ERP (invoice and
shipment data), the deduction management system (if one exists),
and retailer portals (deduction feeds, POS data, compliance
reports). Integration surfaces double-dips and ghost promos in near
real-time, not after a year of accumulation.

**Dispute workflow automation.** The current 18.6% recovery rate
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
proving the gap exists. The value of the engagement is preventing
it from reopening.
