#!/usr/bin/env python3
"""
Tier-2 clinical/named-residue task generator (SIFTS + ClinVar).

Builds three grounded task families, all with references resolved through the
SIFTS UniProt<->author bridge and confirmed against the structure with gemmi:

  * sifts-named   "select canonical (UniProt) position N"   -> tests the numbering bridge
  * clinvar-variant "highlight the residue of the R175H pathogenic variant" -> 1 residue
  * clinvar-hotspots "highlight the mutational hotspot residues" -> top positions by
                    pathogenic-variant count (data-driven, knowledge-hard)

Design note: "highlight ALL residues with pathogenic ClinVar variants" is NOT a
good task — p53 has 204 such residues in 1TUP (a third of the domain), which no
model can enumerate and which isn't discriminating. We use specific variants and
a counted hotspot set instead.

    pip install -e ".[authoring]"
    python scripts/generate_clinical_tasks.py     # -> tasks/mvs_clinical/*.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

from molviewspec import ComponentExpression, create_builder

from molbench import grounding, sifts, variants
from molbench.mvs import categorize

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "tasks" / "mvs_clinical"
CIF = "https://files.rcsb.org/download/{}.cif"

# (pdb, uniprot, friendly name). Disease genes with ClinVar coverage + a structure.
TARGETS = [{"pdb": "1tup", "acc": "P04637", "name": "p53"}]

# Canonical UniProt positions to probe the bridge with (not necessarily clinical).
NAMED_POSITIONS = [143, 175, 248]


def _base(pdb):
    b = create_builder()
    s = b.download(url=CIF.format(pdb)).parse(format="mmcif").model_structure()
    s.component(selector="polymer").representation(type="cartoon").color(color="gray")
    return b, s


def _root(b):
    return json.loads(b.get_state().dumps())["root"]


def _residues_component(b, s, residues, rep, color):
    sel = [ComponentExpression(auth_asym_id=ch, auth_seq_id=n) for ch, n in residues]
    s.component(selector=sel).representation(type=rep).color(color=color)
    return _root(b)


def _write(tid, t, prompt, root, provenance, source):
    doc = {"id": tid, "category": "mvs", "source": source, "pdb": t["pdb"],
           "prompt": prompt, "reference_mvs": root,
           "categories": categorize(root), "provenance": provenance}
    (OUT / f"{tid}.json").write_text(json.dumps(doc, indent=2))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.json"):
        stale.unlink()
    written = 0

    for t in TARGETS:
        st = grounding.fetch_structure(t["pdb"])
        maps = sifts.mappings(t["pdb"])
        vs = variants.pathogenic_clinvar(t["acc"])

        # --- sifts-named: prove the bridge, residue picked by UniProt number ---
        for pos in NAMED_POSITIONS:
            auth = sifts.unp_to_auth(maps, t["acc"], pos)
            if not auth:
                continue
            ch, num = auth[0]
            name = grounding.residue_at(st, ch, num)
            b, s = _base(t["pdb"])
            root = _residues_component(b, s, [(ch, num)], "ball_and_stick", "blue")
            _write(f"named-{t['pdb']}-{pos}", t,
                   f"In {t['name']} (PDB {t['pdb'].upper()}), select the residue at "
                   f"canonical UniProt position {pos} and show it as blue ball-and-stick.",
                   root, {"unp_pos": pos, "auth": [ch, num], "residue": name}, "sifts-named")
            written += 1

        # --- clinvar-variant: one famous hotspot variant each, single residue ---
        counts = Counter(v.unp_pos for v in vs)
        top = [p for p, _ in counts.most_common()]
        by_pos = {v.unp_pos: v for v in vs}
        for pos in top[:5]:
            auth = sifts.unp_to_auth(maps, t["acc"], pos)
            if not auth:
                continue
            ch, num = auth[0]
            v = by_pos[pos]
            b, s = _base(t["pdb"])
            root = _residues_component(b, s, [(ch, num)], "ball_and_stick", "red")
            _write(f"clinvar-{t['pdb']}-{v.wild_type}{pos}", t,
                   f"In {t['name']} (PDB {t['pdb'].upper()}), highlight the residue affected "
                   f"by the pathogenic ClinVar variant {v.wild_type}{pos}{v.alt} as red "
                   f"ball-and-stick.",
                   root, {"variant": f"{v.wild_type}{pos}{v.alt}", "auth": [ch, num],
                          "significance": v.significance}, "clinvar-variant")
            written += 1

        # --- clinvar-hotspots: top positions by pathogenic-variant count ---
        hotspot_pos = [p for p, _ in counts.most_common(6)]
        residues, prov = [], []
        for pos in hotspot_pos:
            auth = sifts.unp_to_auth(maps, t["acc"], pos)
            if auth:
                residues.append(auth[0])
                prov.append({"unp_pos": pos, "n_variants": counts[pos], "auth": list(auth[0])})
        if residues:
            b, s = _base(t["pdb"])
            root = _residues_component(b, s, residues, "spacefill", "red")
            _write(f"hotspots-{t['pdb']}", t,
                   f"In {t['name']} (PDB {t['pdb'].upper()}), highlight the mutational hotspot "
                   f"residues — the positions carrying the most pathogenic ClinVar variants "
                   f"— as red spheres.",
                   root, {"hotspots": prov}, "clinvar-hotspots")
            written += 1

    print(f"wrote {written} clinical tasks to {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
