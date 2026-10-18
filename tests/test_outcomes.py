"""Outcome classes for MVS samples: why a scene scored what it did.

Mol* is stubbed (``molstar_issues``) so this runs without a browser.
"""

import json

from molbench import render, runner

REF = {"kind": "root", "children": [{"kind": "download",
       "params": {"url": "https://files.rcsb.org/download/1cbs.cif"}}]}
TASK = {"id": "t", "category": "mvs", "prompt": "p", "reference_mvs": REF}


class Echo:
    """A model that returns a fixed reply."""
    name = "echo"

    def __init__(self, reply):
        self.reply = reply

    def generate(self, system, user):
        return self.reply


def _sample(reply):
    return runner.run_mvs_task(Echo(reply), "", TASK)


def test_parse_outcomes():
    assert _sample("{not json")["outcome"] == "invalid_json"
    assert _sample('{"kind": "component"}')["outcome"] == "not_mvs"
    assert _sample(json.dumps(REF))["outcome"] == "valid"


def test_molstar_rejection_scores_zero_and_keeps_the_message(monkeypatch):
    msg = 'Node of kind "focus" cannot appear as a child of "structure".'
    good, bad = _sample(json.dumps(REF)), _sample(json.dumps(REF))
    monkeypatch.setattr(render, "molstar_issues",
                        lambda scenes: [[], [msg]][:len(scenes)])
    runner.validate_samples([good, bad])
    assert good["outcome"] == "valid" and good["f1"] == 1.0
    assert bad["outcome"] == "invalid_mvs" and bad["f1"] == 0.0
    assert bad["mvs_issues"] == [msg]


def test_only_parsed_scenes_go_to_molstar(monkeypatch):
    seen = []
    monkeypatch.setattr(render, "molstar_issues",
                        lambda scenes: seen.extend(scenes) or [[] for _ in scenes])
    runner.validate_samples([_sample("{not json"), _sample(json.dumps(REF))])
    assert len(seen) == 1


def test_format_stats_counts_outcomes_and_conditions_on_valid():
    valid, broken = _sample(json.dumps(REF)), _sample("{not json")
    rejected = _sample(json.dumps(REF))
    runner._invalidate(rejected, "invalid_mvs", ["bad"])
    stats = runner._format_stats({"a": [valid], "b": [broken], "c": [rejected]})
    assert stats["outcomes"] == {"valid": 1, "invalid_json": 1, "not_mvs": 0,
                                 "invalid_mvs": 1, "load_failed": 0}
    assert stats["valid_scene"] == round(1 / 3, 4)
    assert stats["parse_success"] == round(2 / 3, 4)  # JSON parsed, whatever Mol* says
    assert stats["cond_f1"] == 1.0                   # over scenes Mol* can show


def test_archives_never_overwrite(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "RUNS_DIR", tmp_path)
    paths = {runner._new_archive_path() for _ in range(3)}
    assert len(paths) == 3 and all(p.exists() for p in paths)
