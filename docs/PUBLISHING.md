# Publishing sima-tseries

By CI with trusted publishing (OIDC), as the rest of the suite
(`art-python/docs/PUBLISHING.md`).

| package | workflow | tag |
|---|---|---|
| sima-tseries | `.github/workflows/publish-sima.yml` | `sima-v*` |

**Order.** sima-tseries depends on drvarma ≥ 0.2.0 and fue ≥ 0.1.16:
`fue → drvarma → sima-tseries`. drvarma 0.2.0 has to be on PyPI before sima
0.1.0 is tagged, or the smoke test (which installs the wheel in a clean
environment) fails. That is the intended outcome: a blocked release is better
than a published package nobody can install.

**Validate without publishing.** `gh workflow run publish-sima.yml --ref <branch>`
builds, installs the wheel, imports it and lists the tools. The publish job
only runs on a `sima-v*` tag.

**Before tagging.**
1. `python -m pytest -q`.
2. `python3 tools/gen_tools_md.py sima.mcp_server sima docs/TOOLS.md`.
   Then `python3 tools/sync_material.py` (the CI runs it too): the packaged
   copy of `bugs/` and `docs/` that the MCP resources serve.
3. The CHANGELOG entry has its date.
4. PyPI: a trusted publisher for `davidesg/sima`, workflow `publish-sima.yml`,
   environment `pypi`.
