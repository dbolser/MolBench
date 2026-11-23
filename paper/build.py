#!/usr/bin/env python3
"""Assemble the paper: sections + generated numbers -> ``paper/molbench.md`` (+ HTML, PDF).

    python paper/build.py            # stdlib only; writes molbench.md, si.md and PENDING.md
    python paper/build.py --check    # same checks, writes nothing; exit 1 on any problem
    python paper/build.py --pdf      # also HTML and PDF, if pandoc (+ Chromium) are installed

No result is typed by hand in ``paper/sections/*.md``. The text uses four markers:

``{{key}}`` / ``{{key:.3f}}`` / ``{{key:.1%}}``
    A value from ``generated/values.json`` (written by ``scripts/paper_tables.py``: numbers
    of a model run) or ``generated/corpus_values.json`` (written by
    ``paper/corpus_values.py``: everything else), with an optional Python format spec. An
    unknown key is an error, and so is a key that both files define.
``{{key|PENDING: what}}``
    The same, but if the key is absent (or null) the visible tag ``⟦PENDING: what⟧`` is
    written instead. Used for numbers only the final run can supply: they fill
    themselves in when the key appears in ``values.json``.
``{{include:generated/table_x.md}}`` / ``{{include:generated/table_y.md|PENDING: what}}``
    A generated table (or any file under ``paper/``); the second form tolerates a file
    that does not exist yet. ``{{include:generated/table_y.md|else:generated/shape_y.md}}``
    shows the second file until the first exists: the table in its final shape, with
    pending cells, until the final run writes the real one.
``[@key]`` / ``[@a; @b]``
    A citation; every key must exist in ``references.bib``. References are numbered in
    order of first use and listed at the end.

A literal ``⟦PENDING: …⟧`` in the text marks something only the final run, the corpus
freeze or an author decision can supply. The first words of a tag say which (see
``FILLED_BY``); ``paper/PENDING.md`` lists every tag of the paper and of the Supporting
Information with what fills it. The Supporting Information is built the same way from
``paper/si/*.md`` into ``paper/si.md``, and the plain-language summary for volunteer raters
from ``paper/plain/`` into ``paper/plain_summary.md`` (its length is checked, as is the
abstract's).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata

PAPER = pathlib.Path(__file__).resolve().parent
SECTIONS = PAPER / "sections"
VALUES = PAPER / "generated" / "values.json"
CORPUS_VALUES = PAPER / "generated" / "corpus_values.json"
SI_SECTIONS = PAPER / "si"
OUT_SI = PAPER / "si.md"
PLAIN_SECTIONS = PAPER / "plain"
OUT_PLAIN = PAPER / "plain_summary.md"
ABSTRACT_MAX_WORDS = 200          # the brief for this paper; JCIM asks for a short abstract
PLAIN_WORDS = (135, 165)          # "a 150-word plain-language summary"
BIB = PAPER / "references.bib"
OUT_MD = PAPER / "molbench.md"
OUT_PENDING = PAPER / "PENDING.md"

MARK = re.compile(r"\{\{([^{}]+)\}\}")
CITE = re.compile(r"\[(@[A-Za-z0-9_:.-]+(?:\s*;\s*@[A-Za-z0-9_:.-]+)*)\]")
PENDING = re.compile(r"⟦PENDING: ([^⟧]*)⟧")
IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


class BuildError(Exception):
    pass


# What fills a PENDING tag, by how the tag starts. A tag that starts in no listed way is
# reported by ``build.py --check`` so that no tag is left without an owner.
FILLED_BY = [
    ("final run", "The paid run (`python -m molbench.runner --manifest run/final_run.toml --go`), then "
                  "`scripts/paper_tables.py` on its archives. A table shown in its final shape is replaced "
                  "when the script writes the file named under \"Keys and files\" below."),
    ("corpus freeze", "The freeze of the corpus (version tag and hash pinned in `run/final_run.toml`), "
                      "then `paper/corpus_values.py`."),
    ("rating study", "The second rating study (design: `paper/a4/FINAL_CALL.md`), run on the final run's "
                     "scenes; `scripts/agreement.py` writes the numbers."),
    ("deposit", "Depositing the frozen corpus, the run archives and the ratings in a public repository "
                "that issues a DOI."),
    ("Dan", "An author decision or author-supplied text."),
]


def filled_by(what: str) -> str | None:
    """The owner of a tag: the entry of ``FILLED_BY`` that the tag starts with (its first words)."""
    for start, _ in FILLED_BY:
        if what.startswith(start):
            return start
    return None


def load_values() -> dict:
    """``values.json`` and ``corpus_values.json`` as one dictionary; no key may be in both."""
    if not VALUES.exists():
        raise BuildError(f"{VALUES} not found: run scripts/paper_tables.py first")
    values = json.loads(VALUES.read_text(encoding="utf-8"))
    if CORPUS_VALUES.exists():
        more = json.loads(CORPUS_VALUES.read_text(encoding="utf-8"))
        both = sorted(set(values) & set(more))
        if both:
            raise BuildError(f"keys defined in both value files: {both[:5]}")
        values.update(more)
    return values


# --------------------------------------------------------------------------- #
# Values and includes
# --------------------------------------------------------------------------- #
NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


def fmt_value(value, spec: str | None) -> str:
    if spec == "word":          # a small count in running prose: "three times"; 10 and above stay digits
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("'word' needs a whole number")
        return NUMBER_WORDS[value] if 0 <= value < len(NUMBER_WORDS) else f"{value:,}"
    if spec in ("date", "month"):   # an ISO date as "13 November 2026", or as "November 2026"
        m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(value))
        if not m:
            raise ValueError(f"'{spec}' needs a value of the form YYYY-MM-DD")
        month = f"{MONTHS[int(m.group(2)) - 1]} {m.group(1)}"
        return month if spec == "month" else f"{int(m.group(3))} {month}"
    if spec:
        return format(value, spec)
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}" if abs(value) >= 10000 else str(value)
    return str(value)


# The pilot tables of SI Section S8 are written by scripts/paper_tables.py in the words of
# October 2026. They are shown with a table number and in the words of the paper; the map
# below changes words only, never a number. Order matters (longer forms first).
PILOT_WORDS = [
    (r"`spec_grounded`", "main + grounding pack"),
    (r"`bare_grounded`", "no format guide + grounding pack"),
    (r"`_grounded`", "+ grounding pack"),
    (r"`spec`", "main"),
    (r"`bare`", "no format guide"),
    (r"\bMVS track\b", "Scene track"),
    (r"Corpus used for the October 2026 panel", "Corpus of the October 2026 pilot run"),
    (r"the frozen MolViewSpec reference", "the format guide"),
    (r"only the output contract", "only the rule for the answer"),
    (r"as in the leaderboard table", "as in the per-model table"),
    (r"image-pair judge model", "image judge"),
    (r"[Tt]ask × model pairs", lambda m: ("T" if m.group(0)[0] == "T" else "t") + "ask-model combinations"),
    (r"of those pairs", "of those combinations"),
    (r"\bA regime is\b", "A category is"),
    (r"\bregimes\b", "categories"), (r"\bregime\b", "category"), (r"\bRegime\b", "Category"),
    (r"\bOutputs\b", "Answers"), (r"\bOutput\b", "Answer"),
    (r"\boutputs\b", "answers"), (r"\boutput\b", "answer"),
    (r"\bResolution\b", "Name resolution"),
    (r"\bGrounded\b", "Structure-grounded"),
    (r"\b(\d+) samples? per task", lambda m: f"{m.group(1)} answer{'' if m.group(1) == '1' else 's'} per task"),
    (r"95% CIs\b", "95% intervals"), (r"95% CI\b", "95% interval"),
    (r"\(PRELIMINARY\)", "(pilot run, preliminary, earlier grader)"),
    # Words that the paper defines otherwise (Section 4.2): in the pilot tables "target" was the
    # requested part read from the reference, "success" a score of 1 under the earlier grader,
    # and "tree F1" or "tree score" that grader's F1.
    (r"the target atoms are selected", "the atoms of the requested part are selected"),
    (r"The \*target\* of a task", "The *requested part* of a task"),
    (r"every target with", "every requested part with"),
    (r"the target is right", "the requested part is right"),
    (r"selects exactly the target atoms", "selects exactly the atoms of the requested part"),
    (r"\bTarget (exact|wrong)\b", lambda m: "Requested part " + m.group(1)),
    (r"\bSuccess\b", "Score of 1"),
    (r"whether the model weights are openly released", "open if the weights of the model can be downloaded"),
    (r"Tree score vs render-checked score", "Earlier-grader F1 against the score after a check of the picture"),
    # Table S19 (the check of pictures in October): column heads and caption in plain words.
    (r"A valid scene that scores below 1 is \*escalated\*: it is rendered next to the reference\. It is "
     r"\*rescued\* \(counted as correct\) if",
     "A valid scene that scores below 1 is rendered next to the reference (*pictures compared*). It is "
     "*counted right* if"),
    (r"\*Validated F1\* is the tree F1 with rescued scenes set to 1\. Scores are never lowered by escalation\.",
     "*F1 after picture check* is the earlier-grader F1 with the scenes that were counted right set to 1. "
     "The check never lowers a score."),
    (r"\bValidated F1\b", "F1 after picture check"),
    (r"\bEscalated\b", "Pictures compared"),
    (r"\bRescued \(pixels\)", "Counted right: pictures identical"),
    (r"\bRescued \(judge\)", "Counted right: image judge says same"),
    (r"Read the thin rows with care: the sample sizes are in the table\.",
     "Rows with few tasks must be read with care: the numbers of tasks are in the table."),
    (r"\bTree F1\b", "Earlier-grader F1"), (r"\btree F1\b", "earlier-grader F1"),
    (r"\btree score\b", "earlier-grader F1"),
]


def pilot_table(text: str, label: str) -> str:
    """A pilot table with its number and in the paper's words (see PILOT_WORDS)."""
    for pattern, new in PILOT_WORDS:
        text = re.sub(pattern, new, text)
    if not text.startswith("**"):
        raise BuildError(f"pilot table for {label} does not start with a bold title")
    return f"**{label}. " + text[2:]


def substitute(text: str, values: dict, where: str, problems: list[str], depth: int = 0) -> str:
    """Resolve ``{{…}}`` markers (includes are resolved recursively, once)."""

    def repl(m: re.Match) -> str:
        body = m.group(1).strip()
        fallback = None
        if "|" in body:
            body, fallback = (s.strip() for s in body.split("|", 1))
            if body.startswith("include:") and fallback.startswith("else:"):
                first = (PAPER / body[len("include:"):].strip())
                rel = body[len("include:"):].strip() if first.exists() else fallback[len("else:"):].strip()
                f = (PAPER / rel).resolve()
                if PAPER not in f.parents or not f.exists():
                    problems.append(f"{where}: missing include {rel}")
                    return m.group(0)
                return substitute(f.read_text(encoding="utf-8").rstrip(), values, rel, problems,
                                  depth + 1)
            if body.startswith("include:") and fallback.startswith("pilot:"):
                rel = body[len("include:"):].strip()
                f = (PAPER / rel).resolve()
                if PAPER not in f.parents or not f.exists():
                    problems.append(f"{where}: missing include {rel}")
                    return m.group(0)
                return pilot_table(f.read_text(encoding="utf-8").rstrip(), fallback[len("pilot:"):].strip())
            if not fallback.startswith("PENDING:"):
                problems.append(f"{where}: fallback must start with 'PENDING:' in {{{{{m.group(1)}}}}}")
                return m.group(0)
            fallback = f"⟦{fallback}⟧"
        if body.startswith("include:"):
            rel = body[len("include:"):].strip()
            f = (PAPER / rel).resolve()
            if PAPER not in f.parents:
                problems.append(f"{where}: include outside paper/: {rel}")
                return m.group(0)
            if not f.exists():
                if fallback:
                    return fallback
                problems.append(f"{where}: missing include {rel}")
                return m.group(0)
            if depth > 2:
                problems.append(f"{where}: include nesting too deep at {rel}")
                return m.group(0)
            return substitute(f.read_text(encoding="utf-8").rstrip(), values, rel, problems,
                              depth + 1)
        key, _, spec = body.partition(":")
        key = key.strip()
        if key not in values or values[key] is None:
            if fallback:
                return fallback
            problems.append(f"{where}: unresolved value key '{key}'")
            return m.group(0)
        try:
            return fmt_value(values[key], spec.strip() or None)
        except (ValueError, TypeError) as e:
            problems.append(f"{where}: cannot format '{key}' with '{spec}': {e}")
            return m.group(0)

    return MARK.sub(repl, text)


# --------------------------------------------------------------------------- #
# References
# --------------------------------------------------------------------------- #
_ACCENT = {'"': "\u0308", "'": "\u0301", "`": "\u0300", "^": "\u0302", "~": "\u0303",
           "c": "\u0327", "v": "\u030c", "u": "\u0306", "H": "\u030b", "k": "\u0328",
           "r": "\u030a", "=": "\u0304", ".": "\u0307"}
_LATEX_ACCENT = re.compile(r"""\\(["'`^~=.]|[cvuHkr](?![A-Za-z]))\s*(?:\{([A-Za-z])\}|([A-Za-z]))""")


def delatex(text: str) -> str:
    """BibTeX text as plain Unicode: accents, quotes and escaped characters."""
    text = _LATEX_ACCENT.sub(lambda m: unicodedata.normalize(
        "NFC", (m.group(2) or m.group(3)) + _ACCENT[m.group(1)]), text)
    text = text.replace("``", "\u201c").replace("''", "\u201d")
    text = re.sub(r"\\([_&%#$])", r"\1", text)
    return text.replace("{", "").replace("}", "")


def parse_bib(text: str) -> dict[str, dict]:
    """A small BibTeX reader: ``@type{key, field = {value}, …}`` with braces or quotes."""
    out: dict[str, dict] = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        kind, key = m.group(1).lower(), m.group(2)
        if kind in ("comment", "string", "preamble"):
            continue
        i, depth = m.end(), 1
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        body = text[m.end():i - 1]
        fields = {"_type": kind}
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            j = fm.end()
            if j >= len(body):
                continue
            if body[j] == "{":
                d, k = 1, j + 1
                while k < len(body) and d:
                    d += {"{": 1, "}": -1}.get(body[k], 0)
                    k += 1
                val = body[j + 1:k - 1]
            elif body[j] == '"':
                k = body.index('"', j + 1)
                val = body[j + 1:k]
            else:
                k = j
                while k < len(body) and body[k] not in ",\n":
                    k += 1
                val = body[j:k]
            name = fm.group(1).lower()
            if name not in fields:
                fields[name] = " ".join(delatex(val).split())
        out[key] = fields
    return out


def fmt_authors(raw: str) -> str:
    names = [n.strip() for n in raw.split(" and ") if n.strip()]
    short = []
    for n in names:
        if n.lower() == "others":
            short.append("et al.")
            continue
        if "," in n:
            last, first = (s.strip() for s in n.split(",", 1))
            initials = "".join(p[0] for p in re.split(r"[\s-]+", first) if p)
            short.append(f"{last} {initials}".strip())
        else:
            short.append(n)
    if len(short) > 8:
        short = short[:8] + ["et al."]
    return ", ".join(short).replace(", et al.", " et al.")


def fmt_reference(e: dict) -> str:
    parts = []
    if e.get("author"):
        parts.append(fmt_authors(e["author"]).rstrip(".") + ".")
    parts.append(e.get("title", "(untitled)").rstrip(".") + ".")
    venue = e.get("journal") or e.get("booktitle") or e.get("howpublished") or e.get("publisher")
    tail = []
    if venue:
        tail.append(f"*{venue}*")
    if e.get("year"):
        tail.append(e["year"])
    cite = " ".join(tail)
    vol = e.get("volume", "")
    if e.get("number"):
        vol += f"({e['number']})"
    if vol:
        cite += f";{vol}"
    if e.get("pages"):
        cite += f":{e['pages'].replace('--', '–')}"
    if cite:
        parts.append(cite + ".")
    if e.get("note"):
        parts.append(e["note"].rstrip(".") + ".")
    if e.get("doi"):
        parts.append(f"doi:[{e['doi']}](https://doi.org/{e['doi']})")
    elif e.get("eprint"):
        parts.append(f"arXiv:[{e['eprint']}](https://arxiv.org/abs/{e['eprint']})")
    if e.get("url") and not e.get("doi"):
        parts.append(f"<{e['url']}>")
    return " ".join(parts)


def resolve_citations(text: str, bib: dict, problems: list[str]) -> tuple[str, list[str]]:
    order: list[str] = []

    def repl(m: re.Match) -> str:
        nums = []
        for key in re.findall(r"@([A-Za-z0-9_:.-]+)", m.group(1)):
            if key not in bib:
                problems.append(f"citation '{key}' is not in references.bib")
                continue
            if key not in order:
                order.append(key)
            nums.append(order.index(key) + 1)
        return "[" + ", ".join(str(n) for n in sorted(nums)) + "]" if nums else m.group(0)

    return CITE.sub(repl, text), order


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #
def build(values: dict | None = None, sections: pathlib.Path | None = None
          ) -> tuple[str, list[dict], list[str]]:
    """Return (markdown, pending tags, problems). Nothing is written. ``sections`` is the
    directory to assemble (default: the paper; ``SI_SECTIONS`` for the Supporting Information)."""
    problems: list[str] = []
    if values is None:
        values = load_values()
    sections = sections or SECTIONS
    bib = parse_bib(BIB.read_text(encoding="utf-8")) if BIB.exists() else {}
    files = sorted(sections.glob("*.md"))
    if not files:
        raise BuildError(f"no sections in {sections}")
    chunks, pending = [], []
    for f in files:
        text = substitute(f.read_text(encoding="utf-8"), values, f"{sections.name}/{f.name}", problems)
        for m in PENDING.finditer(text):  # a tag may run over several lines
            pending.append({"section": f"{sections.name}/{f.name}",
                            "line": text.count("\n", 0, m.start()) + 1,
                            "what": " ".join(m.group(1).split())})
        chunks.append(text.strip())
    body = "\n\n".join(chunks)
    body, order = resolve_citations(body, bib, problems)
    if order:
        refs = "\n".join(f"{i}. {fmt_reference(bib[k])}" for i, k in enumerate(order, 1))
        body += "\n\n## References\n\n" + refs
    unused = sorted(set(bib) - set(order))
    for m in IMAGE.finditer(body):
        if not m.group(1).startswith("http") and not (PAPER / m.group(1)).exists():
            problems.append(f"missing figure file {m.group(1)}")
    if MARK.search(body):
        problems += [f"marker left unresolved: {m.group(0)}" for m in MARK.finditer(body)]
    status = values.get("run.status_tag", "")
    header = (f"<!-- Built by paper/build.py from paper/{sections.name}/ and paper/generated/*.json "
              f"(run numbers: {values.get('run.label', '?')}, {status}). Do not edit: edit the sources. -->\n\n")
    build.unused_refs = unused  # type: ignore[attr-defined]
    return header + body + "\n", pending, problems


def pending_report(pending: list[dict], values: dict) -> str:
    """PENDING.md: every tag of the paper (``pending``) and of the Supporting Information,
    grouped where one tag repeats (the cells of a table), each with what fills it."""
    rows = list(pending)
    if SI_SECTIONS.exists() and any(SI_SECTIONS.glob("*.md")) and not any(
            p["section"].startswith(SI_SECTIONS.name + "/") for p in pending):
        try:
            rows += build(sections=SI_SECTIONS)[1]
        except BuildError:
            pass
    groups: dict[tuple, dict] = {}
    for p in rows:
        g = groups.setdefault((p["section"], p["what"]), {"n": 0, "line": p["line"]})
        g["n"] += 1
    lines = [
        "# PENDING — what the paper still waits for",
        "",
        "Generated by `paper/build.py`. Do not edit by hand.",
        "",
        f"Run numbers currently come from: **{values.get('run.label', '?')}** "
        f"({values.get('run.status_tag', '?')}). They appear only in the boxed "
        "\"Preliminary evidence\" subsection.",
        "",
        f"{len(rows)} tag(s) in the built paper and Supporting Information, in {len(groups)} "
        "distinct places. The first words of a tag say what fills it.",
        "",
        "| Filled by | Tags | How |",
        "|:---|---:|:---|",
    ]
    for start, how in FILLED_BY:
        n = sum(g["n"] for (_, what), g in groups.items() if filled_by(what) == start)
        lines.append(f"| **{start}** | {n} | {how} |")
    lines += ["",
              "| # | Source file | First line | Times | Waiting for | Filled by |",
              "|---:|:---|---:|---:|:---|:---|"]
    for i, ((section, what), g) in enumerate(groups.items(), 1):
        how = filled_by(what) or "**not classified: start the tag with one of the words in `FILLED_BY`**"
        lines.append(f"| {i} | `{section}` | {g['line']} | {g['n']} | {what.replace('|', '/')} | {how} |")
    # Files the sections ask for with a fallback: the contract the final run has to fill.
    keys = []
    for d in (SECTIONS, SI_SECTIONS):
        for f in sorted(d.glob("*.md")) if d.exists() else []:
            for m in MARK.finditer(f.read_text(encoding="utf-8")):
                body = m.group(1)
                if "|" in body:
                    k = body.split("|", 1)[0].strip()
                    name = k if k.startswith("include:") else k.partition(":")[0].strip()
                    present = ((PAPER / name[len("include:"):]).exists() if name.startswith("include:")
                               else values.get(name) is not None)
                    keys.append((name, f"{d.name}/{f.name}", present))
    if keys:
        lines += ["", "## Keys and files the final run must supply", "",
                  "`scripts/paper_tables.py` is expected to write these from the final archives. Until a "
                  "file exists, the paper shows the same table in its final shape with pending cells "
                  "(`generated/shape_*.md`, written by `paper/corpus_values.py`).", "",
                  "| Key or file | Used in | Present now |", "|:---|:---|:---|"]
        seen = set()
        for name, sec, present in keys:
            if (name, sec) in seen:
                continue
            seen.add((name, sec))
            lines.append(f"| `{name}` | `{sec}` | {'yes' if present else 'no'} |")
    return "\n".join(lines) + "\n"


CSS = """
body{font:11pt/1.5 Georgia,serif;max-width:46em;margin:2em auto;padding:0 1em;color:#111}
h1,h2,h3{font-family:Helvetica,Arial,sans-serif;line-height:1.25}
table{border-collapse:collapse;font:8.5pt Helvetica,Arial,sans-serif;margin:1em 0;width:100%;break-inside:avoid}
th,td{border-bottom:1px solid #ccc;padding:3px 6px;text-align:left;vertical-align:top}
th{border-bottom:2px solid #444} tr{break-inside:avoid} p:has(+ table){break-after:avoid}
img{max-width:100%} figure{break-inside:avoid} figure img{width:100%}
code{font-size:90%} pre{font-size:8.5pt;background:#f6f6f6;padding:8px;overflow-x:auto;white-space:pre-wrap}
blockquote{border:1.5px solid #555;border-radius:4px;margin:1.2em 0;padding:.4em 1em;background:#fafafa}
blockquote table{background:#fff} figure{margin:1.2em 0} figcaption{font-size:9.5pt;color:#222}
div.box{border:1.5px solid #555;border-radius:4px;margin:1.2em 0;padding:.2em 1em;background:#fafafa}
div.box table{background:#fff}
@page{size:A4;margin:18mm}
"""


def find_chromium() -> str | None:
    """A Chromium that actually runs: one on PATH, or the one Playwright downloaded."""
    cands = [shutil.which(c) for c in ("chromium", "chromium-browser", "google-chrome", "chrome")]
    cache = pathlib.Path.home() / ".cache" / "ms-playwright"
    cands += [str(f) for f in sorted(cache.glob("chromium-*/chrome-linux*/chrome"), reverse=True)]
    for c in cands:
        if not c:
            continue
        try:  # a distro stub ("install the snap") exits non-zero here
            if subprocess.run([c, "--version"], capture_output=True, timeout=20).returncode == 0:
                return c
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def render(md_path: pathlib.Path) -> list[str]:
    """HTML via pandoc and PDF via headless Chromium, when those tools exist."""
    made = []
    pandoc = shutil.which("pandoc")
    if not pandoc:
        print("pandoc not found: skipping HTML and PDF", file=sys.stderr)
        return made
    html = md_path.with_suffix(".html")
    css = PAPER / "generated" / "_paper.css"
    css.write_text(CSS, encoding="utf-8")
    subprocess.run([pandoc, str(md_path), "-f", "markdown+pipe_tables+implicit_figures-citations", "-t", "html5",
                    "--standalone", "--embed-resources", "--metadata",
                    "pagetitle=MolBench" + (" — Supporting Information" if md_path == OUT_SI else ""),
                    "--metadata", "lang=en", "--css", str(css), "--resource-path", str(PAPER),
                    "-o", str(html)], check=True, cwd=PAPER)
    css.unlink()
    made.append(html.name)
    chrome = find_chromium()
    if not chrome:
        print("Chromium not found: skipping PDF", file=sys.stderr)
        return made
    pdf = md_path.with_suffix(".pdf")
    r = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf}", html.as_uri()],
                       capture_output=True, text=True, timeout=180)
    if r.returncode == 0 and pdf.exists():
        made.append(pdf.name)
    else:
        print(f"PDF step failed ({r.returncode}): {r.stderr[-300:]}", file=sys.stderr)
    return made


REPRESENTATION_WORDS = ("ball-and-stick", "ball_and_stick", "spacefill", "cartoon", "surface", "line", "putty")


def example_problems(values: dict) -> list[str]:
    """The running example must look the same wherever it is shown: the generated table and
    the two figures of it must state the colour and the representation of the request, and
    no other representation for the requested residue."""
    problems = []
    colour, rep = values.get("ex.color"), values.get("ex.rep_short")
    if not colour or not rep:
        return ["generated values lack ex.color / ex.rep_short: run paper/corpus_values.py"]
    if f"{colour} {values['ex.rep']}" not in values.get("ex.prompt", ""):
        problems.append("the request of the running example does not state its colour and representation")
    for name in ("table_example.md", "fig_grading.svg", "fig_twins.svg"):
        f = PAPER / "generated" / name
        text = f.read_text(encoding="utf-8") if f.exists() else ""
        if colour not in text or (rep not in text and values["ex.rep_scene"] not in text):
            problems.append(f"generated/{name} does not show the running example as {colour} {rep}")
        other = [w for w in REPRESENTATION_WORDS
                 if w not in (rep, values["ex.rep_scene"], "cartoon", "line") and w in text
                 # the table also grades answers that add another representation, and says so
                 and not (name == "table_example.md" and w == values.get("ex.other_rep"))]
        if other:
            problems.append(f"generated/{name} names a representation the request does not ask for: {other}")
    return problems


# Numbers that the prose states in words. If one of them changes, the sentence must change:
# (key, value, where the words are).
STATED_IN_WORDS = [
    ("plan.samples", 3, "'at least 2 of its 3 answers' (Sections 4.2 and 5.4, Table 9, Figures 3 and 5)"),
    ("mvs.spec.regime.Clinical.n_structures", 1, "'a single structure' (Section 6.6, Finding 2; abstract)"),
    ("study.max_per_task_model", 1, "'from the same model' (Section 5.5)"),
    ("panel.n_disease_proteins_without_task", 2, "the two proteins without a task, named in Section 3.1"),
    ("clin.n_tasks_kept_by_name", 1, "'1 task per track' for lysozyme p.Ile74Thr (Section 3.1)"),
    ("prompt.longer_track", "call-list", "the order of the two prompt lengths (Sections 5.2 and 9.4)"),
    ("ex.n_clinvar_records", 2, "'both DNA changes', 'both are classified' (Sections 1 and 3.2, SI Section S1)"),
    ("clin.n_face_wrong_no_offset", 1, "'the one remaining traditional name' (Section 3.3.1)"),
    ("clin.n_same_numbering_pairs", 2, "'in the other 2 sets' of matched tasks, both of p53 (Section 3.3.1)"),
    ("corpus.followup.noop_spin", 2, "'in 2 scene tasks, a spin' (Section 3.3, follow-up turn)"),
    ("mvs.spec.outcome.not_mvs", 0, "'no answer of the pilot run fell in the class' (SI Section S8)"),
    ("mvs.spec.samples_per_task", 1, "'one answer per task' in the pilot run (Section 6.6, Table 13)"),
]


def stated_in_words_problems(values: dict) -> list[str]:
    return [f"the text states {key} = {want!r} in words, but the value is {values.get(key)!r}: {where}"
            for key, want, where in STATED_IN_WORDS if values.get(key) != want]


def words(md: str) -> int:
    """Words outside tables, code blocks, figure captions, HTML comments and the reference list."""
    md = md.split("\n## References")[0]
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    md = re.sub(r"^\|.*\|\s*$", "", md, flags=re.M)
    md = re.sub(r"^!\[.*$", "", md, flags=re.M)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", md))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="check only; write nothing")
    ap.add_argument("--pdf", action="store_true", help="also write HTML and PDF of both documents")
    args = ap.parse_args(argv)
    docs = [(SECTIONS, OUT_MD)] + [(d, o) for d, o in ((SI_SECTIONS, OUT_SI), (PLAIN_SECTIONS, OUT_PLAIN))
                                   if d.exists() and any(d.glob("*.md"))]
    try:
        values = load_values()
        built = [(out, *build(values, sec)) for sec, out in docs]
    except BuildError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    problems = [p for _, _, _, probs in built for p in probs]
    problems += example_problems(values)
    problems += stated_in_words_problems(values)
    for _, _, pending, _ in built:
        problems += [f"{p['section']}:{p['line']}: PENDING tag with no owner: {p['what']!r}"
                     for p in pending if not filled_by(p["what"])]
    abstract = re.search(r"## Abstract\n(.*?)\n## ", built[0][1], flags=re.S)
    n_abstract = words(PENDING.sub("", abstract.group(1))) if abstract else 0
    if n_abstract > ABSTRACT_MAX_WORDS:
        problems.append(f"abstract has {n_abstract} words (limit {ABSTRACT_MAX_WORDS}, PENDING tags not counted)")
    for out, md, _, _ in built:
        if out == OUT_PLAIN:
            n_plain = words(re.sub(r"^(#.*|\*.*\*)$", "", md, flags=re.M))
            if not PLAIN_WORDS[0] <= n_plain <= PLAIN_WORDS[1]:
                problems.append(f"plain-language summary has {n_plain} words (wanted {PLAIN_WORDS[0]}-{PLAIN_WORDS[1]})")
    for p in problems:
        print(f"error: {p}", file=sys.stderr)
    if problems:
        return 1
    report = pending_report(built[0][2], values)
    stale = []
    for out, md, pending, _ in built:
        if args.check:
            if not out.exists() or out.read_text(encoding="utf-8") != md:
                stale.append(out.name)
        else:
            out.write_text(md, encoding="utf-8")
        print(f"{'checked' if args.check else 'wrote'} {out.name}: ~{words(md)} words of text, "
              f"{len(pending)} PENDING tag(s)")
    if args.check:
        if not OUT_PENDING.exists() or OUT_PENDING.read_text(encoding="utf-8") != report:
            stale.append(OUT_PENDING.name)
        for name in stale:
            print(f"error: {name} is stale: run python paper/build.py", file=sys.stderr)
        return 1 if stale else 0
    OUT_PENDING.write_text(report, encoding="utf-8")
    print(f"abstract: {n_abstract} words without PENDING tags (limit {ABSTRACT_MAX_WORDS})")
    if args.pdf:
        for out, _, _, _ in built:
            if out == OUT_PLAIN:        # an email text, not a document to typeset
                continue
            made = render(out)
            if made:
                print("also wrote " + ", ".join(made))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
