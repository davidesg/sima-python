"""The MCP resources: the protocol, the two defect registers (sima's and the
engine's), the documents; and the packaged copy is the original."""
import asyncio
import filecmp
import os

from sima import mcp_server as M
from sima import resources as R

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_server_announces_them():
    uris = {str(r.uri) for r in asyncio.run(M.mcp.list_resources())}
    assert {"sima://protocol", "sima://defects", "sima://docs"} <= uris
    tmpl = {t.uriTemplate for t in asyncio.run(M.mcp.list_resource_templates())}
    assert {"sima://defects/{bug_id}", "sima://engine-defects/{bug_id}",
            "sima://doc/{name}"} <= tmpl


def test_the_index_has_both_registers():
    txt = R.defects_index()
    assert "## sima (the assistant)" in txt and "## drvarma (the engine" in txt
    assert "**BUG-0010**" in txt and "sima://engine-defects/BUG-XXXX" in txt


def test_one_engine_report_whole_and_a_missing_one_said():
    txt = asyncio.run(M.mcp.read_resource("sima://engine-defects/0010"))
    body = "".join(c.content for c in txt)
    assert "id: BUG-0010" in body and "## Resolution" in body
    assert "no BUG-9999" in R.defect("drvarma", "9999")


def test_protocol_and_docs():
    body = "".join(c.content for c in asyncio.run(M.mcp.read_resource("sima://protocol")))
    assert "THE AUTONOMOUS LANE" in body
    assert "`DESIGN`" in R.docs_index() and "PUBLISHING" not in R.docs_index()
    assert R.doc("DESIGN").startswith("#")
    assert "no such document" in R.doc("NOPE")


def test_the_packaged_copy_is_in_sync():
    for kind, skip in (("bugs", set()), ("docs", {"PUBLISHING.md"})):
        src = os.path.join(ROOT, kind)
        dst = os.path.join(ROOT, "src", "sima", "material", kind)
        if not os.path.isdir(dst):
            continue
        names = sorted(f for f in os.listdir(src) if f.endswith(".md") and f not in skip)
        assert sorted(os.listdir(dst)) == names, "run tools/sync_material.py"
        _m, bad, err = filecmp.cmpfiles(src, dst, names, shallow=False)
        assert not bad and not err, "run tools/sync_material.py"
