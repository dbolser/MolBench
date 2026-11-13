#!/usr/bin/env python3
"""
Build the fixture tasks under ``tests/fixtures/tasks/``: a handful of tiny tasks of
each kind the final corpus has and today's corpus does not - follow-up turns (one of
them a "no change"), accept-set, MVS/API twins, paraphrases, and a held-back split.
They exist so the dry run and the tests can exercise those paths; they are not
benchmark tasks and are never scored for a paper.

Like real tasks they are built from the frozen panel only (``data/panel/facts``, the
atom tables) and checked before they are written: every reference must grade as exactly right
against its task, every accepted alternative must be a gradable and different final
state, every target must select atoms, and twins must select the same atoms. No network.

    uv run python tests/fixtures/build_fixture_tasks.py          # rewrite the files
    uv run python tests/fixtures/build_fixture_tasks.py --check  # fail if they would change

Which structures: the panel entries with one model whose only non-polymer, non-water
component is a single ligand copy, smallest first (two public, the third held back);
and, for the accept-set tasks, the smallest entries with a protein present as exactly
two chains. 1HSG is skipped: it is the API prompt's worked example.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))

from molbench import grounding, runner, tasks as T  # noqa: E402

OUT = HERE / "tasks"
SCRIPT = "tests/fixtures/build_fixture_tasks.py"
DATE = "2026-11-12"   # the panel's retrieval date; fixed so a rebuild is byte-identical
COLOR = "red"


def scene(entry: str, components: list[dict]) -> dict:
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": f"https://files.rcsb.org/download/{entry}.cif"},
         "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
             {"kind": "structure", "params": {"type": "model"}, "children": components}]}]}]}}


def component(selector, rep: str, color: str | None = None) -> dict:
    node = {"kind": "representation", "params": {"type": rep}}
    if color:
        node["children"] = [{"kind": "color", "params": {"color": color}}]
    return {"kind": "component", "params": {"selector": selector}, "children": [node]}


def ligand_entries() -> list[tuple[dict, dict]]:
    out = []
    for e in grounding.panel()["entries"]:
        f = grounding.facts(e["id"])
        if (e["kind"] != "pdb" or e["id"] == T.WORKED_EXAMPLE or f["n_models"] != 1
                or len(f["ligands"]) != 1 or f["covalent_links"] or f["metal_bonds"]):
            continue
        lig = f["ligands"][0]
        if lig["kind"] == "ligand" and len(lig["copies"]) == 1:
            out.append((e, lig))
    return sorted(out, key=lambda x: (x[0]["atoms"], x[0]["id"]))


def two_copy_entries() -> list[tuple[dict, dict]]:
    out = []
    for e in grounding.panel()["entries"]:
        f = grounding.facts(e["id"])
        if e["kind"] != "pdb" or e["id"] == T.WORKED_EXAMPLE or f["n_models"] != 1:
            continue
        hits = [x for x in f["entities"] if x["polymer_type"] == "protein"
                and len(x["label_asym_ids"]) == 2]
        if hits:
            out.append((e, hits[0]))
    return sorted(out, key=lambda x: (x[0]["atoms"], x[0]["id"]))


def base(tid: str, track: str, tier: str, family: str, entry: str, prompt: str, reference,
         target, skills: list[str], inputs: list[str], **more) -> dict:
    return {"id": tid, "track": track, "tier": tier, "family": family, "structures": [entry],
            "prompt": prompt, "reference": reference, "accepted": [], "context": None,
            "target": target, "twin_of": None, "paraphrase_of": None, "style": "full",
            "split": "public", "grounding": None,
            "provenance": {"script": SCRIPT, "inputs": inputs, "date": DATE, "checks": []},
            "skills": skills, "notes": "Fixture for the dry run and the tests; not a benchmark task.",
            **more}


def twin(a: dict, b: dict) -> list[dict]:
    a["twin_of"], b["twin_of"] = b["id"], a["id"]
    return [a, b]


def build() -> list[dict]:
    out: list[dict] = []
    ligands = ligand_entries()[:3]
    assert len(ligands) == 3, "need three single-ligand panel entries"
    phrasing = {
        "full": "Load {ID}. Show the protein as a cartoon and the {name} ({comp}) as "
                "{color} ball-and-stick.",
        "terse": "{ID}: protein cartoon, {comp} {color} ball-and-stick",
        "indirect": "I would like to look at {ID} with the protein drawn as a cartoon and its "
                    "{name} ligand ({comp}) picked out in {color} ball-and-stick.",
    }
    for n, (e, lig) in enumerate(ligands):
        entry, comp = e["id"], lig["comp_id"]
        words = dict(ID=entry.upper(), comp=comp, name=lig["name"].lower(), color=COLOR)
        inputs = [f"data/panel/facts/{entry}.json", f"molbench/atom_tables/{entry}.json.gz"]
        sel = {"label_comp_id": comp}
        plain = scene(entry, [component("polymer", "cartoon"), component(sel, "ball_and_stick")])
        red = scene(entry, [component("polymer", "cartoon"),
                            component(sel, "ball_and_stick", COLOR)])
        load = [{"action": "load", "molecule_id": entry}]
        paint = load + [{"action": "color", "data": [{"label_comp_id": comp, "color": COLOR}]}]
        t_mvs = [{"selector": sel, "representation": "ball_and_stick", "color": COLOR}]
        t_api = [{"selector": sel, "representation": "ball-and-stick", "color": COLOR}]
        split = "heldback" if n == 2 else "public"
        skills = ["load", "selection", "representation", "color"]

        def pair(stem: str, tier: str, family: str, prompt: str, **more) -> list[dict]:
            return twin(
                base(f"fx-{stem}-{entry}-mvs", "mvs", tier, family, entry, prompt, red, t_mvs,
                     skills, inputs, split=split,
                     **{k: v[0] if isinstance(v, tuple) else v for k, v in more.items()}),
                base(f"fx-{stem}-{entry}-api", "api", tier, family, entry, prompt, paint, t_api,
                     skills, inputs, split=split,
                     **{k: v[1] if isinstance(v, tuple) else v for k, v in more.items()}))

        originals = pair("ligand", "translation", "fx-ligand", phrasing["full"].format(**words))
        out += originals
        if n == 0:
            for style in ("terse", "indirect"):
                out += pair(f"ligand-{style}", "translation", "fx-ligand",
                            phrasing[style].format(**words), style=style,
                            paraphrase_of=(originals[0]["id"], originals[1]["id"]))
            out += pair("follow-colour", "followup", "fx-follow",
                        "Colour the {name} ({comp}) {color}.".format(**words),
                        context=({"scene": plain, "noop": False}, {"calls": load, "noop": False}))
        if n == 1:
            out += pair("follow-noop", "followup", "fx-follow",
                        "Colour the {name} ({comp}) {color}.".format(**words),
                        context=({"scene": red, "noop": True}, {"calls": paint, "noop": True}))

    copies = two_copy_entries()[:2]
    assert len(copies) == 2, "need two panel entries with a two-copy protein"
    for n, (e, entity) in enumerate(copies):
        entry = e["id"]
        first, second = entity["label_asym_ids"]
        name = entity["description"].strip().lower()
        inputs = [f"data/panel/facts/{entry}.json", f"molbench/atom_tables/{entry}.json.gz"]
        chains = "label chains {} and {}".format(first, second)
        out.append(base(
            f"fx-anycopy-{entry}-mvs", "mvs", "accept_set", "fx-anycopy", entry,
            f"Load {entry.upper()} and show one copy of {name} as a cartoon, nothing else. "
            f"There are two copies ({chains}); either will do.",
            scene(entry, [component({"label_asym_id": first}, "cartoon")]),
            [{"selector": {"label_asym_id": first}, "representation": "cartoon", "color": None}],
            ["load", "selection", "representation"], inputs,
            accepted=[scene(entry, [component({"label_asym_id": second}, "cartoon")])],
            accepted_targets=[[{"selector": {"label_asym_id": second},
                                "representation": "cartoon", "color": None}]]))
        if n == 0:
            out.append(base(
                f"fx-anycopy-{entry}-api", "api", "accept_set", "fx-anycopy-focus", entry,
                f"Load {entry.upper()} and zoom in on one copy of {name}. "
                f"There are two copies ({chains}); either will do.",
                [{"action": "load", "molecule_id": entry},
                 {"action": "focus", "data": [{"struct_asym_id": first}]}],
                [{"selector": {"label_asym_id": first}, "representation": None, "color": None}],
                ["load", "selection", "focus"], inputs,
                accepted=[[{"action": "load", "molecule_id": entry},
                           {"action": "focus", "data": [{"struct_asym_id": second}]}]],
                accepted_targets=[[{"selector": {"label_asym_id": second},
                                    "representation": None, "color": None}]]))
    return out


def verify(built: list[dict]) -> list[dict]:
    """Run the corpus checks on the built tasks and record what each one passed."""
    loaded = []
    for t in built:
        t["provenance"]["checks"] = ["(filled in below, once passed)"]
        errors = T.validate_task(t)
        if errors:
            raise SystemExit(f"{t['id']}: " + "; ".join(errors))
        loaded.append(T._with_aliases({**t, "_path": f"tests/fixtures/tasks/{t['id']}.json"}))
    errors, _ = T.check_corpus(loaded, grade=runner.grade_parsed)
    if errors:
        raise SystemExit("fixture tasks fail the corpus checks:\n  " + "\n  ".join(errors))
    for t, full in zip(built, loaded):
        n_atoms = sum(bin(m).count("1") for m in T.target_atoms(full).values())
        checks = ["reference grades as exactly right against the task (runner.grade_parsed)",
                  f"target selects {n_atoms} atoms on the frozen atom table"]
        if t["accepted"]:
            checks.append("every accepted alternative grades as itself, is accepted by the "
                          "task, and is a different final state from the reference")
        if t["twin_of"]:
            checks.append("twin selects the same target atoms")
        if t["context"]:
            checks.append("start state grades as itself; noop flag agrees with the grader")
        t["provenance"]["checks"] = checks
    return built


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if the files would change")
    a = ap.parse_args(argv)
    files = {OUT / f"{t['id']}.json": json.dumps(t, indent=1) + "\n" for t in verify(build())}
    stale = sorted(set(OUT.glob("*.json")) - set(files))
    changed = [p for p, text in files.items()
               if not p.exists() or p.read_text(encoding="utf-8") != text]
    if a.check:
        if changed or stale:
            print("fixture tasks are out of date:", *[p.name for p in changed + stale])
            return 1
        print(f"{len(files)} fixture tasks are up to date")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"wrote {len(files)} fixture tasks to {OUT} ({len(changed)} changed, {len(stale)} removed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
