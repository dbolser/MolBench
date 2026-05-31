"""
Model adapters — the 'plug a model into the benchmark' layer.

Every model implements one method::

    generate(system: str, user: str) -> str   # returns the model's raw text

The runner is responsible for extracting JSON from that text, so adapters stay
dumb and uniform. Three kinds ship here:

* ``BaselineModel`` — a keyless, rule-based NL->actions parser. It is deliberately
  simple and *not good*; its job is to (a) make the whole harness runnable with
  zero credentials and (b) provide a non-trivial score floor that real models must
  beat. Reporting a baseline is standard benchmark hygiene.
* ``AnthropicModel`` / ``OpenAIModel`` — thin wrappers that lazy-import their SDKs
  so importing this module never requires them.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any


class Model:
    """Common interface.

    Also carries a token-usage tally so the runner can report cost. Subclasses that
    call a paid API record tokens via ``_record``; the baseline leaves it at zero.
    """

    name: str = "abstract"

    def __init__(self) -> None:
        self.usage = {"input_tokens": 0, "output_tokens": 0, "calls": 0}

    def _record(self, input_tokens: int, output_tokens: int) -> None:
        self.usage["input_tokens"] += int(input_tokens or 0)
        self.usage["output_tokens"] += int(output_tokens or 0)
        self.usage["calls"] += 1

    def generate(self, system: str, user: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


# --- keyless baseline -------------------------------------------------------------

# A small, transparent dictionary the baseline uses. Real models are expected to
# know far more (and to reason about residue numbers); this is just a floor.
_PDB_HINTS = {
    "hiv": "1hvr", "hiv-1 protease": "1hvr", "protease": "1hvr",
    "haemoglobin": "1hho", "hemoglobin": "1hho",
    "lysozyme": "1lyz", "myoglobin": "1mbn", "insulin": "4ins",
}
_HIDE_WORDS = {
    "water": "hide_water", "waters": "hide_water",
    "ligand": "hide_heteroatoms", "heteroatom": "hide_heteroatoms",
    "carbohydrate": "hide_carbs", "sugar": "hide_carbs",
}
_STYLE_WORDS = {
    "cartoon": "cartoon", "surface": "molecular-surface",
    "molecular surface": "molecular-surface", "gaussian": "gaussian-surface",
    "ball-and-stick": "ball-and-stick", "ball and stick": "ball-and-stick",
    "spacefill": "spacefill", "space-fill": "spacefill", "putty": "putty",
}


class BaselineModel(Model):
    name = "baseline-rules"

    def generate(self, system: str, user: str) -> str:
        text = user.lower()
        actions: list[dict[str, Any]] = []

        # explicit 4-char PDB id wins; otherwise fall back to name hints.
        m = re.search(r"\b([1-9][a-z0-9]{3})\b", text)
        pdb = m.group(1) if m else next(
            (pid for kw, pid in _PDB_HINTS.items() if kw in text), None
        )
        if pdb or "load" in text or "show me the structure" in text:
            actions.append({"action": "load", "molecule_id": pdb or "1hho"})

        for kw, style in _STYLE_WORDS.items():
            if kw in text:
                actions.append({"action": "set_visual_style", "style": style})
                break
        for kw, prop in _HIDE_WORDS.items():
            if f"hide {kw}" in text or f"remove {kw}" in text or f"no {kw}" in text:
                actions.append({"action": "set_property", "name": prop, "value": True})
        if "spin" in text or "rotate" in text:
            actions.append({"action": "set_property", "name": "spin", "value": True})
        if "white background" in text:
            actions.append({"action": "set_property", "name": "bg_color", "value": "#FFFFFF"})

        return json.dumps(actions)


# --- live model adapters ----------------------------------------------------------

class AnthropicModel(Model):
    def __init__(self, model_id: str = "claude-opus-4-8", max_tokens: int = 2000):
        super().__init__()
        self.name = model_id
        self.model_id = model_id
        self.max_tokens = max_tokens

    def generate(self, system: str, user: str) -> str:
        import anthropic  # lazy: only needed when this model is actually used
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = client.messages.create(
            model=self.model_id,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        self._record(resp.usage.input_tokens, resp.usage.output_tokens)
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


class OpenAIModel(Model):
    """Talks to any OpenAI-compatible endpoint.

    OpenAI, OpenRouter, Together, Groq, DeepInfra and local Ollama/vLLM all expose
    the same ``/chat/completions`` wire format, so we cover them all with one class
    by varying ``base_url`` and which env var holds the key. That's why adding e.g.
    Qwen-via-OpenRouter is a spec string, not a new adapter.
    """

    def __init__(self, model_id: str = "gpt-4o", *,
                 api_key_env: str = "OPENAI_API_KEY",
                 base_url: str | None = None,
                 base_url_env: str = "OPENAI_BASE_URL",
                 max_tokens: int = 2000):
        super().__init__()
        self.name = model_id
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.api_key_env = api_key_env
        # explicit base_url wins; else an env override (for OpenAI-compatible hosts);
        # else None, which makes the SDK use api.openai.com.
        self.base_url = base_url or os.environ.get(base_url_env)

    def generate(self, system: str, user: str) -> str:
        from openai import OpenAI  # lazy import
        client = OpenAI(api_key=os.environ[self.api_key_env], base_url=self.base_url)
        resp = client.chat.completions.create(
            model=self.model_id,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        if resp.usage:  # OpenAI-compatible hosts may omit usage; guard for it
            self._record(resp.usage.prompt_tokens, resp.usage.completion_tokens)
        return resp.choices[0].message.content or ""


# Registry the CLI resolves --models against. A "spec" is 'provider:model-id'
# (or the bare word 'baseline'). Keeping providers as data here means adding one
# is a couple of lines; see README "Adding a provider".
def build_model(spec: str) -> Model:
    """Resolve a spec string to a Model.

    Supported:
      baseline                              keyless rule-based floor
      anthropic:<id>                        e.g. anthropic:claude-opus-4-8         (ANTHROPIC_API_KEY)
      openai:<id>                           e.g. openai:gpt-4o                     (OPENAI_API_KEY)
      openrouter:<vendor>/<id>              e.g. openrouter:qwen/qwen-2.5-72b-instruct (OPENROUTER_API_KEY)

    For any other OpenAI-compatible host (Together, Groq, local Ollama/vLLM), use
    the openai: provider and set OPENAI_BASE_URL (+ OPENAI_API_KEY) in your .env.
    """
    if spec in ("baseline", "baseline-rules"):
        return BaselineModel()
    if ":" in spec:
        provider, model_id = spec.split(":", 1)
        if provider == "anthropic":
            return AnthropicModel(model_id)
        if provider == "openai":
            return OpenAIModel(model_id)
        if provider == "openrouter":
            return OpenAIModel(model_id, api_key_env="OPENROUTER_API_KEY",
                               base_url="https://openrouter.ai/api/v1")
        if provider in ("gemini", "google"):
            # Google's OpenAI-compatibility layer — same OpenAIModel, different host.
            return OpenAIModel(model_id, api_key_env="GEMINI_API_KEY",
                               base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    raise ValueError(
        f"unknown model spec {spec!r}. Use 'baseline', 'anthropic:<id>', "
        "'openai:<id>', 'openrouter:<vendor>/<id>', or 'gemini:<id>'."
    )
