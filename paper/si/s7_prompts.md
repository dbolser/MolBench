## S7. System prompts

The two system prompts as sent in the main condition. A name in double angle brackets, such
as `<<MVS_REFERENCE>>`, marks a slot that is filled with a longer frozen text from the
repository: the MolViewSpec reference, the list of call-list actions with their fields, and
the reference of the viewer's calls. These longer texts are the *format guide* of each track.
Everything else is printed as sent. In the condition without a format guide, the section "MVS
reference" is removed. Each prompt has one worked example, on entry 1HSG, which no task uses:
the example of the call-list prompt is printed below, and that of the scene prompt sits inside
its format guide. The format guide of the scene track also has one short illustration of a
distance line on entry 1A6M, which tasks use; no task asks for that distance.

{{include:generated/si_prompts.md}}

A single-turn request is sent as the user message. A follow-up task is sent as the current
scene (scene track) or the calls made so far (call-list track), followed by `Request: …`.
