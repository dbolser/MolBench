> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Planned comparisons (21 models, 3 samples per task)**

| Comparison | Tasks | Task success, first group | Task success, second group | Difference (95% interval) |
|:---|---:|---:|---:|---:|
| Public split against held-back split | 632 and 165 | 0.564 | 0.566 | +0.002 [-0.008, +0.011] |
| Full wording against terse wording | 30 requests | 0.559 | 0.562 | +0.003 [-0.018, +0.022] |
| Full wording against indirect wording | 30 requests | 0.559 | 0.550 | -0.009 [-0.034, +0.017] |
| Format reference against format reference plus JSON mode (20 models) | 797 | 0.565 | 0.563 | -0.001 [-0.009, +0.006] |
| Format reference against format reference plus grounding pack (lookup tiers, scene track) | 121 | 0.540 | 0.543 | +0.003 [-0.010, +0.017] |
| Format reference against no format reference (3 models, scene track) | 381 | 0.542 | 0.537 | -0.005 [-0.026, +0.015] |

Task success, strict, mean over the models that ran both sides. The difference is second minus first; its interval resamples structures (the two splits share none, so each side is resampled on its own; elsewhere the per-task difference is resampled). No interval where fewer than two structures are on a side.
