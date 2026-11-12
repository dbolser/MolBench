#!/usr/bin/env python3
"""Assemble the paper: sections + generated numbers -> ``paper/molbench.md`` (+ HTML, PDF).

    python paper/build.py            # stdlib only; writes molbench.md and PENDING.md
    python paper/build.py --check    # same checks, writes nothing; exit 1 on any problem
    python paper/build.py --pdf      # also HTML and PDF, if pandoc (+ Chromium) are installed

No result is typed by hand in ``paper/sections/*.md``. The text uses four markers:

``{{key}}`` / ``{{key:.3f}}`` / ``{{key:.1%}}``
    A value from ``generated/values.json`` (written by ``scripts/paper_tables.py``),
    with an optional Python format spec. An unknown key is an error.
``{{key|PENDING: what}}``
    The same, but if the key is absent (or null) the visible tag ``⟦PENDING: what⟧`` is
    written instead. Used for numbers only the final run can supply: they fill
    themselves in when the key appears in ``values.json``.
``{{include:generated/table_x.md}}`` / ``{{include:generated/table_y.md|PENDING: what}}``
    A generated table (or any file under ``paper/``); the second form tolerates a file
    that does not exist yet.
``[@key]`` / ``[@a; @b]``
    A citation; every key must exist in ``references.bib``. References are numbered in
    order of first use and listed at the end.

A literal ``⟦PENDING: …⟧`` in the text marks design not yet built or a decision still
open. Every PENDING tag in the built paper is listed in ``paper/PENDING.md``.
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
BIB = PAPER / "references.bib"
OUT_MD = PAPER / "molbench.md"
OUT_PENDING = PAPER / "PENDING.md"

MARK = re.compile(r"\{\{([^{}]+)\}\}")
CITE = re.compile(r"\[(@[A-Za-z0-9_:.-]+(?:\s*;\s*@[A-Za-z0-9_:.-]+)*)\]")
PENDING = re.compile(r"⟦PENDING: ([^⟧]*)⟧")
IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


class BuildError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Values and includes
# --------------------------------------------------------------------------- #
def fmt_value(value, spec: str | None) -> str:
    if spec:
        return format(value, spec)
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}" if abs(value) >= 10000 else str(value)
    return str(value)


def substitute(text: str, values: dict, where: str, problems: list[str], depth: int = 0) -> str:
    """Resolve ``{{…}}`` markers (includes are resolved recursively, once)."""

    def repl(m: re.Match) -> str:
        body = m.group(1).strip()
        fallback = None
        if "|" in body:
            body, fallback = (s.strip() for s in body.split("|", 1))
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
def build(values: dict | None = None) -> tuple[str, list[dict], list[str]]:
    """Return (markdown, pending tags, problems). Nothing is written."""
    problems: list[str] = []
    if values is None:
        if not VALUES.exists():
            raise BuildError(f"{VALUES} not found: run scripts/paper_tables.py first")
        values = json.loads(VALUES.read_text(encoding="utf-8"))
    bib = parse_bib(BIB.read_text(encoding="utf-8")) if BIB.exists() else {}
    files = sorted(SECTIONS.glob("*.md"))
    if not files:
        raise BuildError(f"no sections in {SECTIONS}")
    chunks, pending = [], []
    for f in files:
        text = substitute(f.read_text(encoding="utf-8"), values, f"sections/{f.name}", problems)
        for m in PENDING.finditer(text):  # a tag may run over several lines
            pending.append({"section": f.name, "line": text.count("\n", 0, m.start()) + 1,
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
    header = (f"<!-- Built by paper/build.py from paper/sections/ and paper/generated/values.json "
              f"({values.get('run.label', '?')}, {status}). Do not edit: edit the sections. -->\n\n")
    build.unused_refs = unused  # type: ignore[attr-defined]
    return header + body + "\n", pending, problems


def pending_report(pending: list[dict], values: dict) -> str:
    lines = [
        "# PENDING — what the paper still waits for",
        "",
        "Generated by `paper/build.py`. Do not edit by hand.",
        "",
        f"Numbers currently come from: **{values.get('run.label', '?')}** "
        f"({values.get('run.status_tag', '?')}).",
        "",
        f"{len(pending)} tag(s) in the built paper. A tag written as `{{{{key|PENDING: …}}}}` in a "
        "section disappears by itself once `scripts/paper_tables.py` writes that key; a literal "
        "`⟦PENDING: …⟧` needs an edit.",
        "",
        "| # | Section | Line | Waiting for |",
        "|---:|:---|---:|:---|",
    ]
    for i, p in enumerate(pending, 1):
        lines.append(f"| {i} | `{p['section']}` | {p['line']} | {p['what'].replace('|', '/')} |")
    # Keys the sections ask for with a fallback: the contract the final run has to fill.
    keys = []
    for f in sorted(SECTIONS.glob("*.md")):
        for m in MARK.finditer(f.read_text(encoding="utf-8")):
            body = m.group(1)
            if "|" in body:
                k = body.split("|", 1)[0].strip()
                name = k if k.startswith("include:") else k.partition(":")[0].strip()
                present = ((PAPER / name[len("include:"):]).exists() if name.startswith("include:")
                           else values.get(name) is not None)
                keys.append((name, f.name, present))
    if keys:
        lines += ["", "## Keys and files the final run must supply", "",
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
table{border-collapse:collapse;font:8.5pt Helvetica,Arial,sans-serif;margin:1em 0;width:100%}
th,td{border-bottom:1px solid #ccc;padding:3px 6px;text-align:left}
th{border-bottom:2px solid #444} img{max-width:100%}
code{font-size:90%} blockquote{color:#444;border-left:3px solid #ccc;margin-left:0;padding-left:1em}
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
    subprocess.run([pandoc, str(md_path), "-f", "markdown+pipe_tables-citations", "-t", "html5",
                    "--standalone", "--embed-resources", "--metadata", "pagetitle=MolBench",
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="check only; write nothing")
    ap.add_argument("--pdf", action="store_true", help="also write molbench.html and molbench.pdf")
    args = ap.parse_args(argv)
    try:
        md, pending, problems = build()
    except BuildError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for p in problems:
        print(f"error: {p}", file=sys.stderr)
    if problems:
        return 1
    values = json.loads(VALUES.read_text(encoding="utf-8"))
    words = len(re.findall(r"\w+", re.sub(r"\|.*\|", "", md)))
    if not args.check:
        OUT_MD.write_text(md, encoding="utf-8")
        OUT_PENDING.write_text(pending_report(pending, values), encoding="utf-8")
    unused = getattr(build, "unused_refs", [])
    print(f"{'checked' if args.check else 'wrote'} {OUT_MD.name}: ~{words} words outside tables, "
          f"{len(pending)} PENDING tag(s), {len(unused)} uncited reference(s)"
          + (f" ({', '.join(unused)})" if unused else ""))
    if args.pdf and not args.check:
        made = render(OUT_MD)
        if made:
            print("also wrote " + ", ".join(made))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
