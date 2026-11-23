## 2. Related work

**Benchmarks.** The closest published benchmarks test agents that operate scientific
software on a desktop through screenshots and clicks. ScienceBoard [@sun2026scienceboard]
includes tasks in UCSF ChimeraX [@goddard2018chimerax] and checks the state of the
application afterwards; OSWorld-Science [@dai2026osworldscience; @xie2024osworld] includes
PyMOL in one of its software configurations. SciVisAgentBench [@ai2026scivisagentbench] scores
scientific visualizations, some of them molecular, with a language-model judge. General
benchmarks of tool use [@qin2023toolllm; @yao2024taubench] check that the right function is
called with the right arguments. We found no benchmark that grades the atoms a viewer would
draw against references computed from the structure, and none that tests the mapping of
residue numbers.

**Assistants.** Assistants that drive a molecular viewer exist for Mol\*
[@navarro2026speak; @molstarprism; @molstarmcp], PyMOL [@sun2024chatmol], ChimeraX
[@chimeraxmcp] and for speech interfaces [@jia2025voice; @cortes2026speech]. In their papers
and documentation we found no measurement of how accurately they drive the viewer. One community tool states that
the residue numbers which researchers take from ClinVar and the literature "are always
author numbers" [@molstarmcp]; that fails for many entries [@faezov2021pdbrenum], and it is
the error our clinical category is built to detect.

**Data and software.** MolViewSpec describes a molecular scene as a tree of typed nodes and
is implemented in Mol\* [@midlik2025mvs; @bittrich2024mvs; @sehnal2021molstar]; the call-list
track targets the PDBe build of Mol\* [@pdbemolstar; @ipymolstar]. Residue mentions in the
literature have been mapped to structures through SIFTS before [@vollmar2026residues], and
vision-language models read rendered molecules well below human level [@li2025misibench],
which is one reason our scores do not rest on a model that looks at pictures. SI Section S15
describes each of these works; where we say that a work lacks something, we mean that we did
not find it in the cited source.
