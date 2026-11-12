# Where to submit

Checked 2026-11-12. Each fact below has a source and a note on how it was checked. Things I
could not check are marked **UNVERIFIED**. Plan of record (FINAL_PLAN decision 15): **preprint
first, then JCIM or Digital Discovery.**

## What the paper claims

Not "another tool-use benchmark". In order:

1. **Graded on what the viewer would show.** Selections are resolved to atoms in the real
   structure; author and label numbering are kept apart; invalid output is reported, not hidden.
2. **References built by script, in graded steps of difficulty**, up to clinical variants that
   need the UniProt-to-structure residue mapping (SIFTS).
3. **The same requests in two output formats** (MolViewSpec scene, PDBe Mol\* call list), so a
   content error can be told apart from a format error.
4. Honest null results: grounding packs gave no lift; without the format reference no scene
   was valid.

No "first" or "only" claim. `related_work_checks.md` records what was verified about each
neighbour. "Engine-neutral" is not claimed: both formats are rendered by Mol\*.

## Recommendation

1. **Preprint** as soon as the final run is in. The field moved from empty to busy in twelve
   months (see Related work), and a public repository is not citable. arXiv, bioRxiv and
   ChemRxiv are all compatible with JCIM (below). **UNVERIFIED** which server Dan prefers and
   which arXiv category would accept it.
2. **JCIM** as first choice for the archival paper: it published the closest systems paper
   (Speak to a Protein, J. Chem. Inf. Model. 2026, 66(19), 12391–12401), so the readership and
   the reviewers exist.
3. **Digital Discovery** as the alternative: open access by default and built around data and
   code review. It costs an article processing charge.

## JCIM — Journal of Chemical Information and Modeling (ACS)

Source: ACS author guidelines, <https://researcher-resources.acs.org/publish/author_guidelines?coden=jcisd8>
(fetched and read 2026-11-12). Rolling submission; no deadline.

| Item | Requirement |
|---|---|
| Fit | Scope includes "machine learning on chemical and biological data" |
| Manuscript type | **Article**: full-length research; no length limit stated. (Application Note: at most 4,000 words including abstract, main text and captions; the resource must be available to the community at publication and to reviewers during review. Letter: four journal pages, about 3,500 words.) |
| Title | "preferably 12 words or fewer" |
| Abstract | The guidelines ask for a short abstract ("3–4 sentences" in the format notes). Our abstract is longer and will need cutting. **Confirm against the template at submission.** |
| Sections | Standard research sections, clearly identified; figures and tables placed in the text |
| **Data availability** | **A Data Availability Statement is required at submission** (ACS Research Data Policy Level 2). Public sharing in a repository is encouraged. The page points to an editorial on data and software requirements in force since 1 January 2021 without summarising it — **read that editorial before submitting (UNVERIFIED content)** |
| Supporting Information | Separate file; described before the Acknowledgements |
| Preprints | Allowed (arXiv, bioRxiv, ChemRxiv named). Must be stated in the cover letter, with what changed since the preprint |
| Use of language models | Use for text or images "should be disclosed in the manuscript within the Acknowledgments section"; substantial use is described in Methods |
| Other | Conflict-of-interest statement for all authors; all funding sources; TOC graphic (see the ACS graphics guide) |
| Notes for us | The guidelines say new modelling approaches should be "benchmarked against multiple different tasks", and that papers "without a section on data curation" are less likely to succeed. We are a benchmark, not a method: say so in the cover letter, and keep the corpus-construction section (Section 3) prominent |
| Cost | **UNVERIFIED** (subscription journal with an open-access option; check the ACS price page) |

What the draft already has for JCIM: data and code availability section; data-curation
content (Section 3, provenance per task); CI-use disclosure placeholder; licences table.
Missing: DOI for the corpus and the run archives; TOC graphic; 12-word title check (current
title: 11 words); shorter abstract.

## Digital Discovery (RSC)

Sources. The RSC author-guideline pages returned HTTP 403 to automated fetching on 2026-11-12
(<https://www.rsc.org/publishing/publish-with-us/publish-a-journal-article/digital-discovery>,
<https://www.rsc.org/publishing/publish-with-us/publish-a-journal-article/data-sharing>). The
rows below come from search-engine extracts of those pages and are **to be confirmed by hand
in a browser**. The launch post was fetched directly:
<https://blogs.rsc.org/dd/2021/08/17/digital-discovery-open-for-submissions>. Rolling
submission; no deadline.

| Item | Requirement | Checked how |
|---|---|---|
| Fit | "research at the intersection of chemistry, materials science and biotechnology"; "putting data first to ensure reproducibility" | launch post, read directly |
| Model | Gold open access | launch post, read directly |
| Article types | Communications, Full papers, Commit (technical note), Reviews, Perspectives, Opinions, Comments, Tutorial Reviews. Ours is a **Full paper**. No length limit found | search extract — confirm |
| **Data availability** | A data availability statement is mandatory for all RSC articles | search extract — confirm |
| **Code** | Custom code must be deposited in a persistent repository (Zenodo, Code Ocean and similar are named) on acceptance; the statement must say how editors and reviewers reach code and data during review; repositories that issue DOIs are encouraged | search extract — confirm |
| Review | The journal uses data reviewers who check data handling and code reproducibility | search extract — confirm |
| Licence | CC BY or CC BY-NC | search extract — confirm |
| Cost | Article processing charge listed as **£2,100** plus tax; the launch-period waiver has ended (a 2026 institutional list marks the journal as charged). Institutional agreements may cover it | search extract — confirm the current figure |
| Preprints | **UNVERIFIED** (RSC journals generally accept preprinted work; check the page) |

What the draft already has for Digital Discovery: one-command reproduction of every number,
provenance file, licences. Missing: archive DOI (Zenodo) for code, corpus and raw outputs —
required on acceptance, better at submission.

## Workshops and conference tracks (for visibility; not the plan of record)

| Venue | Status on 2026-11-12 | Source |
|---|---|---|
| Language + Molecules (L+M) | **Only the 2024 edition exists** (ACL 2024, Bangkok, 15 August 2024). No 2025, 2026 or 2027 edition is listed. The earlier advice to send a short version there no longer has a target | <https://language-plus-molecules.github.io> (read directly) |
| ICLR 2027 workshops | Workshop proposals closed 9 October 2026. Accepted workshops announced **29 November 2026**. Suggested paper deadline **1 February 2027**; paper notifications by 26 February 2027. San Francisco. (The page gives the workshop days as "April 29 and 30, 2026", which looks like a typo for 2027.) Whether a suitable CI-for-science workshop is accepted will be known on 29 November | <https://iclr.cc/Conferences/2027/CallForWorkshops> (read directly) |
| NeurIPS Evaluations & Datasets track (formerly Datasets & Benchmarks) | 2026 deadlines have passed: abstract 4 May 2026, paper 6 May 2026, notification 24 September 2026. The 2027 call is **not announced**; early May 2027 is a guess. Requirements in 2026: data and code hosted and reachable by reviewers at submission; a Croissant metadata file with Responsible AI fields; executable code where the contribution is a benchmark; non-compliance can mean desk rejection | <https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets> (read directly) |
| ACL / EACL / NAACL 2027 workshops, ICML 2027 workshops, TMLR, Bioinformatics, GigaScience | **UNVERIFIED** this round. The 2026-11-06 audit lists dates for some; I did not re-check them | — |

## What a submission still needs (any venue)

| Need | State on 2026-11-12 |
|---|---|
| Final corpus, both tracks, ≥ 50 structures, clinical tier with numbering offsets | in progress (FINAL_PLAN phases A–B) |
| Final run: 3 samples per task, archived, one manifest | waiting for the corpus and Dan's go |
| Every number scripted | **done** for the October data; the same script takes the final archives |
| Human rating study readout | pending |
| Archive DOI for corpus, code and raw outputs | not started; the October archives are on one machine only |
| Authors, affiliations, funding, competing interests, ethics wording | ⟦PENDING: Dan⟧ |
| Licence statements confirmed against the providers' terms pages | pending (listed in the paper's Section 9) |
