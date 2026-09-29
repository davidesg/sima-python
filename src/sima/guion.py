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
    "N4b": "study of an ill-defined estimation",
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

    def html_path(self):
        return os.path.splitext(self.path())[0] + ".html"

    def figures_dir(self):
        """Where the figures go: next to the first file, so the HTML guion and
        its figures travel with the data (art does the same)."""
        base = os.path.dirname(os.path.abspath(self.path()))
        return os.path.join(base, "figs")

    def save_html(self, path=None):
        path = path or self.html_path()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render_html(self, os.path.dirname(os.path.abspath(path))))
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


# --------------------------------------------------------------------------- #
#  HTML — the same look as art's guion (art.guion.export_guion_html)           #
# --------------------------------------------------------------------------- #

_CSS = """
body { font-family: "Segoe UI", Arial, sans-serif; max-width: 1100px; margin: 40px auto;
       padding: 0 20px; background:#f7f7f7; color:#222; }
h1 { color:#1a237e; border-bottom:3px solid #1a237e; padding-bottom:8px; }
h2 { color:#283593; margin-top:32px; }
table { border-collapse:collapse; width:100%; margin:16px 0; background:#fff; }
th { background:#283593; color:#fff; padding:8px 12px; text-align:left; font-size:13px; }
td { padding:7px 12px; border-bottom:1px solid #e0e0e0; font-size:13px; vertical-align:top; }
tr:hover td { background:#e8eaf6; }
details { background:#fff; border:1px solid #c5cae9; border-radius:6px;
          margin:14px 0; padding:12px 18px; }
summary { font-size:16px; font-weight:bold; color:#283593; cursor:pointer; }
.step { border-top:1px solid #e0e0e0; padding:8px 0; }
.tool { font-family:monospace; background:#f0f4ff; border-left:4px solid #5c6bc0;
        padding:6px 12px; margin:6px 0; font-size:13px; }
.evidence { white-space:pre-wrap; font-size:13px; margin:6px 0; }
.decision { background:#fff9c4; border-left:4px solid #f9a825; padding:8px 14px; margin:6px 0; }
.alt { background:#fce4ec; border-left:4px solid #e91e63; padding:8px 14px; margin:6px 0; }
img { max-width:100%; border:1px solid #c5cae9; border-radius:4px; margin:10px 0; }
.meta { color:#555; font-size:12px; margin:2px 0; }
"""


def _esc(x):
    import html
    return html.escape(str(x))


def _args(a):
    return ", ".join(f"{k}={v}" for k, v in a.items() if k not in ("png", "decided_by", "alternatives"))


def render_html(g, base_dir=None):
    """The guion as a self-contained HTML page: the steps in a table, then
    one section per protocol node with each step's evidence, its decision
    (highlighted, with who decided and what was set aside, as art's) and the
    figures drawn at that step. Figures are linked by a path relative to the
    page when they sit under it (they travel together), absolute otherwise."""
    order = list(NODES)
    L = ["<!DOCTYPE html><html lang='en'><meta charset='utf-8'>",
         f"<title>sima guion — {_esc(g.name)}</title>",
         f"<style>{_CSS}</style>", "<body>",
         f"<h1>sima guion — {_esc(g.name)}</h1>",
         "<p class='meta'>Files: " + ", ".join(f"<code>{_esc(f)}</code>" for f in g.files) + "</p>"]
    if g.entries:
        L.append(f"<p class='meta'>From {_esc(g.entries[0].when)} to {_esc(g.entries[-1].when)}"
                 f" &nbsp;·&nbsp; {len(g.entries)} steps</p>")
    if not g.entries:
        L.append("<p><em>No steps recorded.</em></p></body></html>")
        return "\n".join(L)

    L += ["<h2>The path</h2>", "<table>",
          "<tr><th>#</th><th>Node</th><th>Tool</th><th>Arguments</th><th>Evidence</th>"
          "<th>Decision</th></tr>"]
    for e in g.entries:
        ev = e.evidence if len(e.evidence) <= 90 else e.evidence[:90] + "…"
        dec = e.decision if len(e.decision) <= 70 else e.decision[:70] + "…"
        L.append(f"<tr><td><a href='#s{e.n}'>{e.n}</a></td><td>{_esc(e.node)}</td>"
                 f"<td>{_esc(e.tool)}</td><td><code>{_esc(_args(e.args))}</code></td>"
                 f"<td>{_esc(ev)}</td><td>{_esc(dec)}</td></tr>")
    L.append("</table>")

    L.append("<h2>Node by node</h2>")
    nodes = order + sorted({e.node for e in g.entries} - set(order))
    last = g.entries[-1].node
    for nd in nodes:
        steps = [e for e in g.entries if e.node == nd]
        if not steps:
            continue
        L.append(f"<details{' open' if nd == last else ''}><summary>{_esc(nd)} — "
                 f"{_esc(NODES.get(nd, ''))} <span style='font-weight:normal;font-size:13px;"
                 f"color:#555'>({len(steps)} step{'s' if len(steps) > 1 else ''})</span></summary>")
        for e in steps:
            L += [f"<div class='step' id='s{e.n}'>",
                  f"<p class='meta'>step {e.n} &nbsp;·&nbsp; {_esc(e.when)}</p>",
                  f"<div class='tool'>{_esc(e.tool)}({_esc(_args(e.args))})</div>"]
            if e.evidence:
                L.append(f"<div class='evidence'>{_esc(e.evidence)}</div>")
            if e.decision:
                by = e.args.get("decided_by")
                L.append(f"<div class='decision'><b>Decision:</b> {_esc(e.decision)}"
                         + (f"<br><span class='meta'>decided by: {_esc(by)}</span>" if by else "")
                         + "</div>")
            if e.args.get("alternatives"):
                L.append(f"<div class='alt'><b>Set aside:</b> {_esc(e.args['alternatives'])}</div>")
            for p in e.args.get("png", []) or []:
                src = p
                if base_dir:
                    ap = os.path.abspath(p)
                    if ap.startswith(os.path.abspath(base_dir) + os.sep):
                        src = os.path.relpath(ap, base_dir)
                L.append(f"<img src='{_esc(src)}' alt='{_esc(e.tool)}'>")
            L.append("</div>")
        L.append("</details>")
    L.append("</body></html>")
    return "\n".join(L)
