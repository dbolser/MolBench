#!/usr/bin/env python3
"""
Which of two coincident representations does Mol* show?

A model often answers "a grey cartoon with residues 84-95 in green" with two components:
the whole polymer as a grey cartoon, then residues 84-95 as a green cartoon. Both are
created, so a read-back of the viewer's representation objects lists a green cartoon on
those residues. On screen there is none: the two meshes are the same there, the one
created first wins the depth test, and the picture is grey all over. (Found on the
pilot of 2026-11-16: `PILOT.md`.)

This script measures it. For each representation type it renders, from one camera in
headless Mol* (the bundle the grader is checked against), a stretch of 3K34 drawn green
on its own, drawn after the same type in grey on the whole polymer, and drawn before
it, and counts green pixels. It also renders the larger and the smaller size factor.
The result is the rule `molbench.mvs.DrawnStructure.settle` implements:

* same type, same size: the first one listed is seen, the later one is hidden;
* another size factor: the larger one is seen, whatever the order;
* a surface is the exception: the surface of a part pokes through the surface of the
  whole either way, so both count as drawn.

    python scripts/check_overlap.py            # measure, write tests/controls/overlap_evidence.json
    python scripts/check_overlap.py --check    # measure, compare with the file, write nothing

Needs the execute extra and the Mol* bundle; no network (the structure is read from the
frozen panel).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import mvs, render  # noqa: E402

OUT = REPO / "tests" / "controls" / "overlap_evidence.json"
ENTRY = "3k34"
PART = {"auth_asym_id": "A", "beg_auth_seq_id": 84, "end_auth_seq_id": 95}
TYPES = ["cartoon", "backbone", "putty", "ball_and_stick", "line", "spacefill", "surface"]
SIZES = [("cartoon", 1.3), ("ball_and_stick", 1.5), ("ball_and_stick", 0.6)]
#: a later draw counts as hidden when it shows fewer than this share of the green pixels
#: the part has on its own, and as seen when it shows more than SEEN of them
HIDDEN, SEEN = 0.01, 0.10


def scene(comps: list[tuple]) -> dict:
    children = [{"kind": "component", "params": {"selector": sel}, "children": [
        {"kind": "representation", "params": {"type": rtype, **extra},
         "children": [{"kind": "color", "params": {"color": colour}}]}]}
        for sel, rtype, colour, extra in comps]
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": f"https://files.rcsb.org/download/{ENTRY}.cif"},
         "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
             {"kind": "structure", "params": {"type": "model"}, "children": children}]}]}]}}


def green_pixels(png: pathlib.Path) -> int:
    from PIL import Image
    im = Image.open(png).convert("RGB")
    data = im.tobytes()
    return sum(1 for i in range(0, len(data), 3)
               if data[i + 1] > data[i] + 40 and data[i + 1] > data[i + 2] + 40)


def grader_sees_green(sc: dict) -> bool:
    """Does the grader's resolved state hold a green draw?"""
    st = next(iter(mvs.resolve_scene(sc).structures.values()))
    return any(colour == mvs.mvs_color("green") for _, colour, _ in st.draws)


def measure() -> dict:
    rows = []
    camera = None
    with tempfile.TemporaryDirectory() as tmp:
        def shot(name: str, comps: list[tuple]) -> tuple[int, dict]:
            nonlocal camera
            png = pathlib.Path(tmp) / f"{name}.png"
            sc = scene(comps)
            kw = {"camera": camera} if camera else {}
            r = render.render_framed(sc, png, network=False, **kw)
            camera = camera or r["camera"]
            return green_pixels(png), sc

        cases = [(t, 1.0) for t in TYPES] + SIZES
        for rtype, factor in cases:
            extra = {} if factor == 1.0 else {"size_factor": factor}
            base = ("polymer", rtype, "gray", {})
            part = (PART, rtype, "green", extra)
            tag = f"{rtype}_{factor}"
            alone, _ = shot(tag + "_alone", [part])
            after, sc_after = shot(tag + "_after", [base, part])
            before, sc_before = shot(tag + "_before", [part, base])
            rows.append({
                "type": rtype, "size_factor_of_part": factor,
                "green_pixels": {"part_alone": alone, "base_then_part": after,
                                 "part_then_base": before},
                "viewer_shows_part": {"base_then_part": verdict(after, alone),
                                      "part_then_base": verdict(before, alone)},
                "grader_draws_part": {"base_then_part": grader_sees_green(sc_after),
                                      "part_then_base": grader_sees_green(sc_before)},
            })
    return {
        "what": "green pixels of residues A 84-95 of 3K34 drawn green, alone, after and before "
                "the same representation type drawn grey on the whole polymer; one camera",
        "viewer": "headless Mol* (molbench/static/molstar), 800x600",
        "thresholds": {"hidden_below_share_of_alone": HIDDEN, "seen_above_share_of_alone": SEEN},
        "rows": rows,
    }


def verdict(n: int, alone: int) -> bool | None:
    if alone and n <= HIDDEN * alone:
        return False
    if alone and n >= SEEN * alone:
        return True
    return None


def disagreements(report: dict) -> list[str]:
    bad = []
    for row in report["rows"]:
        for order in ("base_then_part", "part_then_base"):
            seen, drawn = row["viewer_shows_part"][order], row["grader_draws_part"][order]
            if seen is None:
                bad.append(f"{row['type']} x{row['size_factor_of_part']} {order}: unclear picture "
                           f"({row['green_pixels']})")
            elif seen != drawn:
                bad.append(f"{row['type']} x{row['size_factor_of_part']} {order}: viewer "
                           f"{'shows' if seen else 'hides'} the part, grader "
                           f"{'draws' if drawn else 'drops'} it")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--check", action="store_true", help="compare with the file, write nothing")
    args = ap.parse_args()
    report = measure()
    for row in report["rows"]:
        g = row["green_pixels"]
        print(f"{row['type']:15s} x{row['size_factor_of_part']:<4} alone {g['part_alone']:6d}  "
              f"after base {g['base_then_part']:6d}  before base {g['part_then_base']:6d}  "
              f"viewer {row['viewer_shows_part']}  grader {row['grader_draws_part']}")
    bad = disagreements(report)
    for b in bad:
        print("DISAGREES:", b)
    if args.check:
        old = json.loads(OUT.read_text()) if OUT.exists() else None
        same = old is not None and [
            (r["type"], r["size_factor_of_part"], r["viewer_shows_part"]) for r in old["rows"]] == [
            (r["type"], r["size_factor_of_part"], r["viewer_shows_part"]) for r in report["rows"]]
        if not same:
            print(f"{OUT.relative_to(REPO)} is stale")
            return 1
    else:
        OUT.write_text(json.dumps(report, indent=1) + "\n")
        print(f"wrote {OUT.relative_to(REPO)}")
    print("grader agrees with the viewer on every case" if not bad else f"{len(bad)} disagreement(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
