# KeHE Distributors — Deduction & Dispute Research

Source: web research, 2026-05-07. Citations inline; verification gaps
listed at the end. Used as input to synthetic-data generation; do not
treat as legal or compliance authority.

## 1. Dispute submission systems

KeHE disputes are filed through **K-Solve**, a ticketing module inside the **KeHE CONNECT Supplier** portal at `connectsupplier.kehe.com` [source: https://connectsupplier.kehe.com/] [source: https://tryintercept.com/blog/kehe-disputes]. Brands gather the deduction code, reference, invoice, date, and amount from KeHE Connect, open a case in K-Solve, attach supporting files (POD/BOL, original PO and invoice, promo agreement or email approvals, ASN confirmations, label photos), and track status in-portal [source: https://tryintercept.com/blog/kehe-disputes].

## 2. Deadline windows

KeHE's terms have long carried a **180-day (6-month) dispute window**, historically loosely enforced. As of late 2025, KeHE began strictly enforcing it: the dispute option in K-Solve disappears entirely on deductions older than 6 months, with no override [source: https://www.tryglimpse.com/post/kehe-new-policy-oct2025] [source: https://www.spscommerce.com/community/articles/a-guide-to-disputing-kehe-deductions-in-k-solve]. Standard K-Solve resolution time is ~21 days [source: https://tryintercept.com/blog/kehe-disputes]. Shortage/UDR claims have a much tighter operational window — **about 48 hours to respond with proof (signed BOL, packing slip)** before the deduction is finalized [source: https://tryintercept.com/blog/kehe-deductions]. Could not verify separate published deadlines for slotting, freight, or promo.

## 3. Common deduction / MCB types

Documented codes [source: https://tryintercept.com/blog/kehe-deductions] [source: https://www.confidotech.com/resources/launching-into-kehe-deductions-and-cash-application]:

- **UDR** (Unloading Discrepancy) — shortage / overage / damage
- **MCB** — Manufacturer Chargeback for promo discounts to retailers
- **MCB Fee** — 8% admin fee on the MCB, **$65 minimum per DC**, processed bi-weekly
- **EP Fee** (Event Promotion) — 8% of invoice for scans/demos/slotting, **capped at $500**
- **Connect BI Fee** — flat 2% of sales for portal access
- **Freight** — typically $0.25–$0.40/lb when KeHE ships
- **2% 10 Net 30** — early payment discount
- **Introductory allowance** — minimum 15% off-invoice per new SKU per DC

Billback is the umbrella term; KeHE's MCB is a specific billback variant carrying the 8% admin surcharge [source: https://www.govividly.com/blog/deductions-management-tip-no-1-mcb].

## 4. Promo / MCB processes

Scan-downs come back from the retailer at point of sale with no markup; KeHE MCBs reflect distributor pass-through of a discounted buy and add the 8% admin fee plus per-DC minimums [source: https://tryintercept.com/blog/kehe-deductions] [source: https://www.govividly.com/blog/deductions-management-tip-no-1-mcb]. Promo disputes most often hinge on PO mismatches, missing promo agreements, and vague codes; K-Solve specifically requires "Promotional Agreement or Email Approvals" as backup [source: https://tryintercept.com/blog/kehe-disputes].

## 5. Post-audit / clawback behavior

KeHE conducts internal and third-party post-audits covering allowance compliance, product shortages, the 1.5% marketing allowance, and MCB accuracy. KeHE reserves the right to pass through retailer audit claims to the vendor **beyond the standard 2-year limitation** when a retailer deducts an audit claim from KeHE for the vendor's product [source: https://www.sec.gov/Archives/edgar/data/1670869/000166357718000308/ex10_31.htm]. K-Solve retains roughly 2 years of historical transaction detail [source: https://supplierwiki.supplypike.com/articles/a-guide-to-disputing-kehe-deductions-in-k-solve].

## 6. Known quirks / gotchas

The 48-hour UDR response window is by far the most punishing operational detail for a lean team — once it closes, the shortage is locked [source: https://tryintercept.com/blog/kehe-deductions]. The newly enforced 6-month dispute cliff means deduction backlogs older than that are now permanently dead, regardless of evidence [source: https://www.tryglimpse.com/post/kehe-new-policy-oct2025]. The **$65/DC MCB minimum** can stack quickly across KeHE's distribution network, turning small promotions into outsized fees. Intercept reports observed deduction loads of **25%–82% of invoice value** across KeHE brands, with one brand netting only $21,000 of a $32,000 invoice [source: https://tryintercept.com/blog/kehe-deductions]. Could not verify documented regional DC behavioral differences for KeHE.

## Verification gaps

- KeHE deadline windows for slotting, freight, and promo categories beyond the overarching 180-day cap and 48-hour UDR window.
- Regional DC differences for KeHE — referenced as a category in the prompt but not surfaced in any source reviewed.
- Exact effective date of KeHE's 6-month enforcement change (Glimpse article published March 2026 references it as "recent" without an implementation date).
- The KeHE SEC filing (2018 vendor agreement) describes terms in force at that time; current terms may have evolved.
