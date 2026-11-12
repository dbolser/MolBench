**Scores by regime, `spec` condition (PRELIMINARY).** *Valid / all*: valid outputs out of all outputs, pooled over models. *Models*: models with at least one valid output in the regime (the others cannot contribute to a valid-only mean). *F1 (valid)*: mean score over valid outputs, first averaged per model and then over models (mean), and over all valid outputs together (pooled). *Strict F1*: mean over all outputs, invalid ones scoring 0, averaged per model then over models. *Success*: share of outputs that are valid and score exactly 1. 95% CIs are for the pooled valid-only and pooled strict values, resampling whole structures; n/a where a regime has a single structure. Read the thin rows with care: the sample sizes are in the table.

| Regime | Tasks | Structures | Valid / all | Models | F1 (valid), mean | F1 (valid), pooled | 95% CI | Strict F1 | 95% CI | Success |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Translation | 41 | 7 | 491/615 | 15/15 | 0.978 | 0.977 | 0.974–0.979 | 0.780 | 0.755–0.795 | 65.4% |
| Grounded | 8 | 6 | 91/120 | 14/15 | 0.972 | 0.971 | 0.955–0.991 | 0.737 | 0.705–0.770 | 53.3% |
| Clinical | 9 | 1 | 96/135 | 15/15 | 0.672 | 0.679 | n/a | 0.483 | n/a | 1.5% |
| Resolution | 6 | 6 | 52/90 | 12/15 | 0.542 | 0.564 | 0.513–0.606 | 0.326 | 0.247–0.392 | 2.2% |
| Interactions | 6 | 3 | 54/90 | 14/15 | 0.850 | 0.854 | 0.822–0.884 | 0.512 | 0.356–0.770 | 22.2% |
