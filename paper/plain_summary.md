<!-- Built by paper/build.py from paper/plain/ and paper/generated/*.json (run numbers: October 2026 panel, PRELIMINARY). Do not edit: edit the sources. -->

# MolBench in plain words

*For volunteers who rate pictures. About 150 words.*

Scientists look at proteins in 3D viewers. More and more, they simply tell a computer program
what they want to see, for example "show the amino acid that is changed in this disease", and
a language model writes the viewer commands. The picture that comes back always looks neat,
even when it highlights the wrong amino acid.

MolBench is a test for these models. It holds 781 requests about
75 protein structures. For each request we know the right picture,
because a script works it out from public databases. A program then checks each model's answer
atom by atom.

We need people to check the program. You will see two pictures side by side: the right answer
and a model's answer, taken from the same viewpoint. You say whether they show the same thing,
a different thing, or that you cannot tell. You need no knowledge of biology. It takes about
ten seconds per pair, and nothing we publish will carry your name.
