"""
Grounding packs (ROADMAP R6): the builder is deterministic, the runner sends a pack
only with ``--grounding``, and no pack carries a scene or an instruction.

The builder test needs gemmi (the ``authoring`` extra) and runs offline on a frozen
mmCIF (``tests/data/3ptb.cif.gz``; ``data/cif/`` is an untracked cache).
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import re

import pytest

from molbench import runner
from molbench.runner import load_tasks

REPO = pathlib.Path(__file__).resolve().parent.parent
FIXTURE = pathlib.Path(__file__).resolve().parent / "data" / "3ptb.cif.gz"
SIFTS_3PTB = [{"acc": "P00760", "entity": "1", "name": "TRY1_BOVIN", "regions": [[1, 24, 223]]}]


def _builder():
    pytest.importorskip("gemmi")
    spec = importlib.util.spec_from_file_location(
        "build_grounding_packs", REPO / "scripts" / "build_grounding_packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _packed_tasks():
    return [t for t in load_tasks(["mvs"]) if t.get("grounding")]


def test_pack_builder_is_deterministic_on_a_frozen_cif():
    b = _builder()
    texts = []
    for _ in range(2):
        block, st = b.load(FIXTURE)
        texts.append("\n".join(b.structure_facts("3ptb", block, st,
                                                 b.sifts_segments(SIFTS_3PTB, st))))
    assert texts[0] == texts[1]
    text = texts[0]
    # Both numberings, insertion codes, SIFTS offset, ligand atoms, waters.
    assert "A [A]: entity 1, 223 of 223 SEQRES residues observed" in text
    assert "auth 184A = label 164" in text
    assert "A: P00760 (TRY1_BOVIN) UniProt 24-246 = label 1-223" in text
    assert "BEN (BENZAMIDINE), 1 copy: A 1 [C]; atoms: C1 C2 C3 C4 C5 C6 C N1 N2" in text
    assert "Waters: 62" in text


def test_every_mvs_task_has_a_current_pack():
    b = _builder()
    mvs = load_tasks(["mvs"])
    assert mvs and all(t.get("grounding", {}).get("rule") == b.RULE for t in mvs), \
        "re-run scripts/build_grounding_packs.py"


def test_no_pack_contains_a_scene_or_an_instruction():
    scene = re.compile(r'"kind"|"root"|"children"|"params"|"selector"')
    styling = re.compile(r"\b(cartoon|ball[-_]and[-_]stick|spacefill|surface|representation|"
                         r"component|primitives?|focus|colou?r|red|grey|gray|blue|orange|"
                         r"draw|show|highlight)\b", re.I)
    tasks = _packed_tasks()
    assert tasks
    for t in tasks:
        text = t["grounding"]["text"]
        assert not scene.search(text), t["id"]
        assert not styling.search(text), (t["id"], styling.search(text).group())
        assert len(text) < 6000, f"{t['id']}: pack over ~1.5k tokens"


class _Recorder:
    """A model that records the user messages it is sent and returns no scene."""
    name = "recorder"

    def __init__(self):
        self.usage = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        self.sent: dict[str, tuple[str, str]] = {}   # prompt -> (system, user)

    def generate(self, system, user):
        self.sent[user.split("\n\n", 1)[0]] = (system, user)
        return "{}"


@pytest.mark.parametrize("grounding", [False, True])
def test_runner_sends_the_pack_only_with_grounding(monkeypatch, grounding):
    rec = _Recorder()
    monkeypatch.setattr(runner, "build_model", lambda spec: rec)
    report, _ = runner.run(["rec"], ["mvs", "api_calling"], grounding=grounding)
    meta = report["meta"]
    assert meta["grounding"] is grounding
    tasks = load_tasks(["mvs", "api_calling"])
    systems = runner.build_system_prompts("spec")
    for t in tasks:
        system, sent = rec.sent[t["prompt"]]
        assert system == systems[t["category"]], "the system prompt must not change"
        if grounding and t.get("grounding"):
            assert sent == runner.GROUNDING_TEMPLATE.format(
                prompt=t["prompt"], facts=t["grounding"]["text"])
        else:
            assert sent == t["prompt"]
    if grounding:
        n_with = sum(1 for t in tasks if t.get("grounding"))
        assert meta["n_tasks_with_pack"] == n_with > 0
        assert meta["n_tasks_without_pack"] == len(tasks) - n_with > 0  # api_calling
        assert meta["grounding_rules"] == ["r6-v1"]
    else:
        assert "n_tasks_with_pack" not in meta



def test_user_message_template():
    t = _packed_tasks()[0]
    assert runner.user_message(t, grounding=False) == t["prompt"]
    assert runner.user_message(t, grounding=True) == (
        t["prompt"] + "\n\nFacts about the structures involved:\n" + t["grounding"]["text"])
