#!/usr/bin/env python3
"""
A4: export the human ratings to a local file, read-only, with pseudonyms.

Runs ONE select against the rating site's database (Supabase Management API) and
writes two files next to the private answer key, both git-ignored:

  ratings.json   what scripts/agreement.py reads offline: one row per rating, the
                 rater named only by a pseudonym (R1, R2, ...), plus each
                 pseudonym's role ("rater", "author" or "test"). No names, no
                 invite tokens.
  raters.json    PRIVATE name map: pseudonym -> name, invite token, role. Reused on
                 the next export, so pseudonyms stay stable as raters are added
                 (numbered in order of first rating). Never commit or print it.

Roles are set here and nowhere else:
  --author NAME  the benchmark author's own rating token. Kept as a rater, but
                 agreement.py reports every result with and without it.
  --test NAME    a testing-only token; agreement.py drops its ratings.

    python scripts/export_ratings.py --author "<name>" --test "<name>"

The access token is read from $SUPABASE_ACCESS_TOKEN or ~/.supabase/access-token.
Only a SELECT is ever sent.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
PROJECT = "dfdybtixipdgovagihfn"  # the molstar-chat-driver evaluator project
API = "https://api.supabase.com/v1/projects/{project}/database/query"
QUERY = """
select r.evaluator_token, e.name, r.item, r.label, r.ref_wrong, r.model_better,
       r.note, r.ms, r.client, r.created_at
from ratings r left join evaluators e on e.token = r.evaluator_token
where r.set_id = '{set_id}'
order by r.created_at, r.item
"""
ROLES = ("rater", "author", "test")
ROW_FIELDS = ("item", "label", "ref_wrong", "model_better", "note", "ms", "client", "created_at")


def access_token() -> str:
    tok = os.environ.get("SUPABASE_ACCESS_TOKEN")
    if not tok:
        tok = (pathlib.Path.home() / ".supabase" / "access-token").read_text()
    return tok.strip()


def fetch(set_id: str, project: str = PROJECT) -> list[dict]:
    """Every rating of one set, oldest first, joined to the evaluator's name."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", set_id):
        raise ValueError(f"unsafe set id: {set_id!r}")
    query = QUERY.format(set_id=set_id)
    assert query.lstrip().lower().startswith("select") and ";" not in query
    req = urllib.request.Request(
        API.format(project=project), data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"Bearer {access_token()}", "Content-Type": "application/json",
                 "User-Agent": "molbench-export/1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def pseudonymise(rows: list[dict], known: dict, author: set[str] = frozenset(),
                 test: set[str] = frozenset()) -> tuple[list[dict], dict]:
    """(public rows, name map). `known` is the earlier name map; its pseudonyms are kept.

    Rows must be oldest first: new raters are numbered in order of first rating.
    A role given on the command line replaces the stored one; otherwise it is kept.
    """
    names = {p: dict(v) for p, v in known.items()}
    by_token = {v["token"]: p for p, v in names.items()}
    n = max((int(p[1:]) for p in names), default=0)
    out = []
    for row in rows:
        tok = row["evaluator_token"]
        if tok not in by_token:
            n += 1
            by_token[tok] = f"R{n}"
            names[f"R{n}"] = {"token": tok, "name": row.get("name"), "role": "rater"}
        out.append({"rater": by_token[tok], **{f: row.get(f) for f in ROW_FIELDS}})
    for p, v in names.items():
        if v["name"] in author:
            v["role"] = "author"
        elif v["name"] in test:
            v["role"] = "test"
    return out, names


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", dest="set_id", default="a4-v1")
    ap.add_argument("--out", type=pathlib.Path,
                    help="output directory (default: results/a4/<set>/, git-ignored)")
    ap.add_argument("--author", action="append", default=[], metavar="NAME",
                    help="evaluator name of the benchmark author's rating token (repeatable)")
    ap.add_argument("--test", action="append", default=[], metavar="NAME",
                    help="evaluator name of a testing-only token (repeatable)")
    a = ap.parse_args(argv)
    out = a.out or REPO / "results" / "a4" / a.set_id
    out.mkdir(parents=True, exist_ok=True)
    map_path = out / "raters.json"
    known = json.loads(map_path.read_text()) if map_path.exists() else {}

    rows, names = pseudonymise(fetch(a.set_id), known, set(a.author), set(a.test))
    missing = [n for n in (*a.author, *a.test) if n not in {v["name"] for v in names.values()}]
    map_path.write_text(json.dumps(names, indent=1, sort_keys=True) + "\n")
    map_path.chmod(0o600)
    export = {
        "set": a.set_id,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "raters": {p: {"role": v["role"]} for p, v in sorted(names.items(), key=lambda kv: int(kv[0][1:]))},
        "rows": rows,
    }
    (out / "ratings.json").write_text(json.dumps(export, indent=1) + "\n")
    per = {p: sum(r["rater"] == p for r in rows) for p in export["raters"]}
    print(f"{len(rows)} ratings -> {out / 'ratings.json'}")
    for p, v in export["raters"].items():
        print(f"  {p}  {v['role']:6}  {per[p]} ratings")
    if missing:  # a name with no ratings in this set has no pseudonym; say so without failing
        print(f"  note: {len(missing)} name(s) given with --author/--test have no ratings in this set")


if __name__ == "__main__":
    main()
