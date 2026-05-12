# Data Requirements — Trade Spend Diagnostic

What we need from you to run the diagnostic, and in what format.

---

## 1. Required Data

These five datasets are required. The diagnostic cannot run without them.

---

### A. Point-of-Sale / Scan Data

**What it is:** Weekly unit volumes and dollar sales, broken down by SKU and store (or retailer, if store-level isn't available).

**Fields we need:**

| Field | Example | Notes |
|-------|---------|-------|
| SKU or UPC | `CHP-0010`, `00-14527-00312` | Your internal SKU is fine. Needs to match your product master. |
| Store or account ID | `STR-00047`, `Walmart #1234` | If you only have retailer-level aggregates, that works — just flag it. |
| Week ending date | `2025-06-07` | Weekly granularity required. Daily data is fine; we'll roll it up. |
| Units sold | `312` | Total units for that SKU at that store in that week. |
| Dollars sold | `1,934.40` | Total retail or wholesale dollars. Gross, before returns. |

**Time window:** Trailing 12 months minimum. 18 months is better (gives us pre-period baselines for promotions that started early in the window).

**Where this typically lives:**
- **Walmart:** Retail Link > Decision Support > Item Performance, exported weekly
- **UNFI:** UNFI Insights portal, or ask your broker for weekly POS extracts
- **Costco:** Costco supplier portal, item movement report
- **Regional/natural channel:** Your broker (KeHE, UNFI, DPI) usually has this in their portal
- **DTC:** Your Shopify/ERP sales export

**Format:** CSV or Excel. One row per SKU per store per week.

---

### B. Product Master and Cost File

**What it is:** Your SKU list with what each item costs you to make, what you sell it for by channel, and your planned trade spend rate by channel.

**Fields we need:**

| Field | Example | Notes |
|-------|---------|-------|
| SKU | `CHP-0010` | Must match the SKU in your scan data. |
| Product name | `Smoked Maple Bacon Jerky 3oz` | For readability in the report. |
| Product line / category | `Jerky`, `Snack Bars` | How you group your products internally. |
| COGS per unit | `$2.85` | Your fully-loaded cost of goods. |
| Wholesale price by channel | Walmart: `$4.29`, UNFI: `$4.15`, DTC: `$7.99` | The price you invoice at. If you have a single blended wholesale, that works. |
| Trade spend rate by channel | Walmart: `18.5%`, Costco: `17.2%` | Your planned/contracted trade rate as a percentage of revenue. This is the rate you negotiated — not what you're actually spending (the diagnostic calculates that). |

**Where this typically lives:**
- COGS and wholesale: Your ERP (NetSuite, QuickBooks, SAP) or your pricing/finance team's master spreadsheet
- Trade spend rates: Your trade management system, or the rate cards your sales team negotiated with each retailer

**Format:** CSV or Excel. One row per SKU. If wholesale prices and trade rates vary by channel, we need a column per channel.

---

### C. Deduction Log

**What it is:** Every deduction taken by every retailer in the trailing 12 months. This is the core dataset — without it, there's no diagnostic.

**Fields we need:**

| Field | Example | Notes |
|-------|---------|-------|
| Deduction ID | `DED-0001234` | Your internal tracking number. |
| Retailer | `Walmart`, `UNFI`, `KeHE` | Which retailer took the deduction. |
| Deduction date | `2025-03-15` | The date the deduction appeared on the remittance or was posted. |
| Amount | `$1,247.50` | Dollar amount deducted. |
| Reason code (as remitted) | `70`, `DMG`, `SHR-001` | The code the retailer put on the remittance. These are retailer-specific and often cryptic — that's fine. |
| Remittance reference | `REM-WMT-00123` | The remittance or check number. Helps trace back to source. |

**Highly valuable if available (improves the diagnostic significantly):**

| Field | Example | Why it matters |
|-------|---------|----------------|
| Category / translated code | `Short Ship`, `Damaged`, `Slotting` | If you've already categorized deductions, it saves us a mapping step. If not, we'll map them from reason codes. |
| Order or shipment reference | `ORD-55234`, `SHIP-12901` | Links deductions to specific shipments for root-cause analysis. |
| Remittance description | `"Shorted 2 cases on PO 44721"` | Free-text descriptions often contain information the reason code doesn't. |
| Dispute deadline | `2025-06-15` | If your system tracks the window for filing a dispute. |

**Where this typically lives:**
- Your AR or deduction management system (HighRadius, Vistex, or even an Excel tracker)
- Raw remittance advice files from each retailer
- Your cash application system, if deductions are posted against invoices

**Format:** CSV or Excel. One row per deduction. Export everything — we handle the filtering.

---

### D. Promotion Calendar

**What it is:** Your planned and executed promotions — what ran, when, at which retailer, and what it was supposed to cost.

**Fields we need:**

| Field | Example | Notes |
|-------|---------|-------|
| Promo ID or reference | `PROMO-0042` | Your internal tracking number. |
| SKU | `CHP-0010` | Which product was promoted. |
| Retailer | `Whole Foods` | Where the promo ran. |
| Start date | `2025-02-03` | Week the promotion started. |
| End date | `2025-02-17` | Week the promotion ended. |
| Promotion type | `TPR`, `BOGO`, `Feature`, `Display`, `Demo` | The type of promotion. |
| Planned cost | `$2,400.00` | What you budgeted for this promotion. |
| Funding mechanism | `Off-invoice`, `Bill-back`, `Scan-back` | How the retailer gets paid. This matters because off-invoice discounts don't appear in the deduction log, while bill-backs do. |

**Nice to have:**

| Field | Example |
|-------|---------|
| Discount depth | `20%` |
| Duration in weeks | `2` |
| Store scope | `All stores`, `West region only` |

**Where this typically lives:**
- Your trade promotion management system (if you have one)
- More commonly: the sales team's spreadsheet or shared calendar
- Broker-managed promotions may be in your broker's system

**Format:** CSV or Excel. One row per promotion per SKU per retailer.

---

### E. Dispute Log

**What it is:** The record of disputes you've filed against deductions — what you contested, when, and what happened.

**Fields we need:**

| Field | Example | Notes |
|-------|---------|-------|
| Dispute ID | `DIS-0892` | Your internal tracking number. |
| Deduction ID | `DED-0001234` | Which deduction this dispute is for. Must match the deduction log. |
| Date filed | `2025-04-01` | When the dispute was submitted. |
| Date closed | `2025-05-12` | When the dispute was resolved. Blank if still open. |
| Outcome | `Won`, `Lost`, `Pending` | Current status. |
| Amount recovered | `$1,247.50` | Dollars recovered (may differ from deduction amount). |

**Valuable if available:**

| Field | Example |
|-------|---------|
| Filing method | `Portal`, `Email`, `Phone` |
| Evidence quality | `Strong`, `Moderate`, `Weak` |
| Labor hours | `1.5` |

**Where this typically lives:**
- Your AR team's dispute tracker
- Your deduction management system (HighRadius, etc.)
- Often an Excel workbook maintained by whoever files the disputes

**Format:** CSV or Excel. One row per dispute.

---

## 2. Optional but Valuable

These improve the diagnostic but aren't required.

**Store list.** A mapping of store IDs to retailer names, regions, and volume tiers. Required only if your POS data comes at the store level without a retailer column. If your scan data already has a retailer field, you don't need this.

**Retailer deduction code guides.** The vendor compliance guides from Walmart, UNFI, KeHE, Costco, etc. that define what each reason code means. These are usually PDFs the retailer provides during onboarding or posts on their supplier portal. We use these to verify our code-to-category mapping — if you don't have them, we'll infer the mapping from the codes themselves, but verified is better than inferred.

**Prior-year data.** Extending beyond 12 months lets us identify seasonal patterns and year-over-year trends. 24 months of scan data and deductions is ideal. The promotion calendar is most useful for the trailing 12 months only.

---

## 3. Common Data Quality Issues We Handle

You don't need to clean the data before sending it. The diagnostic is designed to deal with real-world messiness, including:

**Inconsistent retailer naming.** "WFM" in your deduction log, "Whole Foods" in your scan data, "WHOLEFOODS" in your promotion calendar. We normalize all of these.

**Missing or vague reason codes.** Retailer remittances often use internal codes (`70`, `MISC`, `ADJ`) with no explanation. We map known codes to plain-English categories and flag the ones that can't be mapped as "vague" — quantifying vague deductions is part of the diagnostic's value.

**Date format mismatches.** Your ERP exports dates as `MM/DD/YYYY`, your broker uses `YYYY-MM-DD`, and Walmart uses fiscal week numbers. We handle the conversions.

**Deduction timing differences across retailers.** Walmart typically deducts 30–60 days after shipment. UNFI deducts at source (on the same remittance as payment). Costco may batch deductions monthly. The diagnostic accounts for these timing patterns when matching deductions to promotions and shipments.

**Off-invoice discounts missing from the deduction log.** If a promotion is funded off-invoice (the discount is taken on the original invoice), there's no deduction to match against. The diagnostic uses the funding mechanism field from your promotion calendar to handle this correctly — off-invoice promotions are counted as structural trade spend, not operational deductions.

**Promotions tracked in spreadsheets with inconsistent formatting.** Merged cells, color-coded status columns, notes in random cells. As long as we can identify the SKU, retailer, date range, and cost, we can work with it.

**Duplicate or overlapping records.** Deductions that appear twice (once on the remittance, once in a post-audit claim), or promotions entered with overlapping date ranges. We detect and flag these rather than double-counting.

---

## 4. What We Don't Need

**Raw EDI files.** We work with the processed output — the POS data, deduction details, and promotion records that your systems have already parsed from EDI.

**Access to your systems.** You export the data, we ingest it. We don't need logins to Retail Link, your ERP, or your deduction management system.

**Clean data.** Seriously. Messy exports with extra columns, inconsistent formatting, and blank rows are fine. The diagnostic handles the cleaning — identifying what's messy is part of the value.

**Chart of accounts or GL detail.** We work from the operational data (POS, deductions, promotions), not from your general ledger.

**Broker agreements or retailer contracts.** We don't need the legal documents. The trade spend rates in your cost file tell us what we need about your contracted terms.

---

## Checklist

Before our kickoff, confirm you can pull:

- [ ] **Scan data** — 12+ months, weekly, by SKU and store/retailer
- [ ] **Product master** — SKU list with COGS, wholesale prices, trade rates by channel
- [ ] **Deduction log** — every deduction, trailing 12 months, with reason codes
- [ ] **Promotion calendar** — planned promos with SKU, retailer, dates, cost, funding type
- [ ] **Dispute log** — disputes filed with outcomes and amounts recovered

If any of these don't exist or are incomplete, let us know — that's useful information in itself, and we can scope the diagnostic accordingly.
