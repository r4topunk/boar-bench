# v0.3 power statement (T6 EVALFIX, 2026-10-12; source: rnd/research/coordinator/arms/evalfix/aggregates/power.json; 0 judge calls)

Assumptions: items independent; paired Δ tested two-sided α 0.05, 80 % power, t-corrected; Δ = 0.03 on the raw ratio-of-sums scale;
s_d = SD of per-item delta-method influence differences (linearised ratio-of-sums), measured on existing Opus rows. Seeds are averaged per item.

| arm contrast (V-para n 51) | s_d 1 seed | n, 1 seed | s_d 2 seeds | n, 2 seeds |
|---|---|---|---|---|
| deep+think vs deep (T-D, largest arm change) | 0.156 | 213 | 0.116 | 119 |
| quant ceiling vs H (Q-H) | 0.119 | 126 | 0.084 | 63 |
| 4B v0.2, K seed-vs-seed (n 110) | 0.092 | 76 | - | - |
Planning rule: 4B arms n ~ 80; deep/thinking arms with a large change n ~ 210 (1 seed) or ~ 120 (2 seeds); a small change (Q-H, H-T) needs less.
So n = 110 resolves Δ 0.03 for 4B arms with 1 seed and for deep arms only with 2 seeds (and only for T-D-sized variance or smaller).

Bar test "mean raw ratio > 0.50, n = 110, one-sided α 0.05" (v0.2 per-item SD of the linearised ratio: 0.19 for H, 0.20 for 4B K):
- No run noise: se 0.018-0.019, required point estimate = 0.530-0.532 (0.53); a true 0.53 passes only ~50 % (0.51 H, 0.46 K).
- With common-mode seed noise sigma_run 0.020 added (se = sqrt(s_item^2/110 + 0.02^2) = 0.027-0.028): required point = 0.545-0.546; a true 0.53 passes ~29 %.
- n for 80 % power at a true 0.53 (no run noise): ~240-280. Run noise does not shrink with n: averaging k seeds gives sigma_run/sqrt(k) (2 seeds: 0.014, required ~0.538).
Criterion to freeze: state the required point estimate (0.53 without, 0.545 with one-seed run noise) before the claim run, and use >= 2 seeds for deep arms.
Caveat: V-para s_item is 0.107 (items less heterogeneous), so do not use V-para SDs for the v0.3 bar test; CIs here are t-based, not bootstrap.
