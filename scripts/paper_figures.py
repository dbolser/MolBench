#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Draw the paper's figures from ``paper/generated/figdata.json``.

    uv run scripts/paper_figures.py            # after scripts/paper_tables.py

Reads only ``figdata.json`` (written by ``scripts/paper_tables.py``), so the figures can
be redrawn without the raw archives. Writes ``paper/generated/fig_*.svg`` and ``.pdf``.

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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--generated", type=pathlib.Path, default=GEN,
                    help="directory holding figdata.json; figures are written next to it")
    ap.add_argument("--png", type=pathlib.Path, default=None,
                    help="also write PNG previews to this directory")
    args = ap.parse_args(argv)
    global PNG_DIR
    PNG_DIR = args.png
    if PNG_DIR is not None:
        PNG_DIR.mkdir(parents=True, exist_ok=True)
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
