# NimbusAI — GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) | Share of Savings |
|---|---|---|
| Inference (cascade/cache/batch) | $1,212 | 9.7% |
| Purchasing (spot/reserved) | $10,040 | 80.3% |
| Right-size util-lies | $655 | 5.2% |
| Kill idle GPUs | $600 | 4.8% |

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cheapest+cleanest region: europe-north1

---

## 1. Executive Summary & Root Cause Analysis

### 1.1. The 'GPU-Util Lie' Problem
- Telemetry from `nvidia-smi` measures time-active clock rather than computational efficiency.
- Workloads on instances such as `gpu-h100-4` showed **98.2% GPU utilization**, yet the **Model FLOPs Utilization (MFU) was only 19.4%**.
- The root causes include unbatched inference requests, host-to-device memory transfer bottlenecks, and memory-bandwidth bound decode operations.
- Right-sizing over-provisioned GPUs to lower tiers (e.g., H100 -> A100/A10G) and fixing memory stalls avoids paying full H100 rental rates for fractional throughput.

### 1.2. Unit Economics Shift: $/GPU-Hour vs $/1M-Token
- Traditional cloud metrics track $/GPU-hour, hiding inefficiency under high server utilization.
- Transitioning to **$/1M-token** revealed baseline serving cost at **$6.488 / 1M-token**, which dropped by **82.6% to $1.126 / 1M-token** under combined prompt caching, model cascading, and batch scheduling.

## 2. Prioritized Action Plan & Implementation Roadmap

1. **P1 — Purchasing Tier Realignment (ROI: $10,040/month)**: Migrate interruptible batch training jobs to Spot instances with 3% checkpoint overhead and commit high-duty inference workloads (duty cycle >= 55%) to 3-year Reserved instances.
2. **P2 — Inference Stack Optimization (ROI: $1,212/month)**: Enable Anthropic/OpenAI prompt caching (90% discount on cache hits), implement tiered model routing (small vs large models), and leverage 50% Batch API discounts.
3. **P3 — Kill Idle GPUs (ROI: $600/month)**: Implement automated shutdown policies for instances inactive (util < 10%) for >15 minutes.
4. **P4 — Right-Size Util-Lies (ROI: $655/month)**: Downscale over-provisioned memory-bound GPUs to match actual arithmetic intensity.

## 3. FinOps Governance & Sustainability

- **Tag Coverage & Chargeback**: Tag coverage reached **92%**, exceeding the 80% threshold required to transition from Showback to automated Chargeback.
- **FOCUS 1.x Export**: All billing records normalized to Open Multi-Vendor FOCUS schema (`outputs/focus_export.csv`).
- **Carbon-Aware Placement**: Relocating flexible workloads from `us-east-1` (380 gCO2/kWh) to `europe-north1` (30 gCO2/kWh) reduces carbon footprint by **92.1%** while securing lower electricity rates ($0.09/kWh).

_Figures are June-2026 as-of snapshots; re-baseline before acting._