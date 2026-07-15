# Costco — Deduction & Dispute Research

Source: web research, 2026-05-07. Citations inline; verification gaps
listed at the end. Used as input to synthetic-data generation; do not
treat as legal or compliance authority.

## 1. Dispute submission system(s)

Costco operates a **Vendor Accounting Portal** (commonly called the "Costco Vendor Portal") for invoice tracking, deduction visibility, and dispute submission. The system is portal-based: suppliers locate the deducted invoice on the Payments Tab and click a paper-icon to start a claim, or use the Claims Tab and the green plus icon to create a new claim. There is no email-based dispute path described in published guidance, though disputes ultimately must be filed on a "Costco Standard Supplier Claim Form" per Costco's Basic Supplier Agreement [source: https://blog.inymbus.com/costco-vendor-portal-automate-disputing-costco-chargebacks].

Costco uses SPS Commerce as its primary EDI VAN partner for trading-document exchange (POs, ASNs, invoices), but EDI is not the dispute channel — it is the order/shipment channel [source: https://www.orderease.com/community/the-2025-guide-to-costco-edi-compliance-automation-chargeback-prevention]. Vendor authentication occurs through `fssts.costco.com` for password/identity management [source: https://fssts.costco.com/PM/CreatePassword.aspx]. Notably, Costco "buyers identify and contact vendors directly — there is no standard supplier portal or unsolicited application process" for becoming a vendor; the accounting portal is provisioned post-onboarding [source: https://getproductiv.com/costco-vendor-compliance]. Compared to Walmart's Retail Link / APDP / High Radius stack, Costco's tooling is lighter-weight and more manual.

## 2. Deadline windows

**Could not verify** specific dispute deadline windows by deduction type (shortage, compliance, late delivery, defective). Public sources reference Costco's "Standard Supplier Claim Form" requirement and a six-month window for invoice submission to Costco, but do not publish per-deduction-type dispute deadlines [source: https://www.sec.gov/Archives/edgar/data/1940372/000149315222028154/ex10-6.htm via search summary]. Industry commentary notes that "unresolved chargebacks can quickly pile up... increasing the risk of missing dispute deadlines," confirming deadlines exist but not the values [source: https://blog.inymbus.com/costco-vendor-portal-automate-disputing-costco-chargebacks].

## 3. Common deduction / chargeback codes

Costco's specific numeric code list is not publicly documented (unlike Walmart's Code 22 / Code 25 etc.). Verified deduction *categories* and approximate amounts:

- Late or missing ASN: ~$50–$200 per incident [source: https://www.orderease.com/community/the-2025-guide-to-costco-edi-compliance-automation-chargeback-prevention]
- PO/ASN/invoice data mismatch: ~1–3% of PO value [source: https://www.orderease.com/community/the-2025-guide-to-costco-edi-compliance-automation-chargeback-prevention]
- Incorrect GS1-128 / SSCC labeling: $50–$150 per carton (one source cites $5–$10/carton) [source: https://www.orderease.com/community/the-2025-guide-to-costco-edi-compliance-automation-chargeback-prevention]
- Non-compliant packaging: 2% chargeback to cover Costco's handling cost [source: https://www.clubstorepackaging.com/post/costco-packaging-specifications-requirements]
- Pallet configuration (lean, overhang, underhang), quantity discrepancy, packaging/product damage, late/refused delivery [source: https://getproductiv.com/costco-vendor-compliance]

**Could not verify** specific code numbers — chargebacks are "assessed individually rather than as a standardized percentage" [source: https://blog.inymbus.com/costco-vendor-portal-automate-disputing-costco-chargebacks].

## 4. On-time / in-full requirements

Costco operates a cross-dock depot model — product moves from inbound dock to club floor in 24–48 hours [source: https://getproductiv.com/costco-vendor-compliance]. Delivery requires a **scheduled appointment window** (not a range). A **30-minute grace period** after appointment time is typical; beyond 30 minutes without a phone call, deliveries are commonly refused [source: https://www.chep.com/files/download/costco-delivery-driver-guidelines-kemps-creek-depot-july-21.pdf]. Early arrivals are also rejected if depots aren't prepared. Costco does **not publish a numeric OTIF percentage threshold** like Walmart's 98% — penalties are case-by-case, plus reduced future order allocations for repeat offenders [source: https://getproductiv.com/costco-vendor-compliance].

## 5. Post-audit / clawback behavior

Costco's Basic Supplier Agreement contains a "Post Payment Audit" provision. Industry summaries cite a **three-year lookback** from a transaction or contract program completion, with Costco reserving the right to extend beyond three years if noncompliance is found [source: https://contracts.justia.com/companies/sondors-inc-15357/contract/256184/ via search summary]. **Could not verify** which third-party audit firms Costco engages (PRGX, Connolly/Cotiviti, etc.) — no public source confirms a specific auditor relationship for Costco.

## 6. Known quirks / gotchas

- **Depot cross-dock**: Goods are not stored. Late inbound = cascading club delays = swift chargebacks [source: https://getproductiv.com/costco-vendor-compliance].
- **Pallet specs**: 48"×40" max footprint (47"×39" recommended); 58" max height including pallet; iGPS / PECO / CHEP US BLOCK only; **GMA #1 stringer pallets are not accepted** [source: https://www.clubstorepackaging.com/post/costco-packaging-specifications-requirements].
- **Bottom-layer crush rating**: 1,500 lbs for loads <750 lbs; 2,500 lbs for loads ≥750 lbs [source: https://www.clubstorepackaging.com/post/costco-packaging-specifications-requirements].
- **Shipper label content**: SSCC, vendor number, PO number, item info, quantity, weight, destination — placed on two adjacent sides [source: https://getproductiv.com/costco-vendor-compliance].
- **50 lb max** carton weight if hand-lifted [source: https://www.clubstorepackaging.com/post/costco-packaging-specifications-requirements].
- **Returns / damage**: Costco "reserves the right to return such products to the supplier or to salvage, donate, dispose of, re-use, refurbish or recycle such products at the supplier's sole cost and expense" — this is the supplier-deduction mechanism behind member returns [source: https://www.tastingtable.com/1822350/what-happens-returned-costco-items/].
- **Lower-tech than Walmart**: portal-based but no equivalent of Retail Link's depth or APDP's automation [source: https://blog.inymbus.com/costco-vendor-portal-automate-disputing-costco-chargebacks].

## Verification gaps

- Specific numeric dispute-deadline windows by deduction type (shortage, compliance, late, defective) — not published.
- A canonical Costco chargeback code list with code numbers — not publicly available.
- Whether MVCR is a real Costco term — could not find any primary or secondary source using "MVCR" or "Member Value & Costco Return." This term may be a misremembered acronym.
- Whether "CRP" (Costco Return Policy) is a vendor-deduction code or just the consumer-facing return policy — only consumer-facing usage was found.
- Specific third-party auditors Costco uses (PRGX, Connolly/Cotiviti, etc.) — unconfirmed.
- The exact text of the post-payment audit clause (three-year window) — sourced only via secondary summary; the primary SEC filing (ex10-6) returned 403 to direct fetch.
- Whether disputes can be filed via email / fax as a fallback — not confirmed in published sources.
- Costco's published OTIF compliance percentage (if any exists internally) — none found public.
