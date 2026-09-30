#!/usr/bin/env python3
"""Copy `bugs/`, `docs/` and the worked `examples/` to `src/sima/material/`, which
the wheel distributes.

The MCP resources (`sima://defects`, `sima://docs`) serve them at run time, and
a wheel only carries `src/`: without this copy an installation would answer
with nothing (art's BUG-0125). `bugs/` and `docs/` stay the only originals; the
copy is generated and ignored by git. Run it before building;
`tests/test_resources.py` fails if it is stale. Notes for the maintainer
(PUBLISHING.md) do not ship.
"""
from __future__ import annotations

import filecmp
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "src", "sima", "material")
DOCS_OUT = {"PUBLISHING.md"}


def _copy(src, dst, keep):
    os.makedirs(dst, exist_ok=True)
    names = sorted(f for f in os.listdir(src) if keep(f))
    copied = 0
    for f in names:
        o, d = os.path.join(src, f), os.path.join(dst, f)
        if not (os.path.exists(d) and filecmp.cmp(o, d, shallow=False)):
            shutil.copy2(o, d)
            copied += 1
    for f in os.listdir(dst):
        if f not in names:
            os.remove(os.path.join(dst, f))
    return len(names), copied


EXAMPLE_KEEP = (".pre", ".out", ".csv", ".md", ".json")


def example_files(src):
    """The files of the worked examples that travel with the package: the
    manifest, the tutorial, the univariate models and the data — not the
    walkthrough's outputs (out/, figs/) nor the guion it writes."""
    out = []
    for dp, dns, fns in os.walk(src):
        dns[:] = [d for d in dns if d not in ("out", "figs", "__pycache__")]
        for f in fns:
            if f.endswith(EXAMPLE_KEEP) and ".sima." not in f:
                out.append(os.path.relpath(os.path.join(dp, f), src))
    return sorted(out)


def _copy_tree(src, dst):
    rels = example_files(src) if os.path.isdir(src) else []
    copied = 0
    for r in rels:
        o, d = os.path.join(src, r), os.path.join(dst, r)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if not (os.path.exists(d) and filecmp.cmp(o, d, shallow=False)):
            shutil.copy2(o, d)
            copied += 1
    if os.path.isdir(dst):                                   # drop what is gone
        for dp, _dns, fns in os.walk(dst):
            for f in fns:
                if os.path.relpath(os.path.join(dp, f), dst) not in rels:
                    os.remove(os.path.join(dp, f))
    return len(rels), copied


def sync():
    return {"bugs": _copy(os.path.join(ROOT, "bugs"), os.path.join(DEST, "bugs"),
                          lambda f: f.endswith(".md")),
            "docs": _copy(os.path.join(ROOT, "docs"), os.path.join(DEST, "docs"),
                          lambda f: f.endswith(".md") and f not in DOCS_OUT),
            "examples": _copy_tree(os.path.join(ROOT, "examples"),
                                   os.path.join(DEST, "examples"))}


if __name__ == "__main__":
    for k, (n, c) in sync().items():
        print(f"{k}: {n} files, {c} copied")
