## S5. The control set by kind

The control set has {{controls.n:,}} controls on the structures of the structure panel, each a reference
and one answer: {{controls.mvs.n_controls:,}} on the scene track ({{controls.mvs.n_identical}}
identical, {{controls.mvs.n_equivalent}} equivalent, {{controls.mvs.n_wrong}} wrong) and
{{controls.api.n_controls}} on the call-list track ({{controls.api.n_identical}} identical,
{{controls.api.n_equivalent}} equivalent, {{controls.api.n_wrong}} wrong). The verdict of each
control is known from how its answer was made.

Read-back from the viewers. Scene track: the read-back was run on the control set as it then
stood, {{controls.viewer.mvs.n_at_check:,}} scene controls. For
{{controls.viewer.mvs.checked}} of them both scenes were loaded in Mol\*
{{controls.viewer.molstar}} and their drawing read back; in all of them the viewer agreed with
the verdict. The other {{controls.viewer.mvs.skipped}} are of kinds that cannot be read back
(camera target, label text, colouring by chain, assembly, another entry).
{{controls.viewer.mvs.n_added_since}} scene controls were added afterwards and have not been
read back in the viewer. In the same run the grader's resolved state equalled the viewer's for all
{{controls.viewer.mvs.scenes}} scenes, and {{controls.viewer.mvs.probe_draws:,}} single
representations probed across the panel were drawn as the grader predicts. Call-list track:
a sample of the {{controls.api.n_controls}} controls was drawn by taking one control from each
kind in turn, and again, until the sample was full. Each control has two call lists, its
reference and its answer. Those that select by UniProt number were left out, and
{{controls.viewer.api.not_runnable}} could not be run by the test harness. The other
{{controls.viewer.api.lists}} call lists were replayed in PDBe Mol\*
{{controls.viewer.pdbe_molstar}}, and every one ended in the state that the grader computes.
The call-list controls use {{controls.api.n_entries}} structures: the
{{controls.api.n_entries_without}} entries that hold only DNA or RNA
({{controls.api.entries_without}}) have none, because each call-list control is built around a
protein residue.

**Table S5. Every kind of control.** *Controls*: number of controls of this kind. *Graded as
success*: controls that the grader counts as task success; this must equal *Controls* for
kinds that must pass and 0 for kinds that must fail. *Earlier grader*: the same count for the grader that
this work replaces on that track, with a score of exactly 1 read as success.

{{include:generated/si_controls.md}}
