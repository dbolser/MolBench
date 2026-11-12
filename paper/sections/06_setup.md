## 5. Experimental setup

### 5.1 Models

⟦PENDING: final model panel, with provider, version string, access date and weight licence, from
the run manifest⟧

The preliminary panel has {{mvs.spec.n_models}} models from several providers, most of them
small or mid-sized and inexpensive. Each is marked as having open or closed weights, as
classified on the project leaderboard. ⟦PENDING: confirm the weight licence of each model⟧

### 5.2 Prompting conditions

- **`spec`** (headline; all models). The system prompt holds a short instruction, the output
  contract ("answer with one JSON object and nothing else") and the frozen format reference.
- **`spec` + grounding pack** (lookup regimes). As `spec`, with the task's grounding pack
  appended to the request. A pack states facts that an offline lookup could have produced:
  chains and their residue ranges in both numbering schemes, the UniProt mapping, ligand codes
  and atom names, and, where the request names a variant, the residues it maps to. A pack never
  contains a scene, a colour or a representation.
- **`bare`** (three models). The system prompt holds only the instruction and the output
  contract, with no format reference. This measures what a model knows about the format
  unaided.
- **Structured output** (models that support it). As `spec`, with the provider's JSON mode
  switched on. ⟦PENDING: structured-output condition, final run only⟧

No prompt was tuned on benchmark tasks. The worked example in each system prompt is not a
benchmark task. ⟦PENDING: confirm for the rebuilt API prompt⟧

### 5.3 Sampling

The final run draws three samples per task per model at the provider's default temperature.
Every raw output is archived. A malformed output is scored as it stands and is not retried;
only transport errors are retried.

The preliminary panel drew {{mvs.spec.samples_per_task}} sample per task. Its intervals
therefore reflect which tasks and structures were chosen, and not run-to-run variation of a
model.

### 5.4 Cost

Token counts are those reported by the provider. Cost is tokens times list price on the day of
the run. Section 6.8 gives the cost per model.

### 5.5 Reproducibility

One manifest file names the corpus version, the models, the conditions, the samples and the
prices. One command performs the run. One command (`scripts/paper_tables.py`) rebuilds every
table, figure and in-text number of this paper from the archived outputs. A dry run with a mock
model exercises the whole path at no cost.
⟦PENDING: run manifest and dry run (runner work package)⟧
