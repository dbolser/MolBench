"""
Component 2 (visual-rubric) grading — interface + stub.

The "show the key hydrogen bond in haemoglobin" class of task can't be graded by
comparing action lists: many different action sequences produce an acceptable
image, and many wrong ones produce a superficially similar image. The validation
signal has to come from *looking at the rendered scene*.

Pipeline (when fully wired):

    actions --apply_actions--> live PDBeMolstar --headless snapshot--> PNG
    PNG + rubric --> VLM judge --> per-criterion pass/fail + score

This module defines that interface and ships a deterministic stub so the harness
runs end-to-end today. Swapping in a real judge means implementing ``VLMJudge``.
"""

from __future__ import annotations

from typing import Any, Protocol


class VLMJudge(Protocol):
    def score(self, image_path: str, rubric: list[str], prompt: str) -> dict[str, Any]:
        """Return {'criteria': [{'text', 'passed', 'reason'}...], 'score': float}."""
        ...


class StubVLMJudge:
    """Records the rubric but cannot see an image — always returns 'unscored'.

    Lets visual-rubric tasks flow through the runner (so the corpus is exercised
    and the report is shaped correctly) without pretending to have judged them.
    """

    name = "stub"

    def score(self, image_path: str, rubric: list[str], prompt: str) -> dict[str, Any]:
        return {
            "score": None,
            "status": "unscored",
            "criteria": [{"text": c, "passed": None, "reason": "no VLM judge wired"}
                         for c in rubric],
        }


class AnthropicVLMJudge:
    """Reference implementation sketch: send the PNG + rubric to a vision model.

    Not invoked by default. Requires the ``anthropic`` extra and an image on disk.
    """

    name = "anthropic-vlm"

    def __init__(self, model_id: str = "claude-opus-4-8"):
        self.model_id = model_id

    def score(self, image_path: str, rubric: list[str], prompt: str) -> dict[str, Any]:
        import base64
        import json
        import os
        import anthropic

        with open(image_path, "rb") as fh:
            img_b64 = base64.standard_b64encode(fh.read()).decode()
        criteria = "\n".join(f"{i+1}. {c}" for i, c in enumerate(rubric))
        instruction = (
            f"A user asked a molecular viewer to: {prompt!r}\n"
            f"Judge the rendered image against each criterion. Return JSON: "
            f'{{"criteria":[{{"text":...,"passed":true/false,"reason":...}}]}}.\n'
            f"Criteria:\n{criteria}"
        )
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = client.messages.create(
            model=self.model_id,
            max_tokens=1500,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64",
                                             "media_type": "image/png", "data": img_b64}},
                {"type": "text", "text": instruction},
            ]}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        try:
            start, end = text.index("{"), text.rindex("}") + 1
            data = json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return {"score": None, "status": "parse_error", "raw": text}
        passed = [c for c in data.get("criteria", []) if c.get("passed")]
        data["score"] = len(passed) / len(rubric) if rubric else None
        data["status"] = "scored"
        return data
