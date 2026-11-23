## S8. Further tables of the pilot run (October 2026)

**These tables are preliminary.** They were written by script from the archived pilot run and
are the record behind Section 6.6 of the paper. They differ from Section 6.6 in one way that
matters: the scores here are those of the *earlier* scene grader, which compared scene trees
path by path, whereas Section 6.6 regrades the same answers on drawn state. Its numbers
therefore differ, and not all in one direction. F1 is lower there, most of all in the clinical
category ({{oct.spec.clinical.f1:.2f}} against {{mvs.spec.regime.Clinical.f1_mean:.2f}} here).
The share of exactly right answers is in places higher: in the translation category the task
success rate of Section 6.6 is {{oct.spec.translation.success:.1%}}, and the share of answers
with a score of 1 here is {{mvs.spec.regime.Translation.success_mean:.1%}}. Three column names differ from those of the paper, so that no word has two
meanings. *Score of 1* is the share of answers that score exactly 1 under the earlier grader
(the forerunner of task success). *Earlier-grader F1* is the F1 of that grader. *Requested
part*, in Table S14, is defined in the caption of that table; the pilot tasks stored no
target, so there is no target score in these tables.

Two notes on single tables. In Table S10 the caption defines five classes and the table has
four columns: no answer of the pilot run fell in the class "JSON, not a scene". In Table S14
the count for the clinical category ({{mvs.spec.target.Clinical.target_exact}} answers with
the requested part exactly right) differs slightly from that of Section 6.6 of the paper
({{oct.spec.clinical.highlight_exact_n}}), because the two are found by different rules: here
by the earlier grader, component by component of the scene tree, and there on drawn state.

{{include:generated/table_mvs_corpus.md|pilot:Table S8}}

{{include:generated/table_mvs_leaderboard.md|pilot:Table S9}}

{{include:generated/table_mvs_outcomes.md|pilot:Table S10}}

{{include:generated/table_mvs_json_shapes.md|pilot:Table S11}}

{{include:generated/table_mvs_repair.md|pilot:Table S12}}

{{include:generated/table_mvs_regimes.md|pilot:Table S13}}

{{include:generated/table_mvs_targets.md|pilot:Table S14}}

{{include:generated/table_mvs_differences.md|pilot:Table S15}}

{{include:generated/table_mvs_grounding.md|pilot:Table S16}}

{{include:generated/table_mvs_conditions.md|pilot:Table S17}}

{{include:generated/table_mvs_escalation.md|pilot:Table S18}}

{{include:generated/table_mvs_cost.md|pilot:Table S19}}

### S8.1 The trial of the rating study

*Purpose.* To see whether answers that the earlier grader scored below 1 looked the same as
the reference to people, that is, to look for false fails, and to try out the image judge as
a way of finding them.

*What was done.* In October, each valid scene that scored below 1 was rendered, and an image
judge (a vision-language model; Section 5.5 of the paper) was shown its picture beside the
picture of the reference. Volunteers then judged a sample of the same picture comparisons. In
all, {{pilot.n_raters:word}} raters, one of them an author, gave {{pilot.all.n_labelled}}
verdicts of "same" or "different" on {{pilot.all.n_pairs}} picture comparisons.

*Result.* People and the image judge gave the same verdict in {{pilot.all.agreement:.0%}} of
cases. Cohen's kappa, which is agreement beyond what chance would give (0 is chance, 1 is
perfect), was {{pilot.all.kappa:.2f}} (95% interval {{pilot.all.kappa_lo:.2f}} to
{{pilot.all.kappa_hi:.2f}}). Where the judge had said "same", people agreed in
{{pilot.all.rescue:.0%}} of cases (95% interval {{pilot.all.rescue_lo:.0%}} to
{{pilot.all.rescue_hi:.0%}}), or in {{pilot.indep.rescue:.0%}} (95% interval
{{pilot.indep.rescue_lo:.0%}} to {{pilot.indep.rescue_hi:.0%}}) when the author's verdicts
are left out.

*Limits.* Only {{pilot.n_raters_passing_checks:word}} of the {{pilot.n_raters:word}} raters
met the attention-check rule that was written before the data were seen (at least
{{pilot.check_rule:.0%}} right on each kind of check item): the author was never shown a check
item, and one volunteer answered "can't tell" on a check, which the rule counts as a miss. The
numbers above include all raters and so depart from that rule. Only
{{pilot.all.pairs_two_raters}} picture comparisons received two verdicts, so agreement between
people cannot be estimated. The trial does not validate the image judge, and it supports no
statement about categories, single models or the final run. No score in the paper uses the
image judge. As a check of how much it could matter: under the earlier grader, counting the
judge's "same" verdicts as right would have changed no model's mean F1 by more than
{{mvs.spec.escalation.lift_max:.3f}} (Table S18).
