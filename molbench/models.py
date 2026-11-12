"""
Model adapters — the 'plug a model into the benchmark' layer.

Every model implements one method::

    generate(system: str, user: str) -> str   # returns the model's raw text

The runner is responsible for extracting JSON from that text, so adapters stay
dumb and uniform. The manifest runner calls ``complete(...)`` instead, which returns
the text *plus* what a run archive needs: token usage, finish reason, latency. Four
kinds ship here:

* ``BaselineModel`` — a keyless, rule-based NL->actions parser. It is deliberately
  simple and *not good*; its job is to (a) make the whole harness runnable with
  zero credentials and (b) provide a non-trivial score floor that real models must
  beat. Reporting a baseline is standard benchmark hygiene.
* ``AnthropicModel`` / ``OpenAIModel`` — thin wrappers that lazy-import their SDKs
  so importing this module never requires them.
* ``MockModel`` — a deterministic stand-in for any model, used by ``--dry-run`` to
  exercise the whole pipeline at zero cost.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class Completion:
    """One model call, with everything the run archive records about it."""
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str | None = None     # provider's own word: stop / length / end_turn / ...
    latency_s: float | None = None
    reasoning_tokens: int | None = None  # part of output_tokens, when the provider says
    response_model: str | None = None    # the model the provider says answered
    response_id: str | None = None
    cost_usd: float | None = None        # only when the provider reports it (OpenRouter)


class Model:
    """Common interface.

    Also carries a token-usage tally so the runner can report cost. Subclasses that
    call a paid API record tokens via ``_record``; the baseline leaves it at zero.
    """

    name: str = "abstract"

    def __init__(self) -> None:
        self.usage = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        self._usage_lock = threading.Lock()

    def _record(self, input_tokens: int, output_tokens: int) -> None:
        with self._usage_lock:
            self.usage["input_tokens"] += int(input_tokens or 0)
            self.usage["output_tokens"] += int(output_tokens or 0)
            self.usage["calls"] += 1

    def generate(self, system: str, user: str) -> str:
        """The model's raw text. Adapters implement ``complete``; this is the short form."""
        return self.complete(system, user).text

    def complete(self, system: str, user: str, *, max_tokens: int | None = None,
                 structured: str | None = None, timeout: float | None = None,
                 context: dict | None = None) -> Completion:
        """One call. ``structured`` asks the provider for JSON mode (``"json_object"``);
        ``context`` carries the task for the mock model and is ignored by real ones.

        The default wraps a subclass that only defines ``generate`` (the baseline, test
        doubles), timing it and reporting no token usage.
        """
        if type(self).generate is Model.generate:
            raise NotImplementedError("a Model defines generate() or complete()")
        started = time.perf_counter()
        text = self.generate(system, user)
        return Completion(text=text, input_tokens=0, output_tokens=0, finish_reason="stop",
                          latency_s=round(time.perf_counter() - started, 3))


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
        self._clients: dict = {}

    def _client(self, timeout: float | None):
        import anthropic  # lazy: only needed when this model is actually used
        if timeout not in self._clients:
            kw = {} if timeout is None else {"timeout": timeout, "max_retries": 0}
            self._clients[timeout] = anthropic.Anthropic(
                api_key=os.environ["ANTHROPIC_API_KEY"], **kw)
        return self._clients[timeout]

    def complete(self, system: str, user: str, *, max_tokens: int | None = None,
                 structured: str | None = None, timeout: float | None = None,
                 context: dict | None = None) -> Completion:
        if structured:
            # Not wired for the native route (it would need output_config.format with a
            # full JSON schema). Mark the model structured = "none" in the manifest.
            raise ValueError("structured output is not supported on the anthropic: route")
        started = time.perf_counter()
        resp = self._client(timeout).messages.create(
            model=self.model_id,
            max_tokens=max_tokens or self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        latency = time.perf_counter() - started
        self._record(resp.usage.input_tokens, resp.usage.output_tokens)
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        return Completion(text=text, input_tokens=resp.usage.input_tokens,
                          output_tokens=resp.usage.output_tokens,
                          finish_reason=resp.stop_reason, latency_s=round(latency, 3),
                          response_model=getattr(resp, "model", None),
                          response_id=getattr(resp, "id", None))


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
                 max_tokens: int = 2000, report_cost: bool = False):
        super().__init__()
        self._clients: dict = {}
        self.report_cost = report_cost
        self.name = model_id
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.api_key_env = api_key_env
        # explicit base_url wins; else an env override (for OpenAI-compatible hosts);
        # else None, which makes the SDK use api.openai.com.
        self.base_url = base_url or os.environ.get(base_url_env)

    def _client(self, timeout: float | None):
        from openai import OpenAI  # lazy import
        if timeout not in self._clients:
            kw = {} if timeout is None else {"timeout": timeout, "max_retries": 0}
            self._clients[timeout] = OpenAI(api_key=os.environ[self.api_key_env],
                                            base_url=self.base_url, **kw)
        return self._clients[timeout]

    def complete(self, system: str, user: str, *, max_tokens: int | None = None,
                 structured: str | None = None, timeout: float | None = None,
                 context: dict | None = None) -> Completion:
        client = self._client(timeout)
        max_tokens = max_tokens or self.max_tokens
        base: dict[str, Any] = dict(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        if structured == "json_object":
            base["response_format"] = {"type": "json_object"}
        elif structured:
            raise ValueError(f"unknown structured-output mode {structured!r}")
        if self.report_cost:
            # OpenRouter usage accounting: adds the billed cost to resp.usage.
            base["extra_body"] = {"usage": {"include": True}}
        # gpt-5 / o-series reject `max_tokens` and require `max_completion_tokens`;
        # older models and most OpenAI-compatible hosts want `max_tokens`. Try the
        # common one, fall back on the newer spelling — one adapter, both worlds.
        started = time.perf_counter()
        try:
            resp = client.chat.completions.create(max_tokens=max_tokens, **base)
        except Exception as e:  # noqa: BLE001 - inspect the API error to retry
            if "max_completion_tokens" not in str(e):
                raise
            started = time.perf_counter()
            resp = client.chat.completions.create(max_completion_tokens=max_tokens, **base)
        latency = time.perf_counter() - started
        out = Completion(text="", latency_s=round(latency, 3),
                         response_model=getattr(resp, "model", None),
                         response_id=getattr(resp, "id", None))
        usage = resp.usage
        if usage:  # OpenAI-compatible hosts may omit usage; guard for it
            self._record(usage.prompt_tokens, usage.completion_tokens)
            out.input_tokens, out.output_tokens = usage.prompt_tokens, usage.completion_tokens
            details = getattr(usage, "completion_tokens_details", None)
            out.reasoning_tokens = getattr(details, "reasoning_tokens", None)
            cost = getattr(usage, "cost", None)
            out.cost_usd = float(cost) if isinstance(cost, (int, float)) else None
        if resp.choices:
            out.text = resp.choices[0].message.content or ""
            out.finish_reason = resp.choices[0].finish_reason
        return out


# --- deterministic mock (dry runs) ------------------------------------------------

# What the mock answers with, and how often (per 100 calls). Chosen so that a dry run
# meets every outcome class the grader and the scorecard have to handle.
MOCK_MIX = (("reference", 46), ("fenced", 8), ("perturbed", 22), ("truncated", 8),
            ("malformed", 4), ("prose", 4), ("wrong_shape", 4), ("empty", 4))


def _first_color(node: Any) -> dict | None:
    """The first dict in a JSON tree that carries a 'color' value."""
    if isinstance(node, dict):
        if "color" in node:
            return node
        node = list(node.values())
    if isinstance(node, list):
        for child in node:
            hit = _first_color(child)
            if hit is not None:
                return hit
    return None


def perturb_reference(ref: Any) -> Any:
    """A near-miss of a reference answer: one colour changed, or the last step dropped.

    Still well-formed, so it exercises partial credit rather than the failure paths.
    """
    out = copy.deepcopy(ref)
    hit = _first_color(out)
    if hit is not None:
        hit["color"] = ({"r": 1, "g": 2, "b": 3} if isinstance(hit["color"], dict)
                        else "#010203")
        return out
    if isinstance(out, list) and len(out) > 1:
        return out[:-1]
    # No colour to change: drop the last branch of the tree (or, in a tree that is a
    # single chain, its last node).
    node = out.get("root", out) if isinstance(out, dict) else None
    parent = None
    while isinstance(node, dict) and node.get("children"):
        if len(node["children"]) > 1:
            node["children"].pop()
            return out
        parent, node = node, node["children"][0]
    if parent is not None:
        parent["children"].pop()
    return out


def malform_reference(ref: Any) -> Any:
    """Well-formed JSON of the right outer shape that the viewer would reject: an MVS
    tree with a node under a parent that cannot hold it, or an action list with an
    action that does not exist."""
    out = copy.deepcopy(ref)
    if isinstance(out, list):
        return out + [{"action": "no_such_action"}]
    root = out.get("root", out) if isinstance(out, dict) else None
    if isinstance(root, dict):
        root.setdefault("children", []).insert(
            0, {"kind": "representation", "params": {"type": "cartoon"}})
    return out


class MockModel(Model):
    """Stands in for a named model. Deterministic: the same (seed, model, condition,
    task, sample) always gives the same reply, so a dry run is reproducible and a
    resumed dry run is indistinguishable from an uninterrupted one.

    It reads the task's reference from ``context`` - the one thing a real model never
    sees - and returns it intact, perturbed, or broken, in the `MOCK_MIX` proportions.
    Token counts are estimates from the text lengths; it costs nothing.
    """

    is_mock = True

    def __init__(self, name: str = "mock", seed: int = 0,
                 chars_per_input_token: float = 4.0, chars_per_output_token: float = 4.0):
        super().__init__()
        self.name = name
        self.seed = seed
        self.cpt_in = chars_per_input_token
        self.cpt_out = chars_per_output_token

    def _choice(self, key: str) -> str:
        roll = int(hashlib.sha256(f"{self.seed}|{self.name}|{key}".encode()).hexdigest(), 16) % 100
        for kind, weight in MOCK_MIX:
            if roll < weight:
                return kind
            roll -= weight
        return MOCK_MIX[0][0]

    def reply(self, task: dict, key: str, wrap_actions: bool = False) -> tuple[str, str, str]:
        """(kind, text, finish_reason) for one call."""
        ref = task.get("reference_mvs", task.get("reference"))
        is_api = isinstance(ref, list)
        kind = self._choice(key) if ref is not None else "prose"
        answer = (perturb_reference(ref) if kind == "perturbed"
                  else malform_reference(ref) if kind == "malformed" else ref)
        if wrap_actions and is_api:
            answer = {"actions": answer}
        good = json.dumps(answer, indent=1)
        if kind in ("reference", "perturbed", "malformed"):
            return kind, good, "stop"
        if kind == "fenced":
            return kind, f"```json\n{good}\n```", "stop"
        if kind == "truncated":  # cut mid-structure, as when the token limit is hit
            return kind, good[: max(1, len(good) * 2 // 3)], "length"
        if kind == "wrong_shape":  # valid JSON, but not a scene tree / action list
            return kind, json.dumps({"answer": "see above"} if not is_api else [1, 2, 3]), "stop"
        if kind == "empty":
            return kind, "", "stop"
        return "prose", "I am not able to produce that visualization.", "stop"

    def complete(self, system: str, user: str, *, max_tokens: int | None = None,
                 structured: str | None = None, timeout: float | None = None,
                 context: dict | None = None) -> Completion:
        context = context or {}
        task = context.get("task") or {}
        key = "|".join(str(context.get(k)) for k in ("condition", "task_id", "sample"))
        _, text, finish = self.reply(task, key, wrap_actions=bool(structured))
        inp = round((len(system) + len(user)) / self.cpt_in)
        out = round(len(text) / self.cpt_out)
        self._record(inp, out)
        return Completion(text=text, input_tokens=inp, output_tokens=out, finish_reason=finish,
                          latency_s=0.0, response_model=f"mock:{self.name}",
                          response_id="mock-" + hashlib.sha256(
                              f"{self.name}|{key}".encode()).hexdigest()[:12])


# Registry the CLI resolves --models against. A "spec" is 'provider:model-id'
# (or the bare word 'baseline'). Keeping providers as data here means adding one
# is a couple of lines; see README "Adding a provider".
def build_model(spec: str) -> Model:
    """Resolve a spec string to a Model.

    Supported:
      baseline                              keyless rule-based floor
      mock:<name>                           deterministic stand-in, zero cost (dry runs)
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
        if provider == "mock":
            return MockModel(model_id)
        if provider == "anthropic":
            return AnthropicModel(model_id)
        if provider == "openai":
            return OpenAIModel(model_id)
        if provider == "openrouter":
            return OpenAIModel(model_id, api_key_env="OPENROUTER_API_KEY",
                               base_url="https://openrouter.ai/api/v1", report_cost=True)
        if provider in ("gemini", "google"):
            # Google's OpenAI-compatibility layer — same OpenAIModel, different host.
            return OpenAIModel(model_id, api_key_env="GEMINI_API_KEY",
                               base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    raise ValueError(
        f"unknown model spec {spec!r}. Use 'baseline', 'anthropic:<id>', "
        "'openai:<id>', 'openrouter:<vendor>/<id>', or 'gemini:<id>'."
    )
