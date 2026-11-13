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


# --- renders framed on the target (decision 24) ----------------------------------------

def test_target_rows_are_the_highlight_not_the_context():
    import json

    from molbench import render
    task = json.loads((pathlib.Path(__file__).parent.parent / "tasks" / "mvs_clinical"
                       / "clinvar-1tup-D281.json").read_text())
    rows = render.target_rows(task)
    assert len(rows) == 8                       # Asp281 of chain A, not the 5,441-atom cartoon
    assert render.target_rows({**task, "target": {"selector": {"auth_asym_id": "B", "auth_seq_id": 175}}}) != rows
    assert render.rows_of(0b1011) == [0, 1, 3]


def test_reference_and_answer_are_rendered_from_the_same_camera(tmp_path):
    """Needs the Mol* bundle and a headless browser (the ``execute`` extra); skipped
    without them. The camera is worked out by Mol* on the reference's target atoms and
    the same snapshot is applied to the answer."""
    import json

    from molbench import render
    pytest.importorskip("playwright")
    gemmi = pytest.importorskip("gemmi")
    if not (render.STATIC / "molstar" / "molstar.js").exists():
        pytest.skip("Mol* bundle not fetched")
    repo = pathlib.Path(__file__).parent.parent
    task = json.loads((repo / "tasks" / "mvs_clinical" / "clinvar-1tup-D281.json").read_text())
    ref = task["reference_mvs"]
    wrong = json.loads(json.dumps(ref).replace('"auth_seq_id": 281', '"auth_seq_id": 282'))
    try:
        out = render.render_pair(ref, wrong, tmp_path, render.target_rows(task), width=400, height=300,
                                 network=False)        # the structure comes from the frozen panel
    except Exception as e:  # noqa: BLE001 - no browser
        pytest.skip(f"cannot render here: {str(e).splitlines()[0][:120]}")
    assert "answer_error" not in out and set(out["files"]) == {
        "ref_whole", "ref_target", "answer_whole", "answer_target", "panel"}
    # the camera looks at the centroid of the target atoms (from the frozen mmCIF) ...
    st = gemmi.read_structure(str(repo / "data" / "panel" / "cif" / "1tup.cif.gz"))
    pos = [a.pos for ch in st[0] if ch.name == "A" for r in ch if r.seqid.num == 281 for a in r]
    centroid = [sum(p[i] for p in pos) / len(pos) for i in range(3)]
    assert out["framed"]["n_atoms"] == len(pos) == 8
    assert all(abs(a - b) < 0.01 for a, b in zip(out["target_camera"]["target"], centroid))
    assert out["target_camera"]["radius"] < out["whole_camera"]["radius"] / 3
    # ... and the wrong residue, hard to see in the whole view, is plain in the target view
    whole = changed_pixels(out["files"]["ref_whole"], out["files"]["answer_whole"])
    target = changed_pixels(out["files"]["ref_target"], out["files"]["answer_target"])
    assert target > 10 * max(whole, 1)
    # the same scene from the same camera is the same picture
    again = render.render_framed(ref, tmp_path / "again.png", camera=out["target_camera"],
                                 width=400, height=300, network=False)
    assert again["frozen_files"] == ["1tup"]
    assert changed_pixels(out["files"]["ref_target"], again["png"]) == 0
    assert again["camera"]["target"] == out["target_camera"]["target"]
