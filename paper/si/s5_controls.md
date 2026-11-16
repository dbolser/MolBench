## S5. The control set by kind

The control set has {{controls.n:,}} pairs of a reference and an answer on the structures of the
panel: {{controls.mvs.n_controls:,}} on the scene track ({{controls.mvs.n_identical}}
identical, {{controls.mvs.n_equivalent}} equivalent, {{controls.mvs.n_wrong}} wrong) and
{{controls.api.n_controls}} on the call-list track ({{controls.api.n_identical}} identical,
{{controls.api.n_equivalent}} equivalent, {{controls.api.n_wrong}} wrong). The verdict of each
pair is known from how it was made.

Read-back from the viewers. Scene track: {{controls.viewer.mvs.checked}} pairs were loaded in
Mol\* {{controls.viewer.molstar}} and the drawing of both scenes read back; in all of them the
viewer agreed with the verdict. {{controls.viewer.mvs.skipped}} pairs are of kinds that cannot
be read back (camera target, label text, colouring by chain, assembly, another entry). In the
same run the grader's resolved state equalled the viewer's for all
{{controls.viewer.mvs.scenes}} scenes, and {{controls.viewer.mvs.probe_draws:,}} single
representations probed across the panel were drawn as the grader predicts. Call-list track:
{{controls.viewer.api.lists}} call lists were replayed in PDBe Mol\*
{{controls.viewer.pdbe_molstar}}, all with the end state that the grader computes.

**Table S5. Every kind of control pair.** *Pairs*: number of pairs of this kind. *Graded as
success*: pairs that the grader counts as task success; this must equal *Pairs* for kinds that
must pass and 0 for kinds that must fail. *Earlier grader*: the same count for the grader that
this work replaces on that track, with a score of exactly 1 read as success.

{{include:generated/si_controls.md}}
