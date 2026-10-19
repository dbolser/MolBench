#!/usr/bin/env python3
"""
Build the A4 human-agreement rating set from the VLM-judged pairs of a run.

Every pair the T2 judge saw (reference render vs a model's render) is a candidate,
except those the public gallery already shows with their verdict (--public). At most
--max-per-task are kept per task, so raters don't see one prompt a dozen times;
ids listed in --keep (pairs already rated) are kept first. Plus two kinds of attention check with a known answer that doesn't depend on the judge:

  control-same       a T1 rescue: the two renders differ by <= 2 pixels
  control-different  one task's reference vs another task's, on a different structure

Writes two things, kept apart so raters stay blind:

  <out>/items.json + <out>/img/   PUBLIC — prompt and two images per item, opaque ids,
                                  no model name or verdict. Copied to the rating site.
  <key>                           PRIVATE answer key — model, task, VLM verdict, control
                                  type per id, and the secret the ids are keyed with
                                  (reused on rebuild, so ids stay stable). Read by
                                  scripts/agreement.py.

    python scripts/build_rating_set.py results/r2x2/spec \\
        --out ../molstar-chat-driver/site/rate/a4-v1 --key results/a4/a4-v1/key.json
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import hmac
import json
import pathlib
import random
import secrets
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import runner  # noqa: E402
from molbench.escalate import _download_ids  # noqa: E402

QUESTION = (
    "Ignore camera angle, zoom and orientation. Does the model's scene show the SAME "
    "visualization as the reference: same structure, same parts shown, equivalent "
    "representations (cartoon / surface / ball-and-stick), equivalent colours, and the "
    "same region highlighted or focused?"
)


def item_id(secret: str, set_id: str, *parts: str) -> str:
    """Keyed, so a rater can't recompute ids from the public model and task lists."""
    msg = ":".join((set_id, *parts)).encode()
    return hmac.new(bytes.fromhex(secret), msg, hashlib.sha256).hexdigest()[:12]


def judged_pairs(results: pathlib.Path) -> list[dict]:
    """One record per escalated task that has both renders: T2-judged or a T1 rescue."""
    out = []
    for path in sorted(results.glob("*.json")):
        card = json.loads(path.read_text())
        for model, m in card["models"].items():
            for t in m["tasks"]:
                e = t.get("escalation") or {}
                if e.get("decision") not in ("vlm:same", "vlm:different", "rendering-equivalent"):
                    continue
                out.append({"model": model, "task": t["id"], "decision": e["decision"],
                            "tree_f1": e.get("tree_f1"), "changed_pixels": e.get("changed_pixels"),
                            "vlm": e.get("vlm"), "ref_png": e["ref_png"], "pred_png": e["pred_png"]})
    return out


def _short(model: str) -> str:
    """The model name without its provider prefix; the gallery uses both forms."""
    return model.split("/")[-1]


def public_pairs(gallery: pathlib.Path | None) -> set[tuple[str, str]]:
    """(model, task) pairs on the public gallery page, which shows the judge's verdict."""
    if gallery is None:
        return set()
    return {(_short(r["model"]), r["id"]) for r in json.loads(gallery.read_text())["rows"]}


def build(results: pathlib.Path, set_id: str, n_controls: int, seed: int,
          secret: str, public: set[tuple[str, str]] = frozenset(),
          max_per_task: int | None = None, keep: set[str] = frozenset()) -> tuple[list[dict], dict]:
    """(items, key). Items carry source image paths under `_ref`/`_out` until written."""
    tasks = {t["id"]: t for t in runner.load_tasks(None)}
    pairs = [p for p in judged_pairs(results) if (_short(p["model"]), p["task"]) not in public]
    if not pairs:
        raise SystemExit(f"{results}: no escalated pairs with renders")
    rng = random.Random(seed)
    items, key = [], {}

    def add(kind: str, task: str, ref: str, out: str, ident: tuple[str, ...], **info) -> None:
        i = item_id(secret, set_id, kind, *ident)
        items.append({"id": i, "prompt": tasks[task]["prompt"], "_ref": ref, "_out": out})
        key[i] = {"kind": kind, "task": task, **info}

    judged = collections.defaultdict(list)
    for p in pairs:
        if p["decision"].startswith("vlm:"):
            judged[p["task"]].append(p)
    for task, ps in judged.items():
        # Already-rated pairs first; then alternate the judge's "same" and "different"
        # calls so the cap keeps both, each in keyed-id order (fixed, unpredictable).
        ident = {id(p): item_id(secret, set_id, "vlm", p["model"], task) for p in ps}
        by_label = {lab: sorted((p for p in ps if p["vlm"]["label"] == lab), key=lambda p: ident[id(p)])
                    for lab in ("same", "different")}
        rank = {id(p): n for lab in by_label for n, p in enumerate(by_label[lab])}
        ps.sort(key=lambda p: (ident[id(p)] not in keep, rank.get(id(p), len(ps)), p["vlm"]["label"] != "same"))
        for p in ps[:max_per_task]:
            add("vlm", p["task"], p["ref_png"], p["pred_png"], (p["model"], p["task"]),
                model=p["model"], vlm_label=p["vlm"]["label"], vlm_score=p["vlm"].get("score"),
                judge=p["vlm"].get("judge"), tree_f1=p["tree_f1"], changed_pixels=p["changed_pixels"])

    t1 = [p for p in pairs if p["decision"] == "rendering-equivalent"]
    for p in rng.sample(t1, min(n_controls, len(t1))):
        add("control-same", p["task"], p["ref_png"], p["pred_png"], (p["model"], p["task"]),
            model=p["model"], expected="same", changed_pixels=p["changed_pixels"])

    refs = {p["task"]: p["ref_png"] for p in pairs}  # one reference render per task
    structure = {t: frozenset(_download_ids(tasks[t]["reference_mvs"])) for t in refs}
    names = sorted(refs)
    for a in rng.sample(names, min(n_controls, len(names))):
        others = [t for t in names if structure[t].isdisjoint(structure[a])]
        if not others:
            raise SystemExit(f"no reference on a different structure to pair with {a}")
        b = rng.choice(others)
        add("control-different", a, refs[a], refs[b], (a, b), other_task=b, expected="different")

    rng.shuffle(items)
    return items, key


def write(items: list[dict], key: dict, set_id: str, secret: str, out: pathlib.Path, key_path: pathlib.Path,
          quality: int = 85) -> None:
    from PIL import Image
    (out / "img").mkdir(parents=True, exist_ok=True)
    public = []
    for it in items:
        rec = {"id": it["id"], "prompt": it["prompt"]}
        for side, src in (("ref", it["_ref"]), ("out", it["_out"])):
            rel = f"img/{it['id']}-{side}.jpg"
            with Image.open(src) as im:  # flatten any transparency onto white, not black
                rgba = im.convert("RGBA")
                flat = Image.new("RGB", rgba.size, (255, 255, 255))
                flat.paste(rgba, mask=rgba.getchannel("A"))
                flat.save(out / rel, "JPEG", quality=quality)
            rec[side] = rel
        public.append(rec)
    (out / "items.json").write_text(json.dumps(
        {"set": set_id, "question": QUESTION, "items": public}, indent=1) + "\n")
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(json.dumps({"set": set_id, "secret": secret, "items": key}, indent=1, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", type=pathlib.Path, help="directory of scorecards with escalation")
    ap.add_argument("--set", dest="set_id", default="a4-v1")
    ap.add_argument("--out", type=pathlib.Path, required=True, help="public item dir")
    ap.add_argument("--key", type=pathlib.Path, required=True, help="private answer key (json)")
    ap.add_argument("--controls", type=int, default=12, help="checks of each kind")
    ap.add_argument("--seed", type=int, default=4)
    ap.add_argument("--max-per-task", type=int, default=3, help="judged pairs kept per task")
    ap.add_argument("--keep", type=pathlib.Path,
                    help="JSON list of item ids already rated; kept first under the cap")
    ap.add_argument("--public", type=pathlib.Path, default=REPO / "docs" / "gallery_data.json",
                    help="published gallery; its pairs are left out so raters can't copy a verdict")
    a = ap.parse_args(argv)
    secret = (json.loads(a.key.read_text())["secret"] if a.key.exists()
              else secrets.token_hex(32))
    keep = set(json.loads(a.keep.read_text())) if a.keep else set()
    items, key = build(a.results, a.set_id, a.controls, a.seed, secret, public_pairs(a.public),
                       a.max_per_task, keep)
    write(items, key, a.set_id, secret, a.out, a.key)
    kinds = {}
    for v in key.values():
        kinds[v["kind"]] = kinds.get(v["kind"], 0) + 1
    print(f"{len(items)} items -> {a.out} ({kinds}); key -> {a.key}")


if __name__ == "__main__":
    main()
