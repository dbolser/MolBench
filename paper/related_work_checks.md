# Related work — what was verified, and how (2026-11-12)

Every entry in `references.bib` was checked against a primary source on 2026-11-12. This file
records the check, corrections to the 2026-11-06 audit list, and items left out because they
could not be verified.

## How each kind of entry was checked

| Kind | Source | Fields checked |
|---|---|---|
| Journal articles with a DOI | Crossref REST API, `https://api.crossref.org/works/<doi>` | title, all author names, journal, volume, issue, pages, date |
| arXiv preprints | arXiv API, `https://export.arxiv.org/api/query?id_list=…` | title, authors, date, comment / journal-ref, abstract |
| ACL Anthology paper | `https://aclanthology.org/2024.langmol-1.7.bib` | full BibTeX record |
| Software | GitHub API (`/repos/…`), npm registry, PyPI JSON | repository exists, description, licence, version date |
| Web page | fetched and read | title, author, date, quoted sentence |

Claims about the *content* of the four closest works were checked by reading the arXiv HTML
full text (first 100,000 characters of each):

| Work | Claim used in the paper | Verified in source |
|---|---|---|
| ScienceBoard, arXiv:2505.19897v3 | 169 tasks, six domains; biochemistry uses ChimeraX; state-based checks | yes (abstract; Sections 4.1, 4.2) |
| SciVisAgentBench, arXiv:2603.29139v4 | 108 cases; molecular suite on GROMACS + VMD; LLM judge on rubrics; 12 experts; alpha = 0.669; Pearson r 0.806–0.808 | yes |
| OSWorld-Science, arXiv:2609.39903v1 | 146 tasks; a "PyMOL/MNOVA" configuration; state and artefact checks with partial credit | yes |
| Speak to a Protein, arXiv:2510.17826v2 / JCIM | built on the Mol\* engine; question-answering evaluation; no accuracy reported for viewer operations | yes |
| ChimeraX chat page | "Claude will often make mistakes" | yes (page text) |
| molstar-mcp README | residue numbers from ClinVar etc. "are always author numbers" | yes (README line 125) |
| PDBrenum, PLOS ONE 2021 | 38.6% of 176,507 entries not numbered as UniProt | yes (article text) |
| Mol\* pull requests 1978 and 2052 | titles, merge dates; PR 1978 lists "Assistant (opt-in)" | yes (GitHub API) |

## Corrections to the audit list (`audit_related.md`)

- **PDBrenum.** The audit quoted "106,484 entries (63.6%)". The article states 38.6%
  (49,422 entries differ in numbering only, 18,700 in numbering and extra residues, of
  176,507). The paper uses 38.6%.
- **ScienceBoard biochemistry numbers.** The audit gave best model 41.4% and humans 69.0%. The
  camera-ready version (v3) reports different per-domain numbers (its Table 3 lists 62.07% for
  the best setting and 68.97% for humans). The paper cites no per-domain number.
- **ScienceBoard biochemistry task count** ("about 29") and **SciVisAgentBench molecular case
  count** ("13") are not stated in the text we read. Not used.
- **OSWorld-Science** reports "14 recorded software configurations" in one place and "17
  software in total" in another. The paper gives no count of applications.
- **Vollmar et al. 2026**: sixth author is Louise Jones.

## Listed in the audit, not cited (not verified, or not needed)

- pymol-copilot (repository verified to exist, BSD-3-Clause, created 2026-06-28; its evaluation
  numbers were not checked, and it has no paper).
- RCSB PDB MCP server news item; hidari123/molstar-llm; Arcadia agentic-pymol and sibling PyMOL
  tool servers; PROTEAN; ABLE; BioDesignBench; BioXArena; MolLangBench; the survey
  arXiv:2601.14943. None is needed for the argument; none was checked beyond what the audit
  recorded (MolLangBench and SciVisAgentSkills titles and authors were confirmed on arXiv).
- Berkeley Function Calling Leaderboard: no citable record found in Crossref in the time
  available. ToolLLM and tau-bench stand in for tool-use benchmarks.
- OSWorld and ToolLLM conference venues are not asserted; they are cited as arXiv preprints.

## Claims deliberately softened

- No "first" or "only". The paper says we *did not find* a published benchmark that grades
  plain-language control of a molecular viewer on resolved atoms across formats and through the
  UniProt-to-structure mapping.
- "Engine-neutral" is not claimed. MolViewSpec is rendered by Mol\* in practice, and the grader
  uses Mol\* 5.9.0 selection semantics. The paper says "graded at the level of the scene
  description".
- The human rating study is presented as a check on a side column, not as a contribution;
  SciVisAgentBench has a larger expert study.

## Re-check for the rewrite (2026-11-16)

- Every `references.bib` entry with a DOI was compared by script with the Crossref record
  saved at the first check (title, year, volume, pages): all 17 match. The eight arXiv
  identifiers are present in the saved arXiv API response. `jia2025voice` and
  `sun2024chatmol` have no saved Crossref record; their fields stand as checked on
  2026-11-12 (journal page and ACL Anthology).
- One reference was added: Jumper et al. 2021 (AlphaFold, Nature 596:583–589), from its
  Crossref record, because the AlphaFold DB licence asks for it.
- No other citation was added. Statements about other benchmarks (169, 108 and 146 tasks;
  alpha 0.669; r about 0.81; 38.6% of 176,507 entries) are unchanged from the verified draft.

## Review round 2 (2026-11-22)

- One reference was added: Pepys et al. 1993 (Nature 362:553–557, DOI 10.1038/362553a0), for
  the lysozyme variant p.Ile74Thr (I56T) in SI Section S3.2. Title, journal, year, volume,
  pages and authors were taken from its Crossref record on 2026-11-22. The statement that the
  paper reports two variants (Ile56Thr and Asp67His) was written from memory by the
  editing assistant and was not re-read at the source: check before submission.

## Review round 3 (2026-11-23)

- One reference was added: den Dunnen et al. 2016, "HGVS Recommendations for the Description
  of Sequence Variants: 2016 Update" (Human Mutation 37(6):564–569, DOI 10.1002/humu.22981),
  cited in Section 3.3.1 for the HGVS nomenclature. Title, journal, year, volume, issue, pages
  and the ten named authors were taken from its Crossref record on 2026-11-23. The paper cites
  it only for the existence of the nomenclature and its "p." prefix; no further claim about its
  content is made.

## Review round 5 (2026-11-23)

- One reference was added: Hart et al. 2024, "HGVS Nomenclature 2024: improvements to
  community engagement, usability, and computability" (Genome Medicine 16:149, DOI
  10.1186/s13073-024-01421-5), cited beside den Dunnen et al. 2016 in Section 3.3.1. Title,
  journal, year, volume, article number and the eight authors were taken from its Crossref
  record on 2026-11-23.
- Three statements of Section 3.3.1 about the HGVS nomenclature were read on 2026-11-23 at
  hgvs-nomenclature.org (pages "General recommendations" and "Reference sequences" of the
  stable version; the pages show no version number): a variant description without a
  versioned reference sequence is not valid, and accepted protein references are RefSeq NP_
  and Ensembl ENSP accessions; the three-letter amino-acid code is preferred; a predicted
  protein consequence is given in parentheses. The pages were read through an automated
  summary, not word for word: check before submission.
- Not read at the source this round: that "c." positions are counted from the A of the start
  codon ATG (Box 1 and Section 3.3.1). This is the rule of den Dunnen et al. 2016 as the
  clinical-genetics reviewer stated it; check before submission.
- The paper does not name the RefSeq protein accession of lysozyme (the reviewer proposed
  one); it says only what kind of accession a complete description needs.
