# Attribution — MolViewStories example scenes

The scene files in this directory (`story-*.json`) are **derived from** the example
stories in the **MolViewStories** project, fetched via
`scripts/ingest_molviewstories.py` from:

> <https://github.com/molstar/mol-view-stories>
> (`@mol-view-stories/webapp/public/examples/<story>/story.mvsj`, `main`)

Each file is one snapshot of a story, reduced to `{caption, scene_mvs, categories}`
for use as **Component-2 (VLM-judged)** reference material in MolBench. The scene
trees and captions are the upstream project's content.

## License

MolViewStories is distributed under the **MIT License**:

```
The MIT License
Copyright (c) 2025 - now, MolViewSpec contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in the
Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

Upstream license: <https://github.com/molstar/mol-view-stories/blob/main/LICENSE>

## Stories included

| Story | Snapshots | Kind |
|---|---|---|
| `simple` | 2 | generic visualization demo |
| `mvs-examples` | 7 | generic visualization demo |
| `tbp` | 10 | narrative "structural story" |
| `kinase` | 11 | narrative "structural story" |
| `alphafind` | 8 | tool/method demo |

## Note on topical overlap with PDB-101

Some narrative stories cover subjects also featured in RCSB **PDB-101 Molecule of
the Month** (e.g. the TATA-binding protein). The scenes redistributed here are
MolViewStories' own MIT-licensed authored content — we are **not** redistributing
PDB-101 Molecule-of-the-Month text or imagery. For that educational series (by
David S. Goodsell, RCSB PDB; CC-BY-4.0) see
<https://pdb101.rcsb.org/motm/motm-about>.
