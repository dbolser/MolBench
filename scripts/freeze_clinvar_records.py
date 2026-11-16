"""Freeze ClinVar's own record for every variation the panel's variant lists rest on.

``scripts/build_panel.py`` kept a missense variant when a ClinVar variation record (VCV)
with the same protein change is classified pathogenic or likely pathogenic. It did not
keep *what kind of record* that was. The audit of 2026-11-16 found three kinds that do
not back the sentence "the <gene> variant ... is classified as pathogenic in ClinVar":

* a record of **another gene** that encodes the same protein (CALM2 and CALM3 for
  calmodulin, HBA2 for alpha-globin);
* a **haplotype** record (two changes in cis), which says nothing about the single
  variant;
* a record with **no assertion criteria** (zero stars).

This script asks NCBI E-utilities (free, no key) for the summary of every VCV named in
``data/panel/variants/*.json`` and writes the fields the filters need to
``data/panel/clinvar_records.json``. ``molbench.variants.confirmed`` reads that file
and nothing else; nothing is fetched when tasks are generated, loaded or graded.

    uv run python scripts/freeze_clinvar_records.py           # fetch and write
    uv run python scripts/freeze_clinvar_records.py --check   # every VCV has a record
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
VARIANTS = REPO / "data" / "panel" / "variants"
OUT = REPO / "data" / "panel" / "clinvar_records.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def wanted() -> list[str]:
    out = set()
    for path in sorted(VARIANTS.glob("*.json")):
        for v in json.loads(path.read_text())["variants"]:
            out |= set(v["clinvar_vcv"])
    return sorted(out)


def fetch(vcvs: list[str]) -> dict:
    records = {}
    uids = [str(int(v[3:])) for v in vcvs]
    for i in range(0, len(uids), 150):
        time.sleep(0.4)          # at most 3 requests a second without a key
        body = urllib.parse.urlencode({"db": "clinvar", "retmode": "json",
                                       "id": ",".join(uids[i:i + 150])}).encode()
        req = urllib.request.Request(EUTILS, data=body, headers={"User-Agent": "structure-panel-builder"})
        with urllib.request.urlopen(req, timeout=180) as r:
            res = json.load(r)["result"]
        for uid in res.get("uids", []):
            x = res[uid]
            g = x.get("germline_classification") or {}
            records[x["accession"]] = {
                "title": x.get("title") or "",
                "kind": x.get("obj_type") or "",
                "genes": sorted({y["symbol"] for y in x.get("genes") or [] if y.get("symbol")}),
                "classification": g.get("description") or "",
                "review_status": g.get("review_status") or "",
                "last_evaluated": (g.get("last_evaluated") or "")[:10],
                "conditions": sorted({t.get("trait_name") or "" for t in g.get("trait_set") or []} - {""}),
            }
        print(f"  {min(i + 150, len(uids))} of {len(uids)}", file=sys.stderr)
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    vcvs = wanted()
    if args.check:
        have = json.loads(OUT.read_text())["records"] if OUT.exists() else {}
        missing = [v for v in vcvs if v not in have]
        print(f"{len(vcvs)} VCVs in the variant lists, {len(missing)} without a frozen record")
        return 1 if missing else 0
    records = fetch(vcvs)
    missing = [v for v in vcvs if v not in records]
    if missing:
        print(f"no record returned for {missing[:10]}", file=sys.stderr)
        return 1
    OUT.write_text(json.dumps({
        "what": "ClinVar variation records (VCV) behind data/panel/variants/*.json: title, "
                "record kind, gene symbols, aggregate germline classification, review status "
                "and conditions, as NCBI E-utilities esummary returned them.",
        "source": EUTILS + "?db=clinvar", "retrieved": datetime.date.today().isoformat(),
        "records": {k: records[k] for k in sorted(records)}}, indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}: {len(records)} records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
