## S6. The run manifest

The final run is defined by one manifest file in the repository. Its contents, in words:

- **Corpus.** Version `{{plan.corpus_version}}` ⟦PENDING: corpus freeze — final version tag and hash⟧.
- **Answers.** {{plan.samples:word}} per task, model and condition (one in the JSON-mode condition);
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
