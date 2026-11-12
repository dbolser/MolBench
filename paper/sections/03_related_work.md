## 2. Related work

We checked every work below against its source on 2026-11-12. Where we say a benchmark lacks
something, we mean that we did not find it in the paper; we do not claim to be first or only.

### 2.1 Benchmarks that score control of scientific software

**ScienceBoard** [@sun2026scienceboard] is the closest published benchmark. It has 169 tasks in
six domains, performed by agents that operate a desktop through screenshots and clicks. Its
biochemistry domain uses UCSF ChimeraX [@goddard2018chimerax], and tasks are checked by reading
the state of the application after the agent has finished. MolBench shares the idea of checking
the resulting state. It differs in four ways. It tests the translation from request to commands
directly, without a desktop in between. Its references are built by script and carry their
provenance. It has graded regimes of difficulty, up to clinical variants. And it poses each
request in two output formats.

**SciVisAgentBench** [@ai2026scivisagentbench] has 108 expert-written cases of scientific
visualization. Its molecular cases use GROMACS and VMD. Outcomes are scored by a language-model
judge against written rubrics, together with deterministic checks for some suites. The authors
validated the judge against 12 visualization experts and report an inter-rater agreement
(Krippendorff's alpha) of 0.669 and a correlation between judge and human scores of about 0.81.
MolBench is narrower and stricter. It covers only molecular viewers, its main score needs no
judge model, and its human rating study (Section 4.5) is smaller and serves only to check a side
column.

**OSWorld-Science** [@dai2026osworldscience] follows the OSWorld desktop benchmark
[@xie2024osworld] with 146 tasks over scientific applications, one of which pairs PyMOL with an
NMR package. Evaluators inspect application state and output files and give partial credit. The
overlap with MolBench is small: a molecular viewer is one application among many, and the tasks
test the operation of a graphical interface.

General benchmarks of tool use, such as ToolLLM [@qin2023toolllm] and tau-bench
[@yao2024taubench], measure whether a model calls the right function with the right arguments.
MolBench's call-list track has that shape. The difference is the check. A viewer call is right
only if its selection resolves to the right atoms in a particular structure, and the benchmark
checks that.

### 2.2 Assistants for molecular viewers, without a control benchmark

**Speak to a Protein** [@navarro2026speak] is a co-scientist that answers questions about a
protein while driving a browser viewer built on the Mol\* engine. Its evaluation covers question
answering. The paper lists viewer operations as one of its task groups but reports no accuracy
for them. **ChatMol Copilot** [@sun2024chatmol] is an agent for molecular modelling that includes
PyMOL control. **ChimeraX** can be operated from a chat assistant through a built-in tool server;
its documentation notes that the assistant "will often make mistakes" [@chimeraxmcp]. **VOICE**
[@jia2025voice] and a speech interface for an immersive molecular-graphics application
[@cortes2026speech] control molecular scenes by spoken language and were evaluated with users,
not with scored tasks. The Mol\* project has merged an optional assistant and a command-language
layer into its next viewer [@molstarprism]. We found no published benchmark from that work.
A community tool that builds MolViewSpec scenes from chat [@molstarmcp] instructs its model that
residue numbers from variant databases "are always author numbers". That holds for some entries
and fails for many [@faezov2021pdbrenum]. It is the error our clinical tier is built to catch.

### 2.3 The data and software MolBench stands on

MolViewSpec describes a molecular scene as a tree of typed nodes and is implemented as an
extension of the Mol\* viewer [@midlik2025mvs; @bittrich2024mvs; @sehnal2021molstar]. The
call-list track targets the PDBe build of Mol\* [@pdbemolstar] through its notebook widget
[@ipymolstar]. Structures come from the Protein Data Bank [@wwpdb2019] and, where a task uses a
predicted model, the AlphaFold Protein Structure Database [@varadi2024afdb]. The mapping between UniProt
residues and the residues of a structure comes from SIFTS [@dana2019sifts], as distributed with
PDBe-KB [@pdbekb2020; @pdbekb2022]. Variants and their clinical significance come from ClinVar
[@landrum2018clinvar] through UniProt [@uniprot2025]. Structure files are read with GEMMI
[@wojdyr2022gemmi].

The numbering problem at the centre of the clinical tier has been met from another side. Vollmar
and colleagues find residue mentions in the crystallographic literature and map them to
structures through SIFTS [@vollmar2026residues]. Their system reads papers; ours asks whether a
model can do the same mapping when it draws a scene.

### 2.4 Nearby work that does not overlap

MiSI-Bench [@li2025misibench] asks vision-language models questions about rendered images of
molecules and finds them well below human level. That is evidence for caution in using such a
model as an image judge, which is how we treat ours (Section 4.4).
