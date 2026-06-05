# Defensibility Log

Every deduction in this diagnostic is classified into one of three
taxonomy buckets. This document defines the rules and provides the
rebuttal for each classification — the answer to "your consultant
doesn't understand our business, that's just how it works."

## The classification principle

A deduction is **operational waste** if Cinderhaven did not plan for
it, did not budget for it, and could reduce or eliminate it through
process improvement or dispute. A deduction is **contractual** if it
reflects a negotiated term Cinderhaven agreed to in advance. A
deduction is **unknown** if the retailer's remittance provides
insufficient information to classify it — which is itself a finding.

---

## Bucket 1: Probable Waste (addressable)

These are operational failures, compliance gaps, or logistics
breakdowns. They are not standard fees. They are not negotiated
terms. They are cash leaving the building because something broke.

### Spoilage (~$153K, ~728 deductions)

**Taxonomy:** Probable Waste — addressable.

**Defense:** Audit against shelf-life data and retailer handling
procedures.

**Rebuttal to "spoilage is normal for perishables":** Some spoilage
is expected. ~$153K in charges should be cross-referenced against
actual shelf-life dates and retailer handling — was the product
within code at delivery? Did the retailer's distribution center
hold it past the sell-by window? Spoilage deductions where the
product was delivered within spec are disputable.

### Label Fine (~$106K, ~322 deductions)

**Taxonomy:** Probable Waste — addressable.

**Defense:** Labeling compliance failures. Fixable with updated
processes.

**Rebuttal to "every manufacturer gets label fines":** At ~$106K/year,
this is not a rounding error. Retailer labeling specifications are
published. Compliance is a process problem — wrong UPC placement,
missing nutrition panel updates, incorrect case-pack markings — not a
cost of doing business. The fix is a pre-ship QC checklist.

### Short Ship (~$96K, ~756 deductions)

**Taxonomy:** Probable Waste — addressable.

**Defense:** Verify against bill of lading and shipping records.
Many are rebuttable.

**Rebuttal to "that's just warehouse shrink":** If the BOL shows
full shipment and the retailer's receiving dock recorded a shortage,
someone between the dock doors is at fault — possibly the carrier,
possibly the retailer's receiving process. Either way, it is
disputable. If the warehouse genuinely shorted the order, Operations
owns the root cause and can fix it.

### Damaged Goods (~$96K, ~734 deductions)

**Taxonomy:** Probable Waste — addressable.

**Defense:** Audit damage claims against packaging specs and carrier
handling.

**Rebuttal to "stuff breaks in transit":** Damage claims should be
matched against packaging specifications. If the product was packed
to spec and the carrier mishandled it, the manufacturer has a claim
against the carrier. Recurring damage patterns point to packaging
design issues — fixable.

### Pallet Fine (~$45K, ~252 deductions)

**Taxonomy:** Probable Waste — addressable.

**Defense:** Compliance failure. Fixable with warehouse process
changes.

**Rebuttal to "retailers nitpick pallet specs":** Pallet
specifications (height, weight, wrap, labeling, stacking pattern)
are published in retailer vendor guides. Compliance is a warehouse
SOP issue. At ~$45K it is a mid-tier category, but the fix
(training, checklists) is also the cheapest.

### Late Delivery (~$31K, ~607 deductions)

**Taxonomy:** Probable Waste — addressable.

**Defense:** Track against carrier SLAs. Some are carrier fault, not
manufacturer.

**Rebuttal to "carriers are unreliable, can't control it":** If the
carrier missed the SLA, the manufacturer has a freight claim against
the carrier. If Cinderhaven released the shipment late, the root
cause is internal and fixable. Either way, the deduction should not
be silently absorbed.

### Pricing Error (~$6K, ~157 deductions)

**Taxonomy:** Probable Waste — addressable.

**Defense:** Invoice/price discrepancies. Cross-reference against
current price lists and contract terms.

**Rebuttal to "pricing errors are trivial":** The dollar amount is
small; the signal is not. Frequent pricing errors indicate a gap
between the price list the sales team negotiated and what the
invoicing system bills. Fix the master data, and the errors stop.

---

## Bucket 2: Unknown (addressable)

### Vague / Unclassified (~$417K, ~318 deductions)

**Taxonomy:** Unknown — addressable.

**Defense:** No clear basis for the charge. Highest priority for
investigation and dispute.

**Why this is the hero finding:** Vague deductions are the largest
single category at $417K — 43% of the entire operational waste
bucket. Of 318 vague deductions in the trailing year, 106 (33%)
lack even a PO reference, making them untraceable to a specific
order. These are not relabeled spoilage or damaged claims; they
are deductions where the retailer's remittance provides genuinely
vague descriptions ("Audit adjustment," "Misc deduction — see
invoice," "Compliance fee") with no supporting documentation.

**Rebuttal to "those are just miscellaneous fees":** "Miscellaneous"
is not a contractual term. Request supporting documentation from the
retailer — a referenced invoice, a specific compliance failure, a
documented shortage. Deductions without a specific, documented basis
are disputable: the absence of clear justification is itself the
dispute grounds. This is the highest-priority category for
investigation because the ~$417K represents the largest single
category of operational waste and the least understood.

---

## Bucket 3: Contractual (non-addressable)

### Slotting (~$28K, ~6 deductions)

**Taxonomy:** Contractual — not addressable in this diagnostic.

**Defense:** Negotiated shelf-access fee. Verify against contract
terms.

**Why it's not waste:** Slotting fees are agreed upon during the
sales negotiation. They are a known cost of gaining or maintaining
shelf placement. The diagnostic classifies them as contractual
because reducing them requires renegotiating the retailer
relationship, not fixing an operational failure. However: verify
that the amounts match the contract. Discrepancies between the
agreed slotting fee and the actual deduction are disputable.

### Promo Billback (excluded from waste bucket)

**Taxonomy:** Contractual — excluded from operational waste.

**Defense:** Authorized promotional activity. Verify against promo
calendar.

**Why it's excluded:** Promo billbacks are planned promotional
spend funded through deductions. They appear on the Deduction
Ledger for completeness but do not inflate the operational waste
figure. The relevant question for billbacks is not "should this
exist?" but "does it match a planned promotion?" — see the ghost
promo analysis on Tab 3 (3,258 ghost promos, $361K).

---

## The addressable total

Of ~$977K in trailing-365 operational waste:

- **~$949K is addressable** (Probable Waste + Unknown buckets) —
  deductions that can be reduced through operational improvement,
  process fixes, or active dispute.
- **~$28K is contractual** (slotting) — a negotiated term, not an
  operational failure.

The $949K addressable figure is the number that matters for
remediation planning. At Cinderhaven's current 20.9% recovery rate,
~$232K is being recovered. At a 30% recovery rate (achievable with
automated dispute workflows), recovery would increase meaningfully
on the addressable portion.
