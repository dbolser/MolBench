**Effect of grounding packs (PRELIMINARY).** Change in F1 when the task's frozen grounding pack is added to the request (`spec_grounded` minus `spec`), for the 15 models that ran both. Three ways to count, because they answer different questions. Row 1 includes the outputs that became invalid. Row 2 keeps only the 15 tasks that need a lookup (Clinical, Resolution). Row 3 keeps only task × model pairs whose output was valid in both conditions, so it isolates the effect on content; of those pairs 69 improved, 92 got worse and 486 did not change. 95% CI: bootstrap, resampling whole structures.

| Comparison | n | Change in F1 | 95% CI |
| :--- | ---: | ---: | ---: |
| All tasks, all outputs (mean over models) | 70 | -0.041 | -0.066 to -0.022 |
| Lookup tasks only, all outputs (mean over models) | 15 | -0.021 | -0.038 to +0.006 |
| Task × model pairs valid in both conditions (pooled) | 647 | -0.004 | -0.010 to +0.003 |
