## S7. System prompts

The two system prompts as sent in the headline condition. A name in double angle brackets
marks a slot that is filled with a longer frozen text from the repository: the MolViewSpec
reference (`molbench/mvs_reference.md`), the list of call-list actions with their fields, and
the reference of the viewer's calls (`molbench/api_reference.md`). In the condition without a
format reference, the section "MVS reference" is removed. The worked example in the call-list
prompt uses entry 1HSG, which no task uses.

{{include:generated/si_prompts.md}}

A single-turn request is sent as the user message. A follow-up task is sent as the current
scene (scene track) or the calls made so far (call-list track), followed by `Request: …`.
