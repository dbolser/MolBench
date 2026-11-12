## 4. Grading

### 4.1 One idea for both tracks

An answer is graded on what the viewer would show. For a scene, that is the set of components:
which atoms, in which representation, in which colour, plus any drawn lines, labels and camera
focus. For a call list, it is the state of the viewer after the calls have run in order.

**Atom sets.** Every selection, in the answer and in the reference, is resolved against the
frozen atom table of the structure, following the selection rules of the viewer (Mol\* 5.9.0 for
scenes, pdbe-molstar 3.3.2 for call lists). Three consequences follow.

- Different names for the same atoms score the same. "All cysteines" equals the cysteines listed
  one by one.
- The two numbering schemes are kept apart. A structure file carries *author* numbering (chosen
  by the depositor, and often following the UniProt sequence) and *label* numbering (a plain
  count along the sequence in the file). In 1TUP, author chain A is the protein, and label chain
  A is a DNA strand. An answer that uses the wrong scheme selects the wrong atoms and is scored
  on those.
- A selection that matches no atom earns nothing.

**F1.** For the MVS track, the reference scene and the answer are each flattened into paths from
the root to each leaf (for example: entry 1TUP → protein → cartoon → grey). Reference paths are
matched to answer paths. A matched pair earns a similarity between 0 and 1. For a component, the
similarity is the overlap of the two atom sets, measured as the number of shared atoms divided
by the number of atoms in either (the Jaccard index). *Precision* is the total similarity
divided by the number of answer paths: it falls when the answer shows things that were not asked
for. *Recall* is the total similarity divided by the number of reference paths: it falls when
the answer leaves things out. **F1** is the harmonic mean of the two, from 0 (nothing right) to
1 (everything right and nothing extra).

**Task success.** An answer is a *success* if it is valid and its F1 is exactly 1: the final
state is right in every graded respect. F1 gives partial credit and is the smoother measure.
Success is what a user needs. We report both everywhere.

For the API track, the grader replays the calls against a model of the viewer state and compares
the final state with the reference state on the same terms.
⟦PENDING: API state-replay grader (`molbench/pdbe_state.py`) — describe exactly what state is
compared once it is merged⟧ An earlier API grader compared call lists field by field. Section 6.7
shows why it was replaced.

### 4.2 What happens to each output

Each output falls into exactly one class.

| Class | Meaning | Score |
|:---|:---|:---|
| Valid | Parses as JSON; the viewer accepts it; the structure loads | graded, 0 to 1 |
| Invalid JSON | No JSON object can be parsed from the output | 0 |
| JSON, not a scene | Valid JSON, but not an answer in the required format | 0 |
| Rejected by the viewer | Right format, but with a node or parameter the viewer refuses | 0 |
| Structure failed to load | Well formed, but it names a file that does not load | 0 |

Validity is checked by the viewer itself, in a headless browser, and not by a schema of our own.

### 4.3 Three scores, so that validity is reported and not hidden

- **Strict score** (primary). Mean over all outputs. Anything the viewer cannot show scores 0.
  This is what a user of the model would experience.
- **Score over valid outputs.** Mean over the valid outputs only. It asks: when the model does
  produce a scene, how good is the scene? It must be read with the valid-output rate next to it,
  because a model with few valid outputs is scored on few outputs.
- **Repaired score** (counterfactual). Each invalid-JSON output is passed through an open-source
  JSON repair library [@jsonrepair] and graded again. No model is called. This estimates how
  much of the loss is a formatting slip that a wrapper could fix. Repaired scenes are graded as
  trees but are not checked by the viewer, so the repaired score is an upper bound.

### 4.4 Render check (a side column)

The tree comparison can be too strict. Two scenes that differ as trees can look the same. As a
check, every valid scene that scores below 1 is rendered next to its reference at a fixed
camera. If the two images are near-identical pixel for pixel, or if an image-pair judge (a
vision-capable language model) calls them the same, the scene is *rescued* and counted as
correct. The result is the *validated F1*. It is reported as a side column and never replaces
the strict score, for two reasons: the judge is a model with its own errors
[@li2025misibench], and rescue can only raise a score.

### 4.5 Human rating study

To find out how far the image-pair judge can be trusted, human raters see the same image pairs,
blind to the model and to the judge's verdict, and say whether the two images show the same
thing. Known-identical pairs are mixed in as attention checks. Each pair is rated by two people.
We report agreement between raters, agreement between raters and the judge, and how often a
rescue by the judge is confirmed by a human.
⟦PENDING: rating-study readout — number of raters, pairs and ratings; human–human and
human–judge agreement with intervals; share of judge rescues confirmed⟧

### 4.6 Uncertainty

Tasks on one structure are correlated, so we do not treat tasks as independent. All 95%
confidence intervals come from a bootstrap [@efron1979] that resamples whole structures: all
tasks on a drawn structure enter together. We use {{run.bootstrap_replicates}} replicates and
the percentile method. With several samples per task, the samples of a task stay together. An
interval is not given where a group of tasks covers a single structure.
⟦PENDING: clustering by task template as well as by structure, as the final corpus allows⟧

### 4.7 Testing the grader

Every reference is graded against itself and must score 1. Each reference is tested against the
structure: every selection must match at least one atom, and for clinical tasks the selected
residue must have the amino acid that the variant record names. A rule-based script that uses no
model is run as a floor.
⟦PENDING: reference-against-structure tests for every tier (today: interaction tasks and atom-set
unit tests)⟧
⟦PENDING: floor of the rule-based script on the rebuilt API track⟧
