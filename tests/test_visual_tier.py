"""Tier-1 (visual diff) must not rescue a scene that differs in a small detail.

Fixtures are 256x256 renders of ``clinvar-1tup-D281`` (red ball-and-stick on p53
A281) and four wrong predictions. Each wrong one scores > 0.99 on the old
whole-image similarity, which used to rescue it.
"""

import pathlib

import pytest

pytest.importorskip("PIL")

from molbench.escalate import escalating_grade  # noqa: E402
from molbench.visual import changed_pixels, image_similarity  # noqa: E402

DATA = pathlib.Path(__file__).parent / "data" / "t1"
WRONG = ["wrong_residue", "neighbour_residue", "wrong_colour", "wrong_chain"]


def test_a_rerender_changes_no_pixels():
    assert changed_pixels(DATA / "ref.png", DATA / "ref_again.png") == 0


@pytest.mark.parametrize("name", WRONG)
def test_a_small_wrong_detail_changes_pixels(name):
    assert image_similarity(DATA / "ref.png", DATA / f"{name}.png") > 0.99  # the old test passed it
    assert changed_pixels(DATA / "ref.png", DATA / f"{name}.png") > 2


@pytest.mark.parametrize("name,decision", [("ref_again", "rendering-equivalent"),
                                           ("wrong_residue", "visually-different")])
def test_escalation_rescues_only_identical_renders(tmp_path, name, decision):
    pngs = {"gray": DATA / "ref.png", "red": DATA / f"{name}.png"}

    def render(tree, out):  # stand-in renderer: copy the fixture for this scene
        colour = tree["children"][0]["params"]["color"]
        pathlib.Path(out).write_bytes(pngs[colour].read_bytes())

    def scene(colour):
        return {"kind": "root", "children": [{"kind": "color", "params": {"color": colour}}]}

    g = escalating_grade(scene("gray"), scene("red"), render=render, workdir=tmp_path)
    assert g["decision"] == decision
