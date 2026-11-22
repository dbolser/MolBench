## 2. Related work

Existing benchmarks that involve molecular viewers test agents that operate a desktop through
screenshots (ScienceBoard [@sun2026scienceboard], OSWorld-Science [@dai2026osworldscience]), or
score pictures with a judge model (SciVisAgentBench [@ai2026scivisagentbench]). We found none that grades the atoms a viewer would draw against references
computed from the structure, and none that tests the mapping of residue numbers. Assistants
for molecular viewers exist, but their papers report no accuracy for driving the viewer.

### 2.1 Benchmarks that score the operation of scientific software

**ScienceBoard** [@sun2026scienceboard] is the closest published benchmark. It has 169 tasks in
six domains, performed by agents that operate a desktop through screenshots and clicks. Its
biochemistry domain uses UCSF ChimeraX [@goddard2018chimerax], and a task is checked by reading
the state of the application after the agent has finished. MolBench shares the idea of checking
the resulting state. It differs in four ways. It tests the step from request to commands
directly, with no desktop in between. Its references are computed by script and record their
origin. Its categories of task are defined by what the model must know, up to clinical variants. And it
poses requests in two answer formats.

**SciVisAgentBench** [@ai2026scivisagentbench] has 108 expert-written cases of scientific
visualization; its molecular cases use GROMACS and VMD. Outcomes are scored by a language-model
judge against written rubrics, with deterministic checks for some suites. The authors compared
the judge with 12 visualization experts and report an agreement among raters (Krippendorff's
alpha) of 0.669 and a correlation between judge and human scores of about 0.81. MolBench is
narrower and stricter: it covers only molecular viewers, and its scores need no judge model.

**OSWorld-Science** [@dai2026osworldscience] follows the OSWorld desktop benchmark
[@xie2024osworld] with 146 tasks over scientific applications, one of which combines PyMOL with a
nuclear magnetic resonance package. Evaluators inspect application state and output files and
give partial credit. The overlap with MolBench is small: a molecular viewer is one application
among many, and the tasks test the operation of a graphical interface.

General benchmarks of tool use, such as ToolLLM [@qin2023toolllm] and tau-bench
[@yao2024taubench], measure whether a model calls the right function with the right arguments.
Our call-list track has that shape. The difference is the check: a viewer call is right only
if its selection resolves to the right atoms in a particular structure.

### 2.2 Assistants for molecular viewers

**Speak to a Protein** [@navarro2026speak] is an assistant that answers questions about a
protein while driving a browser viewer built on the Mol\* engine [@sehnal2021molstar]. Its
evaluation covers question answering; the paper lists viewer operations as a task group and
reports no accuracy for them. **ChatMol Copilot** [@sun2024chatmol] is an agent for molecular
modelling that can also operate PyMOL. **ChimeraX** can be operated from a chat assistant
through a built-in tool server; its documentation notes that the assistant "will often make
mistakes" [@chimeraxmcp]. **VOICE** [@jia2025voice] and a speech interface for an immersive
molecular-graphics application [@cortes2026speech] operate molecular scenes by spoken language
and were evaluated with users, not with scored tasks. The Mol\* project has merged an optional
assistant and a command layer into its next viewer [@molstarprism]; we found no published
benchmark from that work. A community tool that builds MolViewSpec scenes from chat
[@molstarmcp] states in its documentation that the residue numbers researchers take from
ClinVar, publications and mutation databases "are always author numbers". That holds for some
entries and fails for many [@faezov2021pdbrenum]. It is the error our clinical category is built to
detect.

### 2.3 The data and software MolBench stands on

MolViewSpec describes a molecular scene as a tree of typed nodes and is implemented as an
extension of the Mol\* viewer [@midlik2025mvs; @bittrich2024mvs; @sehnal2021molstar]. The
call-list track targets the PDBe build of Mol\* [@pdbemolstar], which a notebook widget exposes
to Python [@ipymolstar]. Structures come from the Protein Data Bank [@wwpdb2019] and, for
{{panel.n_alphafold}} predicted structures, from the AlphaFold Protein Structure Database [@varadi2024afdb;
@jumper2021alphafold]. The mapping between UniProt residues and the residues of a structure
comes from SIFTS [@dana2019sifts], as distributed by PDBe [@pdbekb2020; @pdbekb2022]. Variants
and their clinical classification come from ClinVar [@landrum2018clinvar], found through UniProt
[@uniprot2025]. Structure files are read with GEMMI [@wojdyr2022gemmi].

The numbering problem at the centre of the clinical category has been met from another side.
Vollmar and colleagues find residue mentions in the crystallographic literature and map them to
structures through SIFTS [@vollmar2026residues]. Their system reads papers; ours asks whether a
language model can do the same mapping when it writes a scene. MiSI-Bench [@li2025misibench] asks
vision-language models questions about rendered images of molecules and finds them well below
human level, which is one reason our scores do not rest on a model that looks at pictures.

Statements in this section about what other work contains were checked against the cited
sources, and the notes of each check are in the repository. Where we say that a benchmark
lacks something, we mean that we did not find it in its paper.
