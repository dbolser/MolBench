## S7. System prompts

The two system prompts as sent in the main condition, and then the texts that fill their
slots. A name in double angle brackets, such as `<<MVS_REFERENCE>>`, marks a slot that is
filled with a longer frozen text. These longer texts are the *format guide* of each track:
for the scene track the MolViewSpec reference; for the call-list track the list of actions
with their fields, followed by the reference of the viewer's calls. With its slots filled,
the system prompt has {{prompt.mvs.words:,}} words on the scene track and
{{prompt.api.words:,}} on the call-list track. In the condition without a format guide, the
section "MVS reference" is removed. Each prompt has one worked example, on entry 1HSG, which
no task uses: the example of the call-list prompt is in the prompt itself, and that of the
scene prompt sits inside its format guide. The format guide of the scene track also has one
short illustration of a distance line on entry 1A6M, which tasks use; no task asks for that
distance.

The prompts and guides are printed as sent, each line indented by two spaces so that their own
headings are not read as headings of this document. They use the words of the repository and
not those of the paper; Table S0c lists the names that differ.

{{include:generated/si_prompts.md}}

A single-turn request is sent as the user message. A follow-up task is sent as the current
scene (scene track) or the calls made so far (call-list track), followed by `Request: …`.
