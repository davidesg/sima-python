"""What the model can ASK for (MCP resources), as art's `recursos`.

Tool descriptions are pushed with every call and clients cut them; resources
are asked for when needed, whole and addressable. sima serves:

* the protocol, to reread it in the middle of an analysis;
* two defect registers: sima's own, and the ENGINE's (drvarma), where the
  defects of the ladder live (the estimation, the MA wall, termcode 3...).
  They number independently, so each has its own address;
* the design documents.

The registers are read with `fue.bugs`, the suite's one parser. The material
comes from the installed package (tools/sync_material.py) or, in the working
tree, from the originals. When it is not there, say so: an absent register is
not a register with no defects (art BUG-0125).
"""
from __future__ import annotations

import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
MISSING = ("*(this installation carries no {what}. It lives in the repository: "
           "{where}.)*")


def _dir(kind):
    for d in (os.path.join(_HERE, "material", kind), os.path.join(_REPO, kind)):
        if os.path.isdir(d):
            return d
    return None


def _registers():
    from drvarma.register import bugs_dir
    return {"sima": (_dir("bugs"), "sima://defects", "github.com/davidesg/sima-python"),
            "drvarma": (bugs_dir(), "sima://engine-defects",
                        "github.com/davidesg/drvarma-python")}


def _bugs(d):
    from fue.bugs import list_bugs
    try:
        return list_bugs(d) if d else []
    except Exception:                                        # noqa: BLE001
        return []


def defects_index():
    out = ["# Defect registers", "",
           "Each report carries its MEASURED cause and why the fix is what it is. "
           "Read them before proposing a simplification that looks obvious: it may "
           "already be documented as a defect.", ""]
    for name, (d, uri, where) in _registers().items():
        title = ("sima (the assistant)" if name == "sima"
                 else "drvarma (the engine: the ladder, the estimation, the MA wall)")
        out += [f"## {title}", ""]
        if d is None:
            out += [MISSING.format(what=f"the {name} register", where=where), ""]
            continue
        bugs = _bugs(d)
        if not bugs:
            out += ["No reports.", ""]
            continue
        open_ = [b for b in bugs if b.status not in ("fixed", "wontfix", "duplicate")]
        out.append(f"{len(bugs)} reports, {len(open_)} not closed. "
                   f"Ask for one with `{uri}/BUG-XXXX`.")
        out.append("")
        for b in bugs:
            out.append(f"- **{b.id}** · {b.status} · {b.severity} — {b.title}")
        out.append("")
    return "\n".join(out)


def defect(register, bug_id):
    d, uri, where = _registers()[register]
    if d is None:
        return MISSING.format(what=f"the {register} register", where=where)
    bug_id = bug_id.strip().upper()
    if not bug_id.startswith("BUG-"):
        bug_id = f"BUG-{bug_id.zfill(4)}"
    for b in _bugs(d):
        if b.id.upper() == bug_id:
            with open(b.path, encoding="utf-8", errors="replace") as fh:
                return fh.read()
    return f"*(no {bug_id} in the {register} register; the index is `sima://defects`.)*"


def _docs():
    d = _dir("docs")
    if d is None:
        return d, []
    return d, sorted(f for f in os.listdir(d) if f.endswith(".md") and f != "PUBLISHING.md")


def docs_index():
    d, names = _docs()
    if not names:
        return MISSING.format(what="the design documents",
                              where="github.com/davidesg/sima-python")
    return "\n".join(["# sima's documents", "",
                      "Ask for one with `sima://doc/<NAME>`, without the extension.", ""]
                     + [f"- `{n[:-3]}`" for n in names])


def doc(name):
    d, names = _docs()
    name = name.strip()
    if not name.endswith(".md"):
        name += ".md"
    if name not in names:
        return "*(no such document; the index is `sima://docs`.)*"
    with open(os.path.join(d, name), encoding="utf-8", errors="replace") as fh:
        return fh.read()
