**Is the requested component itself right? `spec` condition (PRELIMINARY).** Valid scenes only. The *target* of a task is every component of the reference scene except, when the reference has more than one, the component with the most atoms, which is treated as *context* (for example a grey cartoon of the whole protein behind one highlighted residue). *Target exact*: the output draws every target with exactly the reference atoms, representation and colour. *Scene exact*: the whole scene scores 1. *Target exact, scene not*: the target is right and the scene still loses points for something else (missing or different context, extra components). *Atoms only*: the target atoms are selected exactly, in the reference entry or an accepted one, but drawn or coloured differently. *Target wrong*: no component selects exactly the target atoms.

| Regime | Valid scenes | Target exact | Share | Scene exact | Target exact, scene not | Atoms only | Target wrong |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Translation | 491 | 404 | 82.3% | 402 | 2 | 55 | 32 |
| Grounded | 91 | 64 | 70.3% | 64 | 0 | 2 | 25 |
| Clinical | 96 | 85 | 88.5% | 2 | 83 | 2 | 9 |
| Resolution | 52 | 2 | 3.9% | 2 | 0 | 33 | 17 |
| Interactions | 54 | 22 | 40.7% | 20 | 2 | 15 | 17 |
