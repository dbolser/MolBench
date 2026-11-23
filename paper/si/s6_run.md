## S6. The run manifest

The final run is defined by one manifest file in the repository. Its contents, in words:

- **Corpus.** Version `{{plan.corpus_version}}` ⟦PENDING: corpus freeze — final version tag and hash⟧.
- **Answers.** Each model gives {{plan.samples:word}} answers per task and condition (one in the JSON-mode condition);
  no temperature is sent, so each provider's default applies. Limit on the length of an answer:
  {{plan.max_tokens:,}} tokens. Models that write reasoning text before the answer, which the
  user does not see, get {{plan.reasoning_max_tokens:,}} tokens for reasoning and answer
  together, because the provider counts the reasoning against the limit.
- **Retries.** Only transport errors are retried. An invalid answer is archived and scored
  as it stands.
- **Conditions.** {{plan.n_conditions}}, as in Section 5.2 of the paper.
- **Budget.** A cap in US dollars; the run refuses to start if the projected cost is above it
  and stops if spending would pass it. Costs are list prices on the day of the run.
- **Validation.** Every parsed scene is validated by Mol\* 5.9.0.

**Table S7. The models.** *Set*: core, or optional (run only if decided so before the run,
from the projected cost; marked † in the paper). Identifiers are given as the provider or
the routing service lists them; the paper uses the part after the slash. *Provider*: the company that publishes the model, as the identifier or the route names it. *Weights*: open if the model's weights can be downloaded, closed if the model can be used only through a provider's service. *Hidden
reasoning*: by default the model first writes reasoning text that the user does not see; the
provider bills it as output and counts it against the limit on the length of the answer. *JSON mode*: the
provider offers an option that forces syntactically valid JSON on the route used. *List
price*: US dollars per million input / output tokens, read on the date given.
⟦PENDING: final run — the version string each provider reports, and the dates of the calls⟧

{{include:generated/si_models.md}}

### S6.1 Provider pilot

Before the final run, the path from the manifest to a provider and back to a graded answer
was tried once, on a few tasks of the present corpus and with one model of the core set. We
call this the *provider pilot*. It is not the pilot run of October 2026 (Section 6.6 of the
paper), and it is not a result of the benchmark. Every answer of the provider pilot that
was not counted as a task success was read. This showed faults of the benchmark itself,
which were corrected before the corpus was frozen: among them, wrong answers that had been
graded as right (a file address that does not exist; a PDB identifier in upper case on the
call-list track) and a second representation of the same type that the viewer does not show
(Sections S4.5 and S4.6). No request and no reference changed. The table below gives the
answers as graded after the corrections.

{{include:generated/pilot_results.md}}
