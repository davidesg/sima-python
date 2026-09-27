"""The guion: the record of an analysis, node by node.

art records every version of a model and the decision that produced it; that
record is what makes an analysis reviewable and repeatable, and what lets two
analysts (or two models) be compared. sima keeps the same idea, smaller: one
entry per protocol node, with the tool, its arguments, the evidence it produced
in one line, and the decision the analyst took.

The guion is saved as JSON next to the first file of the session
(``<first>.sima.json``) so that it travels with the data.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime

NODES = {
    "N0": "entry: the univariate models (fue files)",
    "N1": "the diagonal gate",
    "N2": "cross identification (residual CCFs)",
    "N3": "estimation of a candidate",
    "N4": "in-sample evidence (LR, residuals)",
    "N5": "the yardstick: out-of-sample against the univariates",
    "N6": "use: forecast, IRF, FEVD",
}


@dataclass
class Entry:
    n: int
    node: str
    tool: str
    args: dict
    evidence: str
    decision: str = ""
    when: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class Guion:
    name: str
    files: list
    entries: list = field(default_factory=list)

    def add(self, node, tool, args, evidence, decision=""):
        e = Entry(len(self.entries) + 1, node, tool, dict(args), evidence, decision)
        self.entries.append(e)
        return e

    def path(self):
        if not self.files:
            return f"{self.name}.sima.json"
        base = os.path.splitext(os.path.expanduser(self.files[0]))[0]
        return f"{base}.sima.json"

    def save(self, path=None):
        path = path or self.path()
        with open(path, "w") as fh:
            json.dump({"name": self.name, "files": self.files,
                       "entries": [asdict(e) for e in self.entries]}, fh, indent=2)
        return path

    def render(self):
        out = [f"GUION — {self.name}", f"files: {', '.join(self.files)}", ""]
        for e in self.entries:
            out.append(f"[{e.n}] {e.node} {NODES.get(e.node, '')} — {e.tool}"
                       f"({', '.join(f'{k}={v}' for k, v in e.args.items())})")
            out.append(f"    evidence: {e.evidence}")
            if e.decision:
                out.append(f"    decision: {e.decision}")
        return "\n".join(out)


def load(path):
    with open(path) as fh:
        d = json.load(fh)
    g = Guion(d["name"], d["files"])
    g.entries = [Entry(**e) for e in d["entries"]]
    return g
