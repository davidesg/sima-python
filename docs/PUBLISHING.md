# Publishing sima-tseries

By CI with trusted publishing (OIDC), as the rest of the suite
(`art-python/docs/PUBLISHING.md`).

| package | workflow | tag |
|---|---|---|
| sima-tseries | `.github/workflows/publish-sima.yml` | `sima-v*` |

**Order.** sima-tseries 0.2.0 depends on fue ≥ 0.1.18, drvarma ≥ 0.3.0 and
drvec ≥ 0.1.0 (drvec-python, its own `publish.yml`, tag `v*`):
`fue → drvarma → drvec → sima-tseries`, the suite's order in
`art-python/docs/PUBLISHING.md`. All three have to be on PyPI before sima
0.2.0 is tagged, or the smoke test (which installs the wheel in a clean
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
4. The worked examples' job caches match the drvec C that drvec-python
   bundles: their key holds the engine and the tier, so a new C (or a new
   csrc/) asks for `python3 tools/build_example_caches.py` (move the old
   `sima_jobs/` aside first, or the run finds them by their key), and
   `SIMA_SLOW=1 python -m pytest tests/test_example_caches.py` on Linux x86_64.
5. PyPI: a trusted publisher for the repository `davidesg/sima-python`,
   workflow `publish-sima.yml`, environment `pypi` (registered: 0.1.1 went out
   by it).
