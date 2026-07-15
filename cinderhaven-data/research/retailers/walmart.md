# Walmart — Deduction & Dispute Research

Source: web research, 2026-05-07. Citations inline; verification gaps
listed at the end. Used as input to synthetic-data generation; do not
treat as legal or compliance authority.

## 1. Dispute submission system(s)

Walmart suppliers file disputes through several distinct systems. Which one applies depends on what kind of deduction it is.

- **Retail Link** is Walmart's primary supplier platform (operational data, item setup, POs). It is the gateway/SSO for the dispute apps below. URL: `https://retaillink.wal-mart.com/` [source: https://retaillink.wal-mart.com/]
- **Accounts Payable Disputes Portal (APDP)** is an app inside Retail Link, launched in 2021, which replaced the previous third-party DCI (Direct Commerce, Inc.) system. It handles AP deductions for Goods-For-Resale (GFR) suppliers — shortages, allowances, pricing differences. Accessed with Retail Link credentials. [source: https://www.8thandwalton.com/blog/walmart-dispute-portal/] [source: https://supplierwiki.supplypike.com/articles/walmarts-new-accounts-payable-disputes-portal-apdp]
- **HighRadius** is a separate self-service portal for Accounts Receivable deductions, including grocery billback allowances (Code 69) and OTIF chargebacks. New-user setup is requested by emailing `HiRadCS@walmart.com`. [source: https://www.8thandwalton.com/blog/walmart-dispute-portal/] [source: https://www.spscommerce.com/community/articles/how-to-dispute-walmart-otif-chargebacks]
- **Supplier One** launched in early 2024 as a unified platform extending Retail Link into financial workflows (including deduction tracking). Item 360 workflows redirected to Supplier One in September 2024, but Retail Link remains the primary platform; Supplier One has not replaced it. URL: `https://supplierone.wal-mart.com` [source: https://supplierwiki.supplypike.com/articles/what-is-walmarts-supplierone]

Submission method is portal-based in all cases (no email-only or EDI dispute path verified).

## 2. Deadline windows

- **Shortage deductions (codes 21–28):** must be disputed within **12 months**. [source: https://supplierwiki.supplypike.com/articles/walmarts-apdp-a-clear-guide-to-the-accounts-payable-dispute-portal]
- **Allowance deductions:** disputable for up to **24 months**. [source: https://supplierwiki.supplypike.com/articles/walmarts-apdp-a-clear-guide-to-the-accounts-payable-dispute-portal]
- **Supplier-Action response window:** when Walmart's Dispute Analyst comments back, the supplier has **7 days** to respond, or the case is auto-closed/denied. [source: https://www.spscommerce.com/community/articles/walmarts-apdp-a-clear-guide-to-the-accounts-payable-dispute-portal]
- **Draft disputes** auto-expire after **14 days** if not submitted. [source: https://www.spscommerce.com/community/articles/walmarts-apdp-a-clear-guide-to-the-accounts-payable-dispute-portal]
- **Date range per dispute:** APDP only allows selecting a **10-day or shorter** date range when creating a dispute, forcing batching. [source: https://supplierwiki.supplypike.com/articles/walmarts-apdp-a-clear-guide-to-the-accounts-payable-dispute-portal]
- **Post-audit claims:** Walmart cannot bring claims more than **2 years** after the audited calendar year. For claims **$500–$100,000**, Walmart auto-deducts and sends the claim packet; for claims **over $100,000.01**, the supplier has **15 days** to respond before the deduction is taken. [source: https://supplierwiki.supplypike.com/articles/what-is-a-post-audit-claim]

OTIF dispute deadline could not be verified from primary sources (see Verification gaps).

## 3. Common deduction / chargeback codes

From Walmart's published code list (compiled by iNymbus, cross-referenced with 8thandWalton and SupplyPike):

| Code | Name | What it represents |
|---|---|---|
| 11 | Price Difference Between PO & Invoice | PO cost vs. invoiced cost mismatch |
| 13 | Substitution Overcharge | Different item received, lower cost than billed |
| 21 | Concealed Shortage | Missing items found after delivery (inner pack, partial pallet) |
| 22 | Merchandise Billed Not Shipped | Receiving says fewer cases arrived than invoiced |
| 24 | Carton Shortage / Freight Bill Signed Short | BOL shows shortage at receipt |
| 25 | No Merchandise Received for Invoice | Walmart claims nothing was received against the invoice |
| 28 | Carton Damage – Freight Bill Signed Damaged | Damage noted at receiving |
| 30 | Duplicate Billing | Two invoices for one PO |
| 51 | Promotional Allowance | Promo/display/fixture allowance |
| 59 | Defective Merchandise Allowance | Allowance for unsaleable goods |
| 87 | Other | Catch-all when no other code fits |
| 99 | OTIF | On-Time In-Full violation |

[source: https://blog.inymbus.com/walmart-deduction-codes-explained-inymbus] [source: https://www.8thandwalton.com/blog/walmart-deduction-codes/]

## 4. OTIF specifics

- **Penalty rate:** **3% of COGS** on non-compliant cases, billed via AR. [source: https://vendormint.com/walmart-on-time-in-full-otif-compliance/]
- **Thresholds (current public reporting):**
  - Prepaid suppliers: **90%** on-time at the DC delivery window
  - Collect suppliers: **98%** on-time
  - In-Full: **95%**
  [source: https://vendormint.com/walmart-on-time-in-full-otif-compliance/]
- **Historical change:** Walmart tightened OTIF from 85% to 87% for full-truckload deliveries within a two-day window and announced splitting OTIF into separate on-time and in-full metrics. [source: https://www.supplychaindive.com/news/walmart-on-time-in-full-87-suppliers/550083/]
- **Billing cadence:** As of 2024, Walmart evaluates monthly but releases fines **quarterly**. [source: https://vendormint.com/walmart-on-time-in-full-otif-compliance/]
- **Disputes:** filed through HighRadius via the EIPP (Open or Closed Bills tab). Up to 10 attachments per dispute. Valid reasons include ASN/DSS discrepancies, Walmart receiving errors, and force majeure. [source: https://www.spscommerce.com/community/articles/how-to-dispute-walmart-otif-chargebacks]

## 5. Post-audit / clawback behavior

- **Auditor:** For fiscal 2025 (starting Feb 1, 2025), Walmart consolidated to a **single third-party auditor — Audit Partners Limited (APL)**, a UK firm. Previously: Apex Analytix, Cotiviti/Connolly, PRGX, and Auditec. [source: https://talkbusiness.net/2025/02/the-supply-side-walmart-making-changes-in-system-that-audits-supplier-payments/]
- **Lookback period:** up to **2 years** after the audited calendar year. [source: https://supplierwiki.supplypike.com/articles/what-is-a-post-audit-claim]
- **Typical claim types:** retroactive pricing errors, missed allowances, freight charges, logistics discrepancies. [source: https://supplierwiki.supplypike.com/articles/what-is-a-post-audit-claim]
- **Auto-deduction threshold:** $500–$100,000 auto-deducted with packet emailed; >$100,000.01 supplier gets 15-day notice. [source: https://supplierwiki.supplypike.com/articles/what-is-a-post-audit-claim]

## 6. Known quirks / gotchas

- **APDP requires multiple disputes for a long deduction span** — the date-range selector caps at 10 days, so a supplier with a 90-day backlog files 9+ separate disputes. [source: https://supplierwiki.supplypike.com/articles/walmarts-apdp-a-clear-guide-to-the-accounts-payable-dispute-portal]
- **APDP and HighRadius are separate worlds** — APDP handles AP deductions, HighRadius handles AR (including OTIF and grocery billbacks). Suppliers must identify the originating system before filing. [source: https://www.8thandwalton.com/blog/walmart-dispute-portal/]
- **Auto-close on inaction:** 7-day Supplier Action window; missing it cancels the dispute. [source: https://supplierwiki.supplypike.com/articles/walmarts-apdp-a-clear-guide-to-the-accounts-payable-dispute-portal]
- **SQEP fines layer on top of code-based deductions.** Phase 1 (PO/ASN accuracy): $200 + $1/case for general defects; **$25 per PO when ASNs are not downloaded** (non-DSDC), $200/PO for DSDC and Dept 38. Phase 2 (barcode/label): **$200 admin + $1/case when manually inspected; $1/case alone when caught by automated scanners**. Phase 3 (pallet/load): **$200 admin + $4/pallet** (pallet defects) or **$200 admin + $20/load** (load defects). [source: https://supplierwiki.supplypike.com/articles/calculating-sqep-fines-by-defect]
- **Code 25 ("No merchandise received") is often a timing artifact** — invoice transmits before the shipment is received and matched, so the supplier appears to bill for a phantom shipment. [source: https://www.8thandwalton.com/blog/walmart-deduction-codes/]
- **Code 22 is the canonical "perceived shortage"** — receiving counts fewer cases than invoiced; non-scannable case labels make this much worse because cases are hand-counted. [source: https://www.8thandwalton.com/blog/walmart-deduction-codes/]
- **OTIF moved from monthly to quarterly billing (2024).** This obscures the cause-effect link between a specific late shipment and a fine that hits 60–90 days later. [source: https://vendormint.com/walmart-on-time-in-full-otif-compliance/]
- **Code 87 ("Other")** is a real, documented catch-all category — vague deductions are not just sloppy retailer behavior, they have an official code. [source: https://blog.inymbus.com/walmart-deduction-codes-explained-inymbus]

## Verification gaps

- **APDP filing windows (12 mo shortage / 24 mo allowance):** stated by SupplierWiki/SupplyPike, but I could not find the same figures restated in Walmart's own documentation, the iNymbus guide, or the HRG audit guide. They may be accurate but should be treated as "industry-cited" rather than primary-source confirmed.
- **OTIF dispute deadline:** explicitly not stated in the SupplyPike OTIF dispute article. Could not verify.
- **Current SQEP phase count:** sources reference Phases 1–3 with dollar amounts; a Phase 4 has been mentioned in industry coverage but I did not confirm it is live as of May 2026 or pull verified fine amounts for it.
- **Walmart's official deduction code master list (full document):** referenced as a downloadable PDF on multiple supplier-blog sites but I did not retrieve a primary-source PDF directly from Walmart. Code names above are consistent across iNymbus and 8thandWalton but are not from Walmart's own portal.
- **Whether Supplier One has absorbed APDP/HighRadius dispute workflows in 2025–2026:** sources from 2024 say it had not yet replaced Retail Link or those portals. I did not find a 2025–2026 update confirming the current state.
- **Walmart's exact thresholds for OTIF in May 2026:** the 90/98/95 split and the 87% full-truckload figure come from articles dated 2023–2024. Current 2026 thresholds may have moved; treat as approximate.
