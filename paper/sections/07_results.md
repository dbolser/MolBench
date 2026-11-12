## 6. Results

> **{{run.status_tag}}.** Everything in this section comes from the *{{run.label}}*
> (run of {{run.date}}): {{mvs.spec.n_models}} models, the MVS track only, {{mvs.n_tasks}} tasks
> on {{mvs.n_structures}} structures, {{mvs.spec.samples_per_task}} sample per task. The tables
> have the shape the final run will fill. The API track, the paired analysis, the follow-up tier
> and the accept-set tier have no results yet.

{{include:generated/table_mvs_corpus.md}}

### 6.1 Whether the output is a valid scene decides the ranking

{{include:generated/table_mvs_leaderboard.md}}

Strict F1 ranged from {{mvs.spec.f1_min:.3f}} ({{mvs.spec.worst.name}}) to
{{mvs.spec.f1_max:.3f}} ({{mvs.spec.best.name}}), a spread of {{mvs.spec.f1_spread:.2f}}. The
valid-scene rate ranged from {{mvs.spec.valid_min:.1%}} to {{mvs.spec.valid_max:.1%}}. The two
are almost the same ranking: across the {{mvs.spec.n_models}} models the correlation between
valid-scene rate and strict F1 is r = {{mvs.spec.r_valid_f1:.3f}} (Figure 1).

![**Figure 1.** Strict F1 against valid-scene rate, one point per model ({{run.status_tag}}). Strict F1 is the mean score over all tasks, with unshowable output scoring 0. Valid-scene rate is the share of outputs that Mol\* accepts and loads. Points near the dashed line are models whose valid scenes are almost all correct. Circles: open weights. Squares: closed weights.](generated/fig_mvs_validity.svg)

Over valid scenes only, the models are close. F1 over valid scenes ranged from
{{mvs.spec.f1_valid_min:.3f}} to {{mvs.spec.f1_valid_max:.3f}}, a spread of
{{mvs.spec.f1_valid_spread:.2f}} against {{mvs.spec.f1_spread:.2f}} for strict F1 (Figure 2). The
model with the lowest strict score, {{mvs.spec.worst.name}}, produced a valid scene for
{{mvs.spec.worst.valid:.1%}} of tasks, and those few scenes scored
{{mvs.spec.worst.f1_valid:.2f}}.

![**Figure 2.** Per model: strict F1 with its 95% interval (filled circle and bar) and F1 over valid scenes only (open diamond) ({{run.status_tag}}). The interval resamples whole structures. The gap between circle and diamond is the cost of invalid output.](generated/fig_mvs_leaderboard.svg)

The intervals are wide. With {{mvs.n_structures}} structures and one sample, the interval of the
best model ({{mvs.spec.best.f1_lo:.2f}} to {{mvs.spec.best.f1_hi:.2f}}) overlaps those of
{{mvs.spec.n_overlap_best}} other models. This panel cannot order the leading models.

Task success is lower than F1 suggests. The share of outputs that were exactly right ranged
from {{mvs.spec.success_min:.1%}} to {{mvs.spec.success_max:.1%}}.

### 6.2 What the invalid outputs are

{{include:generated/table_mvs_outcomes.md}}

Of {{mvs.spec.n_samples}} outputs, {{mvs.spec.n_failed}} were not valid scenes, and
{{mvs.spec.invalid_json_share_of_failures:.0%}} of those were invalid JSON. Three models
({{mvs.spec.failures_top3_models}}) account for {{mvs.spec.failures_top3_share:.0%}} of the
invalid outputs.

{{include:generated/table_mvs_json_shapes.md}}

Most invalid JSON is a miscount of braces. Of the {{mvs.spec.json_shape.n_raw}} invalid-JSON
outputs with archived text, {{mvs.spec.json_shape.brace_count_share:.0%}} open and close a
different number of braces. A scene is a tree nested at least seven levels deep, and one brace
too many or too few loses the whole answer.

### 6.3 Repairing the JSON offline removes most of the spread

{{include:generated/table_mvs_repair.md}}

We passed each invalid-JSON output through a JSON repair library and graded the result, without
calling any model. Of {{mvs.spec.repair.n_raw}} outputs with archived text,
{{mvs.spec.repair.n_scene}} became a scene tree and {{mvs.spec.repair.n_positive}} scored above
zero, with a mean F1 of {{mvs.spec.repair.mean_f1:.2f}}. The largest changes were for
{{mvs.spec.repair.top1.name}} ({{mvs.spec.repair.top1.strict:.2f}} to
{{mvs.spec.repair.top1.repaired:.2f}}), {{mvs.spec.repair.top2.name}}
({{mvs.spec.repair.top2.strict:.2f}} to {{mvs.spec.repair.top2.repaired:.2f}}) and
{{mvs.spec.repair.top3.name}} ({{mvs.spec.repair.top3.strict:.2f}} to
{{mvs.spec.repair.top3.repaired:.2f}}) (Figure 3).

Two cautions apply. The repaired scenes were not checked by the viewer, so these are upper
bounds. And the raw text of {{mvs.spec.repair.n_no_raw}} invalid outputs was never archived
(model: {{mvs.spec.repair.models_missing_raw}}), so that model could not be repaired here.

![**Figure 3.** Per model: strict F1 as reported (filled circle) and after offline JSON repair (open diamond) ({{run.status_tag}}). Repair is a counterfactual computed from archived outputs; no model was called. Repaired scenes were not checked by Mol\*, so the diamonds are upper bounds.](generated/fig_mvs_repair.svg)

### 6.4 Difficulty by regime

{{include:generated/table_mvs_regimes.md}}

On strict F1 the regimes mostly reflect validity. Once invalid output is set aside, a gradient
appears (Figure 4). Translation and structure-grounded tasks are near the ceiling: F1 over valid
scenes is {{mvs.spec.regime.Translation.f1_valid_mean:.2f}} and
{{mvs.spec.regime.Grounded.f1_valid_mean:.2f}}. Clinical tasks are much harder
({{mvs.spec.regime.Clinical.f1_valid_mean:.2f}}), and almost no clinical output was exactly
right (success {{mvs.spec.regime.Clinical.success_mean:.1%}}).

These numbers rest on thin samples, and we state them with that caveat. The clinical regime is
{{mvs.spec.regime.Clinical.n_tasks}} tasks on {{mvs.spec.regime.Clinical.n_structures}}
structure, so no interval over structures can be given. The resolution regime has
{{mvs.spec.regime.Resolution.n_valid}} valid outputs out of
{{mvs.spec.regime.Resolution.n_samples}}, from
{{mvs.spec.regime.Resolution.n_models_with_valid}} of {{mvs.spec.n_models}} models. The
interactions regime has {{mvs.spec.regime.Interactions.n_valid}} valid outputs out of
{{mvs.spec.regime.Interactions.n_samples}}.

![**Figure 4.** Scores by regime ({{run.status_tag}}). Solid bar: strict F1, mean over models. Hatched bar: F1 over valid scenes, mean over models. Dots: F1 over valid scenes for each model. The labels give the number of tasks, structures and valid outputs behind each row.](generated/fig_mvs_regimes.svg)

{{include:generated/table_mvs_differences.md}}

The breakdown of where valid scenes lose points shows what each regime measures, and exposes a
flaw. In the clinical regime the commonest fault is a missing component
({{mvs.spec.diff_regime.Clinical.missing_component}} of the
{{mvs.spec.diff_regime.Clinical.n}} imperfect valid scenes): a part of the reference scene is
absent from the answer. In the resolution regime,
{{mvs.spec.diff_regime.Resolution.unrequested_colour}} of the
{{mvs.spec.diff_regime.Resolution.n}} imperfect valid scenes lost points for a colour that the
request did not ask for and the reference does not contain. Only
{{mvs.spec.diff_regime.Resolution.structure}} of them loaded an entry outside the accepted
list. The low resolution score is therefore mostly a penalty for unrequested styling, and not a
failure to find the protein. ⟦PENDING: decide whether unrequested styling is penalised in the final corpus;
if not, references or grader change before the final run⟧

### 6.5 Grounding packs did not help

{{include:generated/table_mvs_grounding.md}}

We expected that giving the model the facts it needs would raise scores on the tasks that need
a lookup. It did not. We give three numbers, because each answers a different question.

- Over all tasks and outputs, mean F1 changed by {{mvs.grounding.all.delta:+.3f}} (95% interval
  {{mvs.grounding.all.lo:+.3f}} to {{mvs.grounding.all.hi:+.3f}}): it fell.
- On the {{mvs.grounding.n_lookup_tasks}} lookup tasks ({{mvs.grounding.lookup_regimes}}), the
  change was {{mvs.grounding.lookup.delta:+.3f}} ({{mvs.grounding.lookup.lo:+.3f}} to
  {{mvs.grounding.lookup.hi:+.3f}}).
- Over the {{mvs.grounding.both_valid.n}} task and model pairs whose output was valid in both
  conditions, the change was {{mvs.grounding.both_valid.delta:+.3f}}
  ({{mvs.grounding.both_valid.lo:+.3f}} to {{mvs.grounding.both_valid.hi:+.3f}}):
  {{mvs.grounding.both_valid.better}} pairs improved, {{mvs.grounding.both_valid.worse}} got
  worse and {{mvs.grounding.both_valid.same}} did not change.

The first number is negative mainly because the longer request produced more invalid output.
The mean valid-scene rate changed by {{mvs.grounding.valid_delta_mean:+.1%}} in absolute terms,
and for {{mvs.grounding.valid_drop_max.name}} it fell from
{{mvs.grounding.valid_drop_max.from:.0%}} to {{mvs.grounding.valid_drop_max.to:.0%}}. The third
number removes that effect and is indistinguishable from zero. Individual models moved in both
directions on the lookup tasks: {{mvs.grounding.n_models_lookup_gain_10}} gained 0.10 or more
and {{mvs.grounding.n_models_lookup_loss_10}} lost 0.10 or more (Figure 5).

We had set a threshold in advance: build a live tool loop only if packs raised the lookup tasks
by 0.10 F1. The threshold was not met.

![**Figure 5.** Per model: change in strict F1 when the grounding pack is added ({{run.status_tag}}). Bar: all tasks. Diamond: lookup tasks only. Values left of zero mean the pack made the score worse.](generated/fig_mvs_grounding.svg)

### 6.6 Without the format reference, no scene was valid

{{include:generated/table_mvs_conditions.md}}

{{mvs.bare.n_models}} models ({{mvs.bare.models}}) were run in the `bare` condition, with and
without grounding packs. Of {{mvs.bare.n_samples}} outputs, {{mvs.bare.n_valid}} were valid
scenes ({{mvs.bare.outcomes}}). The models wrote JSON that resembled a scene and that the viewer
rejected. This result rests on {{mvs.bare.n_models}} models only. It says that, for these
models, knowledge of the MolViewSpec format came from the prompt and not from training.

### 6.7 Tree score against render-checked score

{{include:generated/table_mvs_escalation.md}}

Of {{mvs.spec.escalation.n}} outputs, {{mvs.spec.escalation.perfect}} matched the reference tree
exactly, {{mvs.spec.escalation.failed}} were invalid, and {{mvs.spec.escalation.escalated}}
valid but imperfect scenes were rendered and compared. {{mvs.spec.escalation.rescued}} were
rescued: {{mvs.spec.escalation.rescued_pixel}} by near-identical pixels and
{{mvs.spec.escalation.rescued_judge}} by the image-pair judge ({{mvs.spec.escalation.judge}}).
Validated F1 exceeded tree F1 by {{mvs.spec.escalation.lift_min:.3f}} to
{{mvs.spec.escalation.lift_max:.3f}} per model. The tree score is thus slightly strict, and the
correction is too small to change any conclusion above. How far the judge's rescues can be
trusted is the subject of the rating study.
⟦PENDING: rating-study readout⟧

### 6.8 The first API track did not separate models

The first version of the API track had {{legacy_api.n_tasks}} hand-written tasks and a grader
that compared call lists field by field. A keyword script that uses no model scored
{{legacy_api.baseline_f1:.3f}} on it. The {{legacy_api.n_models}} models scored between
{{legacy_api.f1_min:.3f}} and {{legacy_api.f1_max:.3f}} (median
{{legacy_api.f1_median:.3f}}; run of {{legacy_api.run}}). The script matched or beat the mean
model on {{legacy_api.n_tasks_baseline_ge_mean}} tasks, and API scores were unrelated to MVS
scores (r = {{legacy_api.r_api_mvs:.2f}} over {{legacy_api.r_api_mvs_n}} models). A check of the
references against the structures also found errors, including references that used label
numbering where author numbering was meant.

We report these numbers only as the reason for the rebuild described in Sections 3 and 4. They
are not results of this benchmark.

{{include:generated/table_api_leaderboard.md|PENDING: API-track leaderboard (final run)}}

{{include:generated/table_paired.md|PENDING: paired MVS–API analysis: discordant pairs and McNemar test per model, with and without clinical twins (final run)}}

{{include:generated/table_followup.md|PENDING: follow-up and accept-set tiers (final run)}}

### 6.9 Cost

{{include:generated/table_mvs_cost.md}}

The {{mvs.spec.n_models}} models used {{mvs.spec.cost.input_mtok}} million input tokens and
{{mvs.spec.cost.output_mtok}} million output tokens for the headline condition. A price was
recorded for {{mvs.spec.cost.n_priced}} models, which together cost
${{mvs.spec.cost.total_priced_usd:.2f}}. The best open-weight model
({{mvs.spec.cost.best_open.name}}, strict F1 {{mvs.spec.cost.best_open.f1:.2f}}) cost
${{mvs.spec.cost.best_open.usd:.3f}} for the run. The best closed-weight model
({{mvs.spec.cost.best_closed.name}}, {{mvs.spec.cost.best_closed.f1:.2f}}) cost
${{mvs.spec.cost.best_closed.usd:.3f}}, {{mvs.spec.cost.closed_over_open}} times as much.
⟦PENDING: prices for the {{mvs.spec.cost.n_unpriced}} models with no recorded price; final-run
cost for all models and both tracks⟧
