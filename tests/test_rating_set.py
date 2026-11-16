"""The a4-v2 rating set (scripts/build_rating_set.py): sampling, order, checks, and what
is public. Pictures come from a stand-in renderer; no browser, no network."""

import collections
import hashlib
import importlib.util
import json
import pathlib
import subprocess

import pytest

pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rs = _load("build_rating_set")
SECRET = "ab" * 32


class FakeRenderer:
    """A flat picture whose colour is a hash of the scene: equal scenes give equal
    pictures, different scenes different ones. A scene marked ``_fail`` cannot be drawn."""

    def __init__(self, d: pathlib.Path):
        self.d, self.n = d, 0

    def _png(self, scene, view) -> str:
        if scene.get("_fail"):
            raise RuntimeError("render failed: stand-in")
        h = hashlib.sha256(json.dumps(scene, sort_keys=True).encode()).digest()
        self.n += 1
        path = self.d / f"{self.n}-{view}.png"
        im = Image.new("RGB", (40, 30), "white")
        im.paste((h[0], h[1], h[2] // 2), (10, 8, 30, 22))
        im.save(path)
        return str(path)

    def ref(self, scene, rows):
        return {"whole": self._png(scene, "whole"), "whole_camera": {"c": 1},
                "target": self._png(scene, "target") if rows else None,
                "target_camera": {"c": 2} if rows else None, "framed": None}

    def answer(self, scene, ref):
        return {"whole": self._png(scene, "whole"),
                "target": self._png(scene, "target") if ref["target_camera"] else None}


@pytest.fixture(scope="module")
def corpus():
    from molbench import tasks
    return {t["id"]: t for t in tasks.load_corpus()}


def _sample(task, model, n, success, target_f1, predicted=None, outcome="valid"):
    return {"model": model, "task_id": task["id"], "sample": n, "track": task["track"], "tier": task["tier"],
            "split": task["split"], "outcome": outcome, "success": success, "target_f1": target_f1,
            "f1": 1.0 if success else 0.5, "matched_reference": 0,
            "predicted": predicted if predicted is not None else task["reference"]}


@pytest.fixture(scope="module")
def run(corpus):
    """A mock run: 10 models x 3 samples on 10 MVS tasks of each tier (and some API,
    resolve and invalid answers that must be left out), classes by a fixed pattern."""
    by_tier = collections.defaultdict(list)
    for t in sorted(corpus.values(), key=lambda t: t["id"]):
        if t["track"] == "mvs" and t.get("target") and len(by_tier[t["tier"]]) < 10:
            by_tier[t["tier"]].append(t)
    out = []
    for tier, ts in sorted(by_tier.items()):
        for i, t in enumerate(ts):
            for m in range(10):
                for n in range(3):
                    kind = (i + m) % 3
                    out.append(_sample(t, f"lab/model-{m}", n, kind == 0, 1.0 if kind < 2 else 0.2,
                                       predicted={**t["reference"], "_variant": [m, kind]}))
    api = next(t for t in corpus.values() if t["track"] == "api")
    out.append(_sample(api, "lab/model-0", 0, True, 1.0))
    out.append({**out[0], "sample": 7, "outcome": "invalid_json", "predicted": None})
    return out


def build(run, corpus, tmp_path, **kw):
    return rs.build_v2(run, corpus, "a4-test", SECRET, FakeRenderer(tmp_path), log=lambda *_: None,
                       **{"n_pairs": 60, "n_checks": 3, **kw})


def test_grader_class():
    assert rs.grader_class({"success": True, "target_f1": 0.0}) == "right"
    assert rs.grader_class({"success": False, "target_f1": 1.0}) == "close"
    assert rs.grader_class({"success": False, "target_f1": 0.99}) == "wrong"
    assert rs.grader_class({"success": False, "target_f1": None}) == "wrong"   # no target: cannot be close


def test_frame_leaves_out_what_has_no_picture(run, corpus):
    kept, why = rs.frame(run, corpus)
    assert all(s["track"] == "mvs" and s["tier"] != "resolve" and s["outcome"] == "valid" for s in kept)
    assert why["API track (no picture of a call list)"] == 1
    assert why["no scene to draw (invalid_json)"] == 1
    assert any(k.startswith("tier resolve") for k in why)


def test_sample_is_stratified_capped_and_stable(run, corpus, tmp_path):
    items, key = build(run, corpus, tmp_path)
    pairs = [v for v in key["items"].values() if v["kind"] == "pair"]
    assert len(pairs) == 60 and len(key["order"]) == 60
    assert collections.Counter(v["grader_class"] for v in pairs) == {"right": 20, "close": 20, "wrong": 20}
    # one sample per task and model; at most 2 per task; no model above its share
    assert len({(v["task"], v["model"]) for v in pairs}) == 60
    assert max(collections.Counter(v["base_task"] for v in pairs).values()) <= 2
    assert max(collections.Counter(v["model"] for v in pairs).values()) <= int(0.12 * 60)
    # tiers share each class about evenly
    per = collections.Counter((v["grader_class"], v["tier"]) for v in pairs)
    for cls in rs.CLASSES:
        ns = [n for (c, _), n in per.items() if c == cls]
        assert max(ns) - min(ns) <= 1
    # the same key gives the same set and order; another key gives other ids
    again = build(run, corpus, tmp_path)[1]
    assert again["order"] == key["order"]
    other = rs.build_v2(run, corpus, "a4-test", "cd" * 32, FakeRenderer(tmp_path), n_pairs=60, n_checks=0,
                        log=lambda *_: None)[1]
    assert not set(other["order"]) & set(key["order"])


def test_model_share_is_a_cap(run, corpus, tmp_path):
    key = build(run, corpus, tmp_path, n_pairs=40, model_share=0.25, n_checks=0)[1]
    assert max(collections.Counter(v["model"] for v in key["items"].values()).values()) <= 10


def test_every_prefix_of_the_order_is_balanced(run, corpus, tmp_path):
    key = build(run, corpus, tmp_path, n_checks=0)[1]
    cells = collections.Counter((v["grader_class"], v["tier"]) for v in key["items"].values())
    for cut in (len(cells), 2 * len(cells), 30):
        seen = collections.Counter((key["items"][i]["grader_class"], key["items"][i]["tier"]) for i in key["order"][:cut])
        for cell, total in cells.items():
            assert abs(seen[cell] - cut * total / 60) <= 1, (cut, cell)


def test_an_answer_that_cannot_be_drawn_is_replaced(run, corpus, tmp_path):
    first = build(run, corpus, tmp_path, n_checks=0)[1]
    victim = first["items"][first["order"][0]]
    broken = [{**s, "predicted": {**s["predicted"], "_fail": True}}
              if (s["task_id"], s["model"]) == (victim["task"], victim["model"]) else s for s in run]
    key = build(broken, corpus, tmp_path, n_checks=0)[1]
    pairs = list(key["items"].values())
    assert len(pairs) == 60 and (victim["task"], victim["model"]) not in {(v["task"], v["model"]) for v in pairs}
    assert [f["task"] for f in key["sample"]["answers_not_drawn"]] == [victim["task"]]


def test_checks_have_a_known_answer_the_pictures_bear_out(run, corpus, tmp_path):
    items, key = build(run, corpus, tmp_path)
    checks = {i: v for i, v in key["items"].items() if v["kind"] != "pair"}
    assert collections.Counter(v["kind"] for v in checks.values()) == dict.fromkeys(rs.CHECK_KINDS, 3)
    by_id = {it["id"]: it for it in items}
    for i, v in checks.items():
        img = by_id[i]["_img"]
        share = rs.differing_share(img["ref"], img["out"])
        if v["kind"] == "check-same":
            assert v["expected"] == "same" and share == 0
        else:
            assert v["expected"] == "different" and share > 0
        if v["kind"] == "check-calibrated":
            assert ":" in v["change"]
        if v["kind"] == "check-different":
            assert set(corpus[v["task"]]["structures"]).isdisjoint(corpus[v["other_task"]]["structures"])


def test_a_calibrated_change_is_one_the_grader_fails(corpus):
    from molbench import runner
    task = corpus["clin-short-target-ins-6tc2-v42a-mvs"]
    what, scene = next(rs.calibrated_variants(task["reference"]))
    assert what == "color: purple -> orange" and scene != task["reference"]
    res = runner.grade_parsed(task, scene)
    assert res["success"] is False and res["target_f1"] < 1.0
    assert runner.grade_parsed(task, task["reference"])["success"] is True   # the original is untouched


def test_target_rows_are_the_task_target(corpus):
    task = corpus["clin-short-target-ins-6tc2-v42a-mvs"]
    from molbench import tasks
    table = tasks.table_for("6tc2")
    rows = rs.target_rows_of(task)
    mask = table.selector(task["target"][0]["selector"])
    assert rows and sum(1 << r for r in rows) == mask
    assert rs.target_rows_of({**task, "target": None}) is None


def test_public_files_hold_nothing_but_ids_prompts_and_pictures(run, corpus, tmp_path):
    items, key = build(run, corpus, tmp_path)
    out, key_path = tmp_path / "public", tmp_path / "private" / "key.json"
    rs.write_v2(items, key, out, key_path)
    public = json.loads((out / "items.json").read_text())
    assert public["design"] == "v2" and public["goal"] == 35 and set(public["questions"]) == {"whole", "target"}
    allowed = {"id", "prompt", "note", "ref", "out", "ref_target", "out_target", "start"}
    assert all(set(it) <= allowed for it in public["items"])
    assert [it["id"] for it in public["items"]] == sorted(key["items"])   # order tells nothing
    text = (out / "items.json").read_text()
    for word in ("model-", "check", "right", "close", "wrong", SECRET, "success"):
        assert word not in text.replace("Something extra", "").replace("request leaves open", ""), word
    assert all((out / it[k]).exists() for it in public["items"] for k in ("ref", "out"))
    # follow-ups show the scene before the request
    fu = [it for it in public["items"] if "start" in it]
    assert fu and all(corpus[key["items"][it["id"]]["task"]]["tier"] == "followup" and "note" in it for it in fu)
    # private: key, serving plan, review sheets
    seed = (key_path.parent / "seed_rating_items.sql").read_text()
    assert seed.count("'pair'") == 60 and seed.count("'check-") == 9
    order = [line.split("'")[3] for line in seed.splitlines() if "'pair'" in line]
    assert order == key["order"]
    assert (key_path.parent / "review" / "index.tsv").read_text().count("\n") == len(items) + 1
    assert oct(key_path.stat().st_mode & 0o777) == "0o600"


def test_the_key_must_be_out_of_gits_reach(run, corpus, tmp_path):
    assert rs.private_place(tmp_path / "anywhere" / "key.json")
    assert rs.private_place(REPO / "results" / "a4" / "a4-v2" / "key.json")      # git-ignored
    assert not rs.private_place(REPO / "paper" / "a4" / "key.json")              # one `git add` from public
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    items, key = build(run, corpus, tmp_path, n_pairs=6, n_checks=0)
    with pytest.raises(SystemExit, match="not ignored"):
        rs.write_v2(items, key, tmp_path / "public2", repo / "key.json")


def test_common_box_is_shared_and_keeps_the_shape(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    for path, box in ((a, (300, 250, 360, 290)), (b, (420, 300, 470, 340))):
        im = Image.new("RGB", (800, 600), "white")
        im.paste((200, 0, 0), box)
        im.save(path)
    box = rs.common_box([str(a), str(b)])
    x0, y0, x1, y1 = box
    assert x0 <= 300 and y0 <= 250 and x1 >= 470 and y1 >= 340           # holds both drawings
    assert abs((x1 - x0) / (y1 - y0) - 800 / 600) < 0.02                  # the picture's own shape
    assert (x1 - x0) >= 400                                               # never blown up more than twice
    blank = tmp_path / "blank.png"
    Image.new("RGB", (800, 600), "white").save(blank)
    assert rs.common_box([str(blank)]) is None


def test_judge_verdicts_are_carried_when_the_judge_was_run(run, corpus, tmp_path):
    first = build(run, corpus, tmp_path, n_checks=0)[1]
    v = first["items"][first["order"][0]]
    judge = tmp_path / "judge.jsonl"
    judge.write_text(json.dumps({"model": v["model"], "task_id": v["task"], "sample": v["sample"],
                                 "label": "same", "score": 0.9}) + "\n")
    key = build(run, corpus, tmp_path, n_checks=0, judge=rs.read_judge(judge))[1]
    labelled = [x for x in key["items"].values() if x.get("judge_label")]
    assert len(labelled) == 1 and labelled[0]["judge_label"] == "same"
    judge.write_text(json.dumps({"model": "m", "task_id": "t", "sample": 0, "label": "maybe"}) + "\n")
    with pytest.raises(SystemExit):
        rs.read_judge(judge)


def test_plan_only_draws_nothing(run, corpus, tmp_path, capsys):
    d = tmp_path / "run" / "samples" / "spec"
    d.mkdir(parents=True)
    (d / "m.jsonl").write_text("\n".join(json.dumps(s) for s in run) + "\n")
    rs.main([str(tmp_path / "run"), "--plan-only", "--pairs", "30"])
    out = capsys.readouterr().out
    assert "30 pairs" in out and "right (run)" in out
    with pytest.raises(SystemExit):
        rs.main([str(tmp_path / "run"), "--set", "a4-v1", "--plan-only"])
