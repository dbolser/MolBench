## 5. Experimental setup

One run fills every result in Sections 6.1 to 6.5. Its plan is fixed in a single manifest
file before any model is called (SI Section S6). SI Section S12 gives this section in full.

### 5.1 Models

The models are chosen by a written rule, not by results. The {{plan.n_core_models}} *core
models* are those shown in the first version's online results browser in October 2026
(Section 12), taken over unchanged, so that the choice depends on no result of the present
benchmark; {{plan.n_core_in_pilot}} of them are in the pilot run of Section 6.6, and the
other could not be reached on the day of that run (SI Section S12.1). Most are the
smaller, cheaper models of their providers. {{plan.n_core_open}} have *open weights* (the
weights can be downloaded) and {{plan.n_core_closed}} have *closed weights* (the model can
be used only through a provider's service). Up to {{plan.n_optional_models}} *optional
models* (the largest current models of several providers of closed weights, and the largest
model with open weights) are named in the manifest and marked † in the tables; which of them are run is decided from the projected cost alone, before any
result exists. SI Table S7 lists every model with its price.
⟦PENDING: Dan — which of the optional models are run⟧

Two scripts that use no model are run on both tracks as floors. The *keyword script* maps
words of the request to fixed answers. The *literal script* writes what the request spells
out and uses every number as written, as an author residue number. It looks nothing up, so
the difference between a model and the literal script is what the model adds to the words
of the request. On a clinical task it copies the number (Box 1), so its rows show what
copying alone scores.

### 5.2 Prompting conditions

In each condition of Table 5 a model receives a system prompt and the request, and returns
one answer. Both system prompts say that the answer is judged by what the viewer ends up
showing; the scene prompt adds that anything drawn that was not asked for counts against the
answer.

**Table 5. Prompting conditions.** All main results come from the *main* condition. *Format
guide*: a frozen text in the system prompt that documents the answer format. *JSON mode*: a
provider option that forces syntactically valid JSON. *Grounding pack*: the result of an
offline lookup, appended to the request.

| Condition | What the model is given | Run on | Answers per task |
|:-----|:----------|:----------|--:|
| **Main** | A short instruction, the rule for the answer ("answer with one JSON value and nothing else") and the format guide | all models, all tasks, both tracks | {{plan.samples}} |
| Main + JSON mode | The same, with JSON mode switched on | every model that offers JSON mode ({{plan.n_json_mode_models}} of the {{plan.n_core_models}} core models, and each optional model that is run); all tasks, both tracks | 1 |
| Main + grounding pack | The same, with the task's grounding pack appended to the request | all models; the lookup categories, scene track | {{plan.samples}} |
| No format guide | The instruction and the rule for the answer only | {{plan.n_bare_models}} models, the three of the pilot run (SI Section S12.2); all tasks of the scene track | {{plan.samples}} |

The format guide is all that a model is told about the answer format. The guide of the
scene track documents selection by author and by label numbering; the guide of the
call-list track documents these and selection by UniProt position. Neither says how a given
structure is numbered. No prompt was tuned on benchmark tasks (SI Sections S7 and S12.2).

A grounding pack never contains a scene, a colour or a representation. For a clinical task
it contains the mapped residue, and for a name-resolution task a list of entries. This
condition therefore shows the most that a perfect lookup tool could add; it does not test
whether a model can use raw lookup tables.

### 5.3 Sampling

Each model answers each task {{plan.samples:word}} times in the main condition, at the
provider's default temperature, with a limit of {{plan.max_tokens:,}} tokens per answer
(more for models that first write hidden reasoning). An answer that reaches the limit is
*cut off* by the provider. A cut-off or invalid answer is scored as it stands and is not
retried.

### 5.4 Statistics

**Scores and intervals.** A per-model score is the mean over tasks of the mean over the
task's {{plan.samples}} answers (valid-only scores pool a model's valid answers); a mean
over models covers the core models and the optional models that were run, and leaves the
two scripts out. Intervals
are 95% bootstrap intervals [@efron1979] with {{run.bootstrap_replicates:,}} resamples.
Whole structures are resampled, not single tasks, because tasks on one structure share its
difficulties. Models are treated as fixed, so an interval describes these models and not
models in general.

**Paired comparison of the formats.** For each model and pair, a side is right when at least
2 of its {{plan.samples}} answers are right. In the primary comparison (Table 9a) an answer
is right when it is target-right, which is the same test in both formats; it covers the
{{corpus.twins.n_with_target}} pairs that have a target score. The secondary comparison
(Table 9b) uses task success, on all {{corpus.n_twin_pairs}} pairs. The two counts of pairs
that are right on one side only are compared with McNemar's exact test [@mcnemar1947], one
test per model. The test treats pairs as independent although several sit on one structure,
so we read its p values as descriptions and give beside them the difference of the two
counts with a resampled interval.

**The central clinical comparison.** On the scene track, clinical tasks in which copying the
number is right are compared with those in which it is wrong, on the target score, because
task success also falls when an answer adds unrequested context (difference row of Table
10).

**Six further planned comparisons** are the rows of Table 12, each a difference in task
success rate with an interval: the set-aside split, the two alternative wordings, JSON mode, the
grounding pack and the format guide. We do not correct for multiple comparisons, and we
report every count.

### 5.5 Human check of the grader

After the run, volunteers will check the grader's verdicts against pictures. A rater sees the request and
four pictures from one camera: the reference and a model answer, each drawn whole and each
zoomed on the target atoms. The rater says "same", "different" or "can't tell" twice: on
the whole scenes (compared with the grader's task success) and on the zoomed pictures
(compared with a target score of 1).

The study has {{study.n_pairs}} such comparisons of valid scene-track answers,
{{study.n_per_verdict}} for each verdict of the grader (task success; target-right but not a
success; neither), each rated by {{study.raters_per_pair:word}} raters. We will report how often people call the grader's task
successes the same and its other answers different, the same for the target score, and the
agreement between raters as the yardstick. The call-list track and the name-resolution category are left out (SI Section
S12.5). 

### 5.6 Reproducibility

One command performs the run from the manifest, and one rebuilds this paper from the
archived answers. A *connection test* of the run script on a few tasks, before the corpus was
frozen, exposed faults of the grader, which were corrected; it produced no result reported
here (SI Section S6.1).
