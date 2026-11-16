## S7. System prompts

The two system prompts as sent in the main condition. A name in double angle brackets, such
as `<<MVS_REFERENCE>>`, marks a slot that is filled with a longer frozen text from the
repository: the MolViewSpec reference, the list of call-list actions with their fields, and
the reference of the viewer's calls. Everything else is printed as sent. In the condition
without a format reference, the section "MVS reference" is removed. The worked example in each
prompt uses entry 1HSG, which no task uses.

{{include:generated/si_prompts.md}}

A single-turn request is sent as the user message. A follow-up task is sent as the current
scene (scene track) or the calls made so far (call-list track), followed by `Request: …`.
