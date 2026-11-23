#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Draw the paper's figures from ``paper/generated/figdata.json``.

    uv run scripts/paper_figures.py            # after scripts/paper_tables.py

Reads only ``figdata.json`` (written by ``scripts/paper_tables.py``), so the figures can
be redrawn without the raw archives. Writes ``paper/generated/fig_*.svg`` and ``.pdf``.

    uv run scripts/paper_figures.py --result-figure paper/generated_mock   # Figure 5, dry run
    uv run scripts/paper_figures.py --result-figure paper/generated        # Figure 5, final run

The result figure (Figure 5 of the paper) is drawn from the four result tables that
``scripts/paper_tables.py`` writes (``table_final_*.md``), so the figure and the tables cannot
differ. It is written next to them, with ``fig_final_results.md``, the line that the paper
includes in place of its layout sketch once the file exists in ``paper/generated``. Mock
tables are refused there and their figure is stamped as mock.

Every series is told apart twice: by colour (a blue/orange pair checked for the common
colour-vision deficiencies) and by marker shape or fill, so the figures still read in
greyscale. Output is deterministic (no dates, fixed ids), so a re-run on the same data
gives byte-identical SVG.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
GEN = REPO / "paper" / "generated"

BLUE, ORANGE = "#2a78d6", "#eb6834"   # validated pair (CVD and normal-vision separation)
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#dddcd6"
PNG_DIR: pathlib.Path | None = None

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 9.5,
    "axes.labelsize": 8.5, "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.labelcolor": INK,
    "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
    "svg.fonttype": "none", "svg.hashsalt": "molbench", "pdf.fonttype": 42,
    "figure.dpi": 150,
})


def save(fig, out: pathlib.Path, name: str) -> None:
    fig.savefig(out / f"{name}.svg", metadata={"Date": None}, bbox_inches="tight")
    fig.savefig(out / f"{name}.pdf", metadata={"CreationDate": None, "ModDate": None},
                bbox_inches="tight")
    if PNG_DIR is not None:  # previews for checking layout; not used by the paper
        fig.savefig(PNG_DIR / f"{name}.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


def mark_status(fig, data: dict) -> None:
    """Stamp a figure drawn from data that the final run will supersede."""
    if data.get("status") == "preliminary":
        fig.axes[0].annotate(f"PRELIMINARY — {data.get('label', '')}", xy=(1, 0),
                             xycoords="axes fraction", xytext=(0, -34),
                             textcoords="offset points", ha="right", va="top", fontsize=6.5,
                             color=MUTED)


def fig_validity(data: dict, out: pathlib.Path, track: str = "mvs") -> bool:
    """Strict F1 against valid-scene rate, one point per model."""
    rows = data.get(f"{track}_leaderboard")
    if not rows:
        return False
    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    ax.plot([0, 1], [0, 1], color=MUTED, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.text(0.30, 0.325, "strict F1 = valid-scene rate", rotation=40.5, color=MUTED, fontsize=7,
            rotation_mode="anchor")
    styles = {"open": dict(marker="o", color=BLUE, label="open weights"),
              "closed": dict(marker="s", color=ORANGE, label="closed weights")}
    for w, st in styles.items():
        pts = [r for r in rows if r["weights"] == w]
        if pts:
            ax.scatter([r["valid"] for r in pts], [r["f1"] for r in pts], s=34, marker=st["marker"],
                       facecolor=st["color"], edgecolor="white", linewidth=0.8, label=st["label"],
                       zorder=3)
    other = [r for r in rows if r["weights"] not in styles]
    if other:
        ax.scatter([r["valid"] for r in other], [r["f1"] for r in other], s=34, marker="^",
                   facecolor=MUTED, edgecolor="white", linewidth=0.8, label="other", zorder=3)
    # Direct labels on the extremes only; the full list is in the leaderboard table.
    ranked = sorted(rows, key=lambda r: r["f1"])
    for r in ranked[:3] + ranked[-1:]:
        ax.annotate(r["model"], (r["valid"], r["f1"]), xytext=(6, -3), textcoords="offset points",
                    fontsize=7, color=INK)
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.set_aspect("equal")
    ax.grid(True)
    ax.set_axisbelow(True)
    ax.set_xlabel("Valid-scene rate (share of outputs Mol* can show)")
    ax.set_ylabel("Strict F1 (invalid output scores 0)")
    ax.legend(loc="upper left")
    mark_status(fig, data)
    save(fig, out, f"fig_{track}_validity")
    return True


def fig_leaderboard(data: dict, out: pathlib.Path, track: str = "mvs") -> bool:
    """Per model: strict F1 with its interval, and F1 over valid scenes."""
    rows = data.get(f"{track}_leaderboard")
    if not rows:
        return False
    rows = sorted(rows, key=lambda r: r["f1"])
    fig, ax = plt.subplots(figsize=(5.6, 0.27 * len(rows) + 1.1))
    for y, r in enumerate(rows):
        if r["f1_valid"] is not None:
            ax.plot([r["f1"], r["f1_valid"]], [y, y], color=GRID, lw=1.2, zorder=1)
        if r["f1_ci"]:
            ax.plot(r["f1_ci"], [y, y], color=BLUE, lw=2, solid_capstyle="round", zorder=2)
    ax.scatter([r["f1"] for r in rows], range(len(rows)), s=30, marker="o", facecolor=BLUE,
               edgecolor="white", linewidth=0.8, zorder=3,
               label="strict F1 (line: 95% interval)")
    have = [(r["f1_valid"], y) for y, r in enumerate(rows) if r["f1_valid"] is not None]
    ax.scatter([x for x, _ in have], [y for _, y in have], s=30, marker="D", facecolor="white",
               edgecolor=ORANGE, linewidth=1.4, zorder=3, label="F1 over valid scenes only")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r["model"] for r in rows], color=INK)
    ax.set_xlim(0, 1.02)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("F1")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, columnspacing=1.5,
              handletextpad=0.4)
    mark_status(fig, data)
    save(fig, out, f"fig_{track}_leaderboard")
    return True


def fig_regimes(data: dict, out: pathlib.Path, track: str = "mvs") -> bool:
    """Per regime: every model's F1 over valid scenes (dots) and the mean (bar)."""
    rows = data.get(f"{track}_regimes")
    if not rows:
        return False
    fig, ax = plt.subplots(figsize=(5.6, 0.55 * len(rows) + 1.2))
    n = len(rows)
    for k, r in enumerate(rows):
        y = n - 1 - k
        ax.barh(y + 0.17, r["f1"] or 0, height=0.3, color=BLUE, edgecolor="white", linewidth=0.8,
                label="strict F1, mean over models" if k == 0 else None, zorder=2)
        ax.barh(y - 0.17, r["f1_valid"] or 0, height=0.3, color="white", edgecolor=ORANGE,
                linewidth=1.2, hatch="////",
                label="F1 over valid scenes, mean over models" if k == 0 else None, zorder=2)
        ax.scatter(r["f1_valid_models"], [y - 0.17] * len(r["f1_valid_models"]), s=7,
                   color=INK, alpha=0.55, linewidth=0, zorder=3,
                   label="one model (valid scenes)" if k == 0 else None)
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{r['regime']}\n{r['n_tasks']} tasks, {r['n_structures']} "
                        f"structure{'s' if r['n_structures'] != 1 else ''}, "
                        f"{r['n_valid']}/{r['n_samples']} valid" for r in reversed(rows)],
                       color=INK, fontsize=7.5)
    ax.set_xlim(0, 1.02)
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("F1")
    ax.legend(loc="lower center", bbox_to_anchor=(0.4, 1.0), ncol=1, handletextpad=0.5)
    mark_status(fig, data)
    save(fig, out, f"fig_{track}_regimes")
    return True


def fig_grounding(data: dict, out: pathlib.Path, track: str = "mvs") -> bool:
    """Per model: change in strict F1 with a grounding pack; marker = lookup tasks only."""
    rows = data.get(f"{track}_grounding")
    if not rows:
        return False
    rows = sorted(rows, key=lambda r: r["delta"])
    fig, ax = plt.subplots(figsize=(5.6, 0.27 * len(rows) + 1.1))
    ys = range(len(rows))
    ax.barh(ys, [r["delta"] for r in rows], height=0.55, color=BLUE, edgecolor="white",
            linewidth=0.8, zorder=2, label="all tasks")
    look = [(r["delta_lookup"], y) for y, r in zip(ys, rows) if r["delta_lookup"] is not None]
    ax.scatter([x for x, _ in look], [y for _, y in look], s=30, marker="D", facecolor="white",
               edgecolor=ORANGE, linewidth=1.4, zorder=3, label="lookup tasks only")
    ax.axvline(0, color=INK, lw=0.8, zorder=1)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([r["model"] for r in rows], color=INK)
    lim = max(0.12, max(abs(x) for r in rows for x in (r["delta"], r["delta_lookup"] or 0)) * 1.1)
    ax.set_xlim(-lim, lim)
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Change in strict F1 when the grounding pack is added")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, columnspacing=1.5,
              handletextpad=0.4)
    mark_status(fig, data)
    save(fig, out, f"fig_{track}_grounding")
    return True


def fig_repair(data: dict, out: pathlib.Path, track: str = "mvs") -> bool:
    """Per model: strict F1 and the upper bound after offline JSON repair."""
    rows = data.get(f"{track}_repair")
    if not rows:
        return False
    rows = sorted(rows, key=lambda r: r["strict"])
    fig, ax = plt.subplots(figsize=(5.6, 0.27 * len(rows) + 1.1))
    for y, r in enumerate(rows):
        if r["repaired"] - r["strict"] > 0.004:
            ax.annotate("", xy=(r["repaired"], y), xytext=(r["strict"], y),
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.0), zorder=1)
    ax.scatter([r["strict"] for r in rows], range(len(rows)), s=30, marker="o", facecolor=BLUE,
               edgecolor="white", linewidth=0.8, zorder=3, label="strict F1 (as reported)")
    ax.scatter([r["repaired"] for r in rows], range(len(rows)), s=30, marker="D",
               facecolor="white", edgecolor=ORANGE, linewidth=1.4, zorder=2,
               label="after offline JSON repair (upper bound)")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r["model"] + (" *" if r["n_raw"] < r["n_invalid_json"] else "")
                        for r in rows], color=INK)
    ax.set_xlim(0, 1.02)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.grid(True, axis="x")
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("F1")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, columnspacing=1.5,
              handletextpad=0.4)
    if any(r["n_raw"] < r["n_invalid_json"] for r in rows):
        ax.annotate("* raw text not archived; cannot be repaired offline", xy=(0, 0),
                    xycoords="axes fraction", xytext=(0, -34), textcoords="offset points",
                    ha="left", va="top", fontsize=6.5, color=MUTED)
    mark_status(fig, data)
    save(fig, out, f"fig_{track}_repair")
    return True


FIGURES = (fig_validity, fig_leaderboard, fig_regimes, fig_grounding, fig_repair)


# --------------------------------------------------------------------------- #
# The result figure of the paper (Figure 5), drawn from a run's tables
# --------------------------------------------------------------------------- #
RESULT_NAME = "fig_final_results"
RESULT_TABLES = ("table_final_leaderboard_scene.md", "table_final_leaderboard_calls.md",
                 "table_final_paired.md", "table_final_tiers.md")
# Okabe-Ito, as in paper/figures.py, whose layout sketch this figure replaces.
OI_BLUE, OI_ORANGE, OI_GREEN = "#0072B2", "#E69F00", "#009E73"
MOCK_NOTE = "MOCK DATA: dry run with a mock model, every number is fake"

RESULT_CAPTION = (
    "![**Figure 5. Results of the final run{mock}.** **A**: task success rate (the share of answers whose "
    "drawn state is exactly right) per model, strict, with 95% intervals, one plot per track; each plot "
    "is ordered by its own scores, † marks an optional model and an open square a script without a "
    "model. The two plots must not be compared with each other (Section 4.2); formats are compared in "
    "panel B only. **B**: for each model, its {{{{corpus.twins.n_with_target}}}} pairs that have a target "
    "score, by which side was right (at least 2 of its {{{{plan.samples}}}} answers target-right). **C**: "
    "valid answers only, per category, mean over the models: task success rate and target score (0 to 1: "
    "how exactly the answer marks out the requested atoms; any other drawing is ignored). A target score "
    "well above the task success rate means that the requested atoms were right and something else was "
    "not. Panel A is strict and panel C is valid-only, so the two must not be compared.]({path})\n")


def read_tables(path: pathlib.Path) -> list[tuple[str, list[str], list[list[str]]]]:
    """Every pipe table of a Markdown file as (bold title above it, header cells, rows)."""
    out, title, header, rows = [], "", None, []
    for line in path.read_text(encoding="utf-8").splitlines() + [""]:
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if header is None:
                header = cells
            elif not set(line) <= set("|:- "):
                rows.append(cells)
        else:
            if header is not None:
                out.append((title, header, rows))
                header, rows = None, []
            if line.startswith("**"):
                title = line.strip("* ")
    return out


def number(cell: str) -> tuple[float, tuple[float, float] | None] | None:
    """'0.547 [0.519, 0.576]' -> (0.547, (0.519, 0.576)); '76.5%' -> (0.765, None); '–' -> None."""
    import re
    nums = [float(x) for x in re.findall(r"[-+]?\d+(?:\.\d+)?", cell)]
    if not nums:
        return None
    scale = 0.01 if "%" in cell else 1.0
    return nums[0] * scale, ((nums[1] * scale, nums[2] * scale) if len(nums) >= 3 else None)


def column(header: list[str], name: str) -> int:
    for i, h in enumerate(header):
        if h.startswith(name):
            return i
    raise SystemExit(f"no column '{name}' in a result table (columns: {header})")


def result_figure(tables: pathlib.Path, out: pathlib.Path) -> pathlib.Path:
    """Figure 5 from the four result tables in ``tables``; written to ``out`` with the
    Markdown line that the paper includes. Mock tables are never written into
    ``paper/generated``, and their figure says on its face that it is mock."""
    missing = [n for n in RESULT_TABLES if not (tables / n).exists()]
    if missing:
        raise SystemExit(f"{tables} lacks {', '.join(missing)}: run scripts/paper_tables.py first")
    mock = any("MOCK DATA" in (tables / n).read_text(encoding="utf-8") for n in RESULT_TABLES)
    if mock and out.resolve() == GEN.resolve():
        raise SystemExit("these tables are mock data: their figure is not written into paper/generated")
    if not mock and "pilot" in (tables / RESULT_TABLES[0]).read_text(encoding="utf-8").lower():
        raise SystemExit("these tables are from a pilot: the result figure is for the final run")

    # A: per model and track
    per_track = []
    for name in RESULT_TABLES[:2]:
        _, header, rows = read_tables(tables / name)[0]
        c = column(header, "Task success rate, strict")
        got = [(r[0], number(r[c])) for r in rows]
        per_track.append(sorted([(m, v) for m, v in got if v], key=lambda x: x[1][0]))
    # B: Table 9a
    title, header, rows = next(t for t in read_tables(tables / RESULT_TABLES[2]) if t[0].startswith("Table 9a"))
    cols = [column(header, n) for n in ("Right on both sides", "Right in the scene only",
                                        "Right in the call list only", "Right on neither side")]
    pairs = [(r[0], [float(r[c]) for c in cols]) for r in rows if number(r[cols[0]])]
    pairs.sort(key=lambda x: x[1][0] / sum(x[1]))
    # C: categories, valid-only
    _, header, rows = read_tables(tables / RESULT_TABLES[3])[0]
    cs, ct = column(header, "Task success rate, valid-only"), column(header, "Target score, valid-only")
    cats, track = [], ""
    for r in rows:
        if r[0].startswith("**"):
            track = r[0].strip("*")
        elif not r[0].lstrip().startswith("*of which") and number(r[cs]) and number(r[ct]):
            cats.append((track, r[0], number(r[cs])[0], number(r[ct])[0]))

    na, nb, nc = max(len(t) for t in per_track), len(pairs), len(cats) + 2
    row = 0.155
    fig = plt.figure(figsize=(7.2, row * (na + nb + nc) + 3.3))
    gs = fig.add_gridspec(3, 2, height_ratios=[na, nb, nc], hspace=0.42 * 22 / max(na, 12), wspace=0.9,
                          top=0.955, bottom=0.04)

    def frame(ax, xlabel):
        ax.set_xlim(0, 1)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0", "0.25", "0.5", "0.75", "1"])
        ax.xaxis.grid(True)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0, labelsize=7)
        ax.spines["left"].set_visible(False)
        ax.set_xlabel(xlabel)

    for k, (head, rows_) in enumerate(zip(("Scene track", "Call-list track"), per_track)):
        ax = fig.add_subplot(gs[0, k])
        for y, (model, (v, ci)) in enumerate(rows_):
            script = "no model" in model
            if ci:
                ax.plot(ci, [y, y], color=INK, lw=1.4, solid_capstyle="round", zorder=2)
            ax.scatter([v], [y], s=26, marker="s" if script else "o", zorder=3, linewidth=1.1,
                       facecolor="white" if script else OI_BLUE, edgecolor=MUTED if script else "white")
        ax.set_yticks(range(len(rows_)), [m for m, _ in rows_])
        ax.set_ylim(-0.7, len(rows_) - 0.3)
        frame(ax, "Task success rate, strict")
        ax.set_title(("A  " if k == 0 else "") + head, loc="left", fontweight="bold")

    ax = fig.add_subplot(gs[1, :])
    # solid fills, in the colours that Figure 3 gives the two one-sided cells; the order of
    # the segments is fixed (both, scene only, call list only, neither), left to right
    styles = [("right on both sides", "#8a8a8a"), ("right in the scene only", OI_BLUE),
              ("right in the call list only", OI_ORANGE), ("right on neither side", "#ececec")]
    for y, (model, counts) in enumerate(pairs):
        left, total = 0.0, sum(counts)
        for (label, colour), n in zip(styles, counts):
            ax.barh(y, n / total, left=left, height=0.72, color=colour,
                    edgecolor="white", linewidth=0.6, label=label if y == 0 else None)
            left += n / total
    ax.set_yticks(range(len(pairs)), [m for m, _ in pairs])
    ax.set_ylim(-0.7, len(pairs) - 0.3)
    frame(ax, "Share of the pairs that have a target score")
    ax.xaxis.grid(False)
    ax.set_title("B  The same request in both formats (target-right on which side)", loc="left",
                 fontweight="bold", pad=20)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=4, fontsize=7,
              columnspacing=1.2, handlelength=1.6)

    ax = fig.add_subplot(gs[2, :])
    labels, y = [], 0
    for i, (track, cat, success, target) in enumerate(reversed(cats)):
        ax.plot([success, target], [y, y], color=MUTED, lw=1.0, zorder=1)
        ax.scatter([success], [y], s=30, marker="D", facecolor=OI_ORANGE, edgecolor="white", linewidth=0.8,
                   zorder=3, label="task success rate" if i == 0 else None)
        ax.scatter([target], [y], s=30, marker="o", facecolor=OI_GREEN, edgecolor="white", linewidth=0.8,
                   zorder=3, label="target score" if i == 0 else None)
        labels.append((y, f"{cat}  ({track.split()[0].lower()})"))
        y += 1
    ax.set_yticks([p for p, _ in labels], [s for _, s in labels])
    ax.set_ylim(-0.7, y - 0.3)
    frame(ax, "Score, valid answers only, mean over the models")
    ax.set_title("C  Where points are lost, by category and track", loc="left", fontweight="bold", pad=20)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=7)
    if mock:
        fig.text(0.5, 0.995, MOCK_NOTE, ha="center", va="top", fontsize=9, fontweight="bold", color="#a00000")
    out.mkdir(parents=True, exist_ok=True)
    save(fig, out, RESULT_NAME)
    rel = (out / f"{RESULT_NAME}.svg").resolve().relative_to((REPO / "paper").resolve())
    caption = RESULT_CAPTION.format(mock=" (MOCK DATA, every number is fake)" if mock else "", path=rel.as_posix())
    (out / f"{RESULT_NAME}.md").write_text(caption, encoding="utf-8")
    return out / f"{RESULT_NAME}.svg"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--generated", type=pathlib.Path, default=GEN,
                    help="directory holding figdata.json; figures are written next to it")
    ap.add_argument("--png", type=pathlib.Path, default=None,
                    help="also write PNG previews to this directory")
    ap.add_argument("--result-figure", type=pathlib.Path, default=None, metavar="DIR",
                    help="draw only the result figure of the paper (Figure 5) from the table_final_*.md "
                         "files in DIR, into DIR: paper/generated_mock for the dry run, paper/generated "
                         "for the final run")
    args = ap.parse_args(argv)
    global PNG_DIR
    PNG_DIR = args.png
    if PNG_DIR is not None:
        PNG_DIR.mkdir(parents=True, exist_ok=True)
    if args.result_figure is not None:
        print(f"wrote {result_figure(args.result_figure, args.result_figure)} (+ .pdf, .md)")
        return 0
    data = json.loads((args.generated / "figdata.json").read_text(encoding="utf-8"))
    tracks = sorted({k.rsplit("_", 1)[0] for k in data if k.endswith("_leaderboard")})
    made = []
    for track in tracks:
        for f in FIGURES:
            if f(data, args.generated, track):
                made.append(f"{f.__name__}[{track}]")
    print(f"wrote {len(made)} figures (svg + pdf) to {args.generated}: {', '.join(made)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
