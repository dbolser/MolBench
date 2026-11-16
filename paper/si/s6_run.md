## S6. The run manifest

The final run is defined by one manifest file in the repository. Its contents, in words:

- **Corpus.** Version `{{plan.corpus_version}}` ⟦PENDING: corpus freeze — final version tag and hash⟧.
- **Samples.** {{plan.samples}} per task, model and condition (1 in the JSON-mode condition);
  no temperature is sent, so each provider's default applies. Limit on the length of an answer:
  {{plan.max_tokens:,}} tokens; models that reason before answering get a larger limit,
  because the hidden reasoning counts against it.
- **Retries.** Only transport errors are retried. A malformed answer is archived and scored
  as it stands.
- **Conditions.** {{plan.n_conditions}}, as in Section 5.2 of the paper.
- **Budget.** A cap in US dollars; the run refuses to start if the projected cost is above it
  and stops if spending would pass it. Costs are list prices on the day of the run.
- **Validation.** Every parsed scene is validated by Mol\* 5.9.0.

**Table S6. The model panel.** *Panel*: core, or optional (run only if the budget allows;
marked † in the paper). *Weights*: open if the model's weights can be downloaded. *Hidden
reasoning*: the model spends reasoning tokens by default, billed as output. *JSON mode*: the
provider offers an option that forces syntactically valid JSON on the route used. *List
price*: US dollars per million input / output tokens, read on the date given.
⟦PENDING: final run — the version string each provider reports, and the dates of the calls⟧

{{include:generated/si_models.md}}
