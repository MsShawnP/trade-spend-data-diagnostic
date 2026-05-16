# Prose & Narrative Review

Reviewed: 2026-05-15

## Audience

Two audiences per PROJECT_PLAN.md:

1. **Prospect CPG CEO** — non-technical, cares about dollars and actions, wants the finding in 10 seconds, will forward the memo to their VP of Sales. Reads EXECUTIVE_MEMO.md first, opens the workbook second, may never read the walkthrough.
2. **Portfolio viewer** — evaluating the analyst's capability, reads README first, scans the walkthrough for methodology rigor, may open the workbook to verify claims.

## Summary

The narrative layer is strong where it matters most — the punchline lands in every document, the numbers are specific, and the CEO-facing memo is genuinely actionable. Two BLOCKING issues: the recovery rate contradicts itself across documents (walkthrough says 13.7%, memo and defensibility say 14.3%), and the vague deduction category gets contradictory advice (walkthrough says it's "the hardest to dispute" while the memo and defensibility log say the retailer bears the burden). Several advisory items around stale numbers, a phantom rapidfuzz reference, and a "chart" that's actually text.

## Findings

### [BLOCKING] P1: Recovery rate contradicts itself across deliverables

- **Location:** `walkthrough.md` section 3 ("Dispute recovery") vs. `EXECUTIVE_MEMO.md` ("What you are recovering") vs. `DEFENSIBILITY.md` ("The addressable total") vs. Methodology tab section 5
- **Issue:** Four documents, two different numbers:
  - Walkthrough: "a **13.7%** recovery rate... **1,410** disputes... **$716,082**"
  - Executive memo: "**1,409** disputes... a **14.3%** recovery rate"
  - Defensibility log: "current **14.3%** recovery rate"
  - Methodology tab: "$98,216 ÷ **$687,210** = **14.3%**"
  
  The walkthrough appears to have been updated with current DB numbers (13.7% is correct per the current database). The other three documents retain stale numbers from a prior build.
- **Audience impact:** A CEO who reads the memo (14.3%) and then the walkthrough (13.7%) sees an inconsistency that undermines trust. A VP of Sales looking for ammunition will find it immediately.
- **Suggested fix:** Pick one number, apply it everywhere. Per the current DB: 13.7% (all-time) or 11.7% (trailing-365, methodologically consistent with the waste bucket). Update the memo, defensibility log, and methodology tab to match.

### [BLOCKING] P2: Contradictory framing of vague deductions — "hardest to dispute" vs. "retailer bears the burden"

- **Location:** `walkthrough.md` section 3 ("Where the waste comes from") vs. `EXECUTIVE_MEMO.md` (Monday morning action #1) vs. `DEFENSIBILITY.md` (Bucket 2: Unknown)
- **Issue:** Three documents make incompatible claims about who bears the burden of proof for the $294K vague deduction category:
  - Walkthrough: "the least actionable... the hardest to dispute: without a specific claim to contest, **the burden of proof shifts entirely to the manufacturer**"
  - Executive memo: "Deductions without specific justification **have no contractual standing**" (implying they should be easy to dispute)
  - Defensibility log: "**the retailer bears the burden of justification**"
  
  The walkthrough says the manufacturer must prove the charge is wrong. The defensibility log says the retailer must prove the charge is right. The memo says the charge has no standing at all. These are three different legal positions on the same $294K.
- **Audience impact:** This is the #1 Monday-morning action — the single largest dollar category. If the CEO walks this to their VP of Sales and the VP asks "who actually bears the burden here?", the deliverables give three different answers. This is the exact VP-of-Sales rebuttal scenario the defensibility log was designed to prevent.
- **Suggested fix:** Decide on a position and apply it consistently. The defensible framing: "Vague deductions lack a specific contractual basis. Request supporting documentation from each retailer. Deductions the retailer cannot substantiate should be disputed — the absence of a clear basis is the dispute grounds." This avoids claiming either party bears a legal burden (which depends on contract terms the diagnostic doesn't have).

### [ADVISORY] P3: README and walkthrough claim rapidfuzz is part of the stack — it's not used in shipped code

- **Location:** `README.md` ("Stack" section), `walkthrough.md` section 2 ("Deduction code crosswalk"), `requirements.txt`
- **Issue:** README lists "rapidfuzz" as part of the stack. Walkthrough says "Fuzzy matching (via rapidfuzz) handles naming inconsistencies across retailers." Neither statement is true of the shipped code — no file in the project imports rapidfuzz. The crosswalk code (`tab_code_crosswalk.py`) runs a SQL query against the `deduction_codes` table; there is no fuzzy matching logic. Rapidfuzz may have been used in the upstream `cinderhaven-data` pipeline, but the walkthrough attributes it to this diagnostic.
- **Audience impact:** A portfolio viewer reading the walkthrough expects to find a fuzzy matching implementation. They won't. A reviewer checking `requirements.txt` will install a dependency that's never called.
- **Suggested fix:** Remove rapidfuzz from `requirements.txt` and README stack line. In the walkthrough, either remove the fuzzy matching claim or clarify: "The upstream data pipeline used fuzzy matching to build the crosswalk table; this diagnostic consumes the result."

### [ADVISORY] P4: README lists pandas in the stack — it's not imported in any shipped code

- **Location:** `README.md` ("Stack" section), `requirements.txt`
- **Issue:** Same as P3 but for pandas. No shipped code file imports pandas.
- **Suggested fix:** Remove from both files, or add a comment that it's needed for dev/ scripts only.

### [ADVISORY] P5: Walkthrough says "12-month waste trend chart" — it's a text indicator, not a chart

- **Location:** `walkthrough.md` section 4 ("The deliverables"): "A 12-month waste trend chart shows whether the problem is stable or accelerating."
- **Issue:** The openpyxl chart was abandoned after 3 failed rendering attempts (documented in FAILURES.md). The replacement is a text-based trend indicator in merged cells F16:G19. The walkthrough still calls it a "chart."
- **Audience impact:** A reader who opens the workbook expecting a chart will see text. Minor, but the discrepancy is noticeable.
- **Suggested fix:** Change "chart" to "trend indicator" or "trend summary."

### [ADVISORY] P6: Walkthrough claims 601,341 POS records — misleading scope

- **Location:** `walkthrough.md` section 2 ("Data sources"): "POS scan data — 601,341 weekly point-of-sale records from 11 retailers"
- **Issue:** 601,341 is the trailing-52-week subset of scan_data. The full table has 1,118,009 rows (104 weeks). The promo ROI analysis uses scan data going back further than 52 weeks (pre-period baselines for early promotions), so the 601,341 count understates the data actually consumed. The walkthrough presents this as the total without noting the scope.
- **Suggested fix:** Either "1,118,009 scan records spanning 104 weeks (revenue uses trailing 52; promo analysis uses the full history)" or "601,341 trailing-52-week records used for revenue calculation."

### [ADVISORY] P7: Walkthrough says promo window range is "1 to 8 weeks" — Tab 3 allows 1 to 12

- **Location:** `walkthrough.md` section 2 ("Promotion measurement"): "adjustable from 1 to 8 weeks; default 4"
- **Issue:** The Tab 3 data validation allows 1 to 12, and the hidden helper columns support up to 12 weeks (`_MAX_WINDOW = 12`). The walkthrough documents the wrong upper bound.
- **Suggested fix:** Change "1 to 8" to "1 to 12."

### [ADVISORY] P8: Methodology tab hardcodes dispute count and promo billback amount from prior DB build

- **Location:** `workbook/tab_methodology.py` — "1,409 dispute records" (line ~112), "$211,513" promo billback (line ~81)
- **Issue:** Current DB has 1,410 disputes and $213,017 in promo billback (trailing-365). The differences are small (known DB rebuild variance) but the methodology tab presents specific counts as facts. Both are stale.
- **Suggested fix:** Either derive these counts at build time (pass them from the query functions) or use approximate language ("~1,400 dispute records").

### [ADVISORY] P9: Instructional callout could orient the CEO faster

- **Location:** `tab_executive_pulse.py` — callout row near bottom of Tab 1
- **Issue:** The callout text reads: "This workbook summarizes trailing-12-month trade spend for Cinderhaven Provisions. Green tabs are analysis. Blue tab is the full deduction ledger. Gray tabs are reference. Yellow cells are adjustable inputs." This is useful orientation, but it's at the bottom of Tab 1, below the navigation links. A CEO scanning Tab 1 top-to-bottom hits the KPIs, the waterfall, the responsibility matrix, the navigation links, THEN the orientation. By that point they've already been confused about what the yellow cells are.
- **Suggested fix:** Move the color-coding orientation to row 3 (under the date range) or add it as a comment on the first yellow cell the CEO encounters.

## Spot-Checks: Claims vs. Data

### Check 1: "Cinderhaven budgets 17% for trade spend" → 17.3% structural rate

Source: `AVG(trade_spend_pct_*) × channel_revenue / total_revenue` = $4,435,052 / $25,593,052 = 17.33%

**Verdict: ACCURATE** — 17% is appropriate rounding for the headline; 17.3% is used where precision matters.

### Check 2: "The gap is $1 million per year" → $1,012,455 operational waste

Source: `SUM(amount) FROM deductions WHERE deduction_type != 'promo_billback' AND trailing_365` = $1,012,455

**Verdict: ACCURATE** — "$1 million" is a fair characterization of $1,012,455.

### Check 3: "137 promo-billback deductions totaling $95,826 reference promotions that do not appear" (ghost promos)

Source: Ghost promo query returns 137 deductions, $95,826.

**Verdict: ACCURATE** — exact match.

### Check 4: "a 14.3% recovery rate" (executive memo) vs. "a 13.7% recovery rate" (walkthrough)

Source: $98,216 / $716,082 = 13.7%

**Verdict: INACCURATE in memo** — 14.3% is wrong. 13.7% (walkthrough) is correct per current data.

### Check 5: "Walmart contributes 51% of revenue"

Source: $13,001,138 / $25,593,052 = 50.8%

**Verdict: ACCURATE** — 51% is fair rounding of 50.8%.

## Checklist Results

### Conclusions Follow from Evidence
- [x] Every claim supported by data — spot-checks confirm key numbers
- [x] Prose adjacent to visualizations matches data — KPI labels, waterfall, category table all accurate
- [x] Recommendations grounded in analysis — Monday morning actions cite specific dollar amounts and categories
- [x] Caveats stated where they matter — methodology limitations, "not a causal model," benchmark limitations all documented
- [ ] **Key findings reflect most important findings** — PARTIAL: the April 2026 spike ($152K, 2x average) is the kind of "Monday morning" finding the plan calls for but it's not surfaced in any narrative document

### Audience Calibration
- [x] Technical depth matches audience — memo is CEO-appropriate, walkthrough is analyst-appropriate
- [x] Jargon appropriate — trade spend terms defined in glossary, used correctly in body
- [x] "So what" is explicit — memo ends with "three things to do Monday morning"
- [x] Action items concrete — specific dollar amounts, specific categories, specific processes to fix

### Operational Substance
- [x] Narrative adds insight beyond charts — walkthrough provides context (why mid-market CPG is vulnerable, why three buckets don't work)
- [x] Business context woven in — retailer dynamics, channel economics, dispute mechanics
- [ ] **Numbers in prose match data** — FAIL: recovery rate contradicts across documents (P1); dispute count off by 1 in memo/methodology
- [ ] **Labels in prose match visualizations** — PARTIAL: walkthrough says "chart," workbook has text indicator (P5)

### Structural Clarity
- [x] Logical flow — README → memo → workbook → walkthrough → defensibility log forms a coherent reader path
- [x] Section titles descriptive — walkthrough sections are "The problem," "The methodology," "The findings," not generic
- [x] Length appropriate — memo is genuinely one page, walkthrough is thorough without padding
- [x] No copy-paste duplication — each document serves a different moment and reader

### Labels, Annotations, and Metadata
- [x] Tab names clear — "Executive Pulse," "Leak Diagnostic," "Promo Efficacy" describe content
- [x] Column headers readable — "Deduction Type," "Amount," "Owner," "Root Cause" are self-explanatory
- [x] Units stated — $ and % formats applied consistently, "trailing 365 days" noted on each tab
- [x] Adjustable inputs clearly marked — yellow fill + comments on every input cell
- [ ] **Cross-references accurate** — PARTIAL: walkthrough references `dev/sql/` query paths correctly, but "trend chart" reference is wrong (P5)
