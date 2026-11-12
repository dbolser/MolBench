# The task format

Format version 1. One schema for every task of the final corpus, on both tracks.
`molbench/tasks.py` is the code form of this page and checks every file when it is
loaded; `scripts/validate_tasks.py` checks the corpus as a whole. If this page and the
code disagree, a test fails (`tests/test_tasks_format.py`).

A task is **one JSON file** anywhere under `tasks/`. File and directory names carry
no meaning; the `id` does. Every field below is written in every file, with `null`
or `[]` where it does not apply, so a missing field is always a mistake.

```bash
uv run python scripts/validate_tasks.py           # the corpus in tasks/
uv run python scripts/validate_tasks.py --final   # what the frozen corpus must pass
```

## Fields

| field | type | meaning |
|---|---|---|
| `id` | string | Unique and stable: it never changes once results exist. Letters, digits, `.`, `_`, `-`. |
| `track` | `"mvs"` \| `"api"` | The answer format: a MolViewSpec scene, or a list of pdbe-molstar 3.3.2 calls. |
| `tier` | string | One of the tiers below. |
| `family` | string | Id of the template (generator family) that made the task. Confidence intervals are clustered by structure and by family. |
| `structures` | list of strings | The structures the reference loads, lower case, in order of first use: a PDB id (`"1cbs"`) or the panel id of an AlphaFold model (`"af-p04637-f1-model_v6"`). The first is the cluster key. Empty only when the reference loads no structure entry (the PDBe-KB superposition view). |
| `prompt` | string | The request, as a structural biologist would say it. It must determine the reference completely (plan decision 17). |
| `reference` | scene or call list | The answer. MVS: an MVS state `{"root": {...}}` (a bare root node is also read). API: a JSON array of canonical actions (`molbench/schema.py`). It holds only what the request states. |
| `accepted` | list | Further answers that are equally right, in the same form as `reference`. Empty for most tasks. In the accept-set tier each one is a *different* final state; elsewhere it is a harmless equivalent the grader would not otherwise see as equal. |
| `context` | object \| null | The start state of a follow-up turn; `null` on a single turn. See "Follow-up turns". |
| `target` | list \| null | Which part of the reference is the thing asked for, for the target score. See "Target". `null` when the request has no atom target (a background colour, the spin setting). |
| `twin_of` | string \| null | Id of the same request on the other track. Always mutual. |
| `paraphrase_of` | string \| null | Id of the original phrasing this task rewords; `null` on an original. |
| `style` | `"full"` \| `"terse"` \| `"indirect"` | How the prompt is phrased. `full` on every original; `terse` or `indirect` on a paraphrase. |
| `split` | `"public"` \| `"heldback"` | `heldback` tasks come from the same generators on structures no public task uses, and are not published before the run (decision 21). They are run exactly like public ones. |
| `grounding` | object \| null | The frozen grounding pack: `{"rule": "<rule id>", "text": "<facts>"}`. Appended to the request only in the grounding condition, and only on the lookup tiers. |
| `provenance` | object | How the reference was made: `script` (repo path of the generator), `inputs` (the frozen files it read), `date` (`YYYY-MM-DD`), `checks` (the checks the reference passed, in words). |
| `skills` | list of strings | Skill tags for the per-skill breakdown (`load`, `selection`, `color`, ...). At least one. |

Optional fields: `title` and `notes` (free text for people); `accepted_structures`
(resolve tier: other structure ids that count as the reference's); `accepted_targets`
(one target per entry of `accepted`, when the alternatives have different targets).
Any other field is an error, which is how a typo in a field name is caught.

### Tiers

| tier | what is asked |
|---|---|
| `translation` | Everything needed is in the request: turn it into the format. |
| `grounded` | The request names something that must be found in the structure (the ligand, the disulfides). |
| `interactions` | Named atoms and a measurement or contact between them. |
| `resolve` | The structure is named by protein, not by id. A lookup tier. |
| `clinical` | A variant given in UniProt numbering has to be mapped to the structure's residues. A lookup tier. |
| `followup` | A start state plus an edit request. Exactly the tasks with a `context`. |
| `accept_set` | An ambiguous request with several accepted final states. `accepted` is not empty. |
| `tool_only` | Something only the API track can express (a viewer setting with no MVS counterpart). API track, no twin. |

The grounding-pack condition runs on the lookup tiers only (`resolve`, `clinical`;
`molbench.tasks.LOOKUP_TIERS`). No other condition depends on the tier.

### Follow-up turns

```json
"context": {"scene": {"root": {...}}, "noop": false}      // MVS track
"context": {"calls": [{"action": "load", ...}], "noop": false}   // API track
```

The model is shown the start state and then the request, and must answer with the
**full** new scene or the **full** call list (decision 19):

```
Current scene (MolViewSpec JSON):          Calls made so far (JSON array):
{"root":{...}}                             [{"action":"load",...}]

Request: Colour the biotin (BTN) red.      Request: Colour the biotin (BTN) red.
```

`reference` is the complete final state, not a patch, and is graded like any other
answer: only the final state counts, so an answer that rebuilds the scene from
nothing and lands on the right state is right. `noop: true` marks a request that
needs no change; its reference is the start state, and returning the start state
unchanged is the right answer. The validator checks the flag against the grader.

### Target

The target score judges the requested atoms alone: are they selected, drawn in the
requested representation, in the requested colour (decision 17). `target` is a list
of parts:

```json
"target": [{"selector": {"label_comp_id": "BTN"}, "representation": "ball_and_stick", "color": "red"}]
```

- `selector` names the atoms, on both tracks, in the MVS selector vocabulary (a static
  name such as `"polymer"`, a ComponentExpression, or a list of them). It is resolved
  on the frozen atom table by `molbench.atoms.AtomTable.selector`, so twins can be
  checked to select the same atoms whatever keys their references use.
- `representation` and `color` are what the request asks for, in the track's own
  vocabulary (`ball_and_stick` in MVS, `ball-and-stick` in the API); `null` when the
  request does not state one.
- `structure` names the structure the part is on; needed only when the task loads
  more than one.

### Twins and paraphrases

- **Twins** are the same request on the two tracks: the same `prompt`, `structures`,
  `split`, `style` and `tier`, and the same target atoms. `twin_of` points each at the
  other. The references differ, because the formats do (a bare `load` already draws
  the whole structure; an MVS scene draws only what it lists).
- **Paraphrases** are other wordings of one request on one track. The original has
  `style: "full"`; each paraphrase has `paraphrase_of` set to the original's id, a
  `terse` or `indirect` style, a different `prompt`, and the same `reference`,
  `accepted`, `context`, `target`, `structures`, `split`, `tier` and `family`. A
  paraphrase's twin is the paraphrase with the same style on the other track.

## What the validator checks

`scripts/validate_tasks.py` exits non-zero unless all of these hold:

1. Every file matches the schema above (all errors of all files are listed).
2. Ids are unique.
3. Twins and paraphrases are linked as described; twins select the same target atoms.
4. Every structure is in the panel (`data/panel/panel.json`) and has a frozen atom
   table; no structure is used by both splits; every target part selects atoms.
5. Every reference grades as exactly right against its own task: success, F1 = 1 and,
   once the grader reports it, target score 1. Every accepted alternative grades as
   itself and is accepted by its task; in the accept-set tier it is a different final
   state from the reference.
6. A follow-up's start state grades as itself, and `noop` agrees with the grader.
7. `provenance.script` exists in the repository.
8. No task uses 1HSG. It is the worked example in the API system prompt, so the
   prompt, structures, reference, alternatives and start state are all searched.

`--final` adds: no task in the old format, and a target score reported for every
reference.

## How a task is graded

The runner hands the whole task to one function, `grader.grade_task(task, prediction)`,
and reads from its result `f1`, `success`, `target_f1`, `outcome` and `grader` (other
keys are kept and ignored). A task that cannot be graded on atoms stops the run: a
structure with no atom table is refused when the run is planned, and an API answer
not graded by the final-state grader raises an error instead of being scored some
other way. Task success for a model on a task is the mean over its samples; "all
samples right" is reported next to it.

## Old task files

Files written before this format (they have `category` and no `track`) are **read
through an adapter** (`molbench.tasks.adapt_legacy`), not rewritten: `category` gives
the track, `source` the tier, `reference_mvs` the reference, `categories` / `skills`
the skills, `accepted_ids` the `accepted_structures`; `structures` is read off the
reference; `split` is `public`, `style` is `full`, and `target`, `context` and the
links are `null`. Old API tasks get the tier `unclassified`, which no new file may
use. They load and run, but `--final` refuses them: the final corpus is generated in
this format.

A loaded task also carries the names older code reads (`category`, `categories`,
`reference_mvs`, `accepted_ids`), so code that goes through `runner.load_tasks` or
`molbench.tasks.load_corpus` needs no change. Code that opens `tasks/**/*.json`
itself does.

## Fixture tasks

`tests/fixtures/tasks/` holds 17 tiny tasks of every kind above (follow-up, one of
them a no-op; accept-set; twins; paraphrases; held-back), built from the frozen panel
by `tests/fixtures/build_fixture_tasks.py`. They are examples of the format and keep
the dry run honest until the real corpus has every kind. They are never part of a
real run.
