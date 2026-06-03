"""
Visual similarity for the escalating grader (Tier 1).

When two MVS trees differ but might render to the same picture (e.g. selector
`all` vs `polymer` on a single-chain protein, or label vs author numbering that
resolve to the same residue), a cheap image diff can confirm rendering-equivalence
without paying for a VLM call. This is intentionally simple and fast — it only has
to recognise "these are essentially the same image"; the hard, semantic cases
escalate to the VLM judge (Tier 2).
"""

from __future__ import annotations

import pathlib


def image_similarity(a: str | pathlib.Path, b: str | pathlib.Path,
                     size: int = 128) -> float:
    """1.0 = identical, →0 = very different. Normalised RMSE over a downscaled RGB.

    Downscaling smooths away sub-pixel antialiasing / negligible camera jitter while
    preserving gross differences in colour, representation, and composition.
    """
    from PIL import Image
    ia = Image.open(a).convert("RGB").resize((size, size))
    ib = Image.open(b).convert("RGB").resize((size, size))
    pa, pb = list(ia.getdata()), list(ib.getdata())
    se = sum((x[0] - y[0]) ** 2 + (x[1] - y[1]) ** 2 + (x[2] - y[2]) ** 2
             for x, y in zip(pa, pb))
    rmse = (se / (len(pa) * 3)) ** 0.5
    return max(0.0, 1.0 - rmse / 255.0)
