# Failures — cinderhaven-data

## 2026-05-17: VELOCITY_SCALE not recalibrated for SKU count change

**What happened:** Changed catalog from 90 to 50 SKUs without adjusting VELOCITY_SCALE. First build produced $13.6M annual revenue (target $23-27M) — a 47% shortfall roughly proportional to the 44% SKU reduction.

**Why it failed:** Revenue scales roughly linearly with SKU count. The multiplier was tuned empirically for 90 SKUs; halving the catalog halves the output.

**Fix:** Recalculated VELOCITY_SCALE as 0.66 × (25/13.6) ≈ 1.21. Second build hit $24.3M.

**Lesson:** When changing catalog size, back-of-envelope the revenue impact before running the full pipeline. `new_scale = old_scale × (target_revenue / (old_revenue × new_skus/old_skus))`.

**Tags:** calibration, velocity, scan-data

---

## 2026-05-17: Deduction rate doubling still undershoots 10K target

**What happened:** After bumping promo_billback, vague, and spoilage rates across all 7 retailer profiles (most doubled), deductions reached ~8K — still below the 10-16K target range (WARN).

**Why it failed:** Deduction count depends on order volume × per-order rates. With fewer SKUs generating fewer orders, doubling rates compensates but not enough. The relationship isn't purely multiplicative — slotting and post-audit claims are count-based, not rate-based.

**Fix (pending):** Either accept 8K as the natural output of a 50-SKU catalog and widen the target range, or increase order frequency to generate more deduction opportunities.

**Lesson:** Deduction volume is a function of both rate AND base order count. When SKUs drop, orders drop, and rate increases alone can't fully compensate without distorting the per-order economics.

**Tags:** calibration, deductions, target-ranges
