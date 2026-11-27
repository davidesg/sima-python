---
id: BUG-0020
title: When drvarma computes on its pure-Python port no tool says so — the warning goes to the server's stderr, and the provenance records neither the Python version nor why the engine did not load
status: fixed
severity: high
component: server
found_in: 0.2.4
fixed_in: unreleased (after 0.2.4)
reported: 2026-11-27
reporter: David / Claude — the P08 run of the course (UCM), US monetary VAR 1990-2007
tags:
  - engine
  - provenance
  - warnings
references:
  - src/sima/provenance.py base(), drvarma_backend()
  - src/sima/mcp_server.py load_pre, run_gate
  - drvarma bugs/BUG-0031 (why the port is installed), BUG-0005 (the warning); drvarma TODO.md, the speed study (what the port costs)
  - bugs/BUG-0020-repro/repro.py
---

## Summary

drvarma's fallback warning (BUG-0005) is a `RuntimeWarning` printed once to
stderr, and an MCP server's stderr reaches neither the model nor the analyst.
sima writes "drvarma engine python" into the provenance of every script
entry, where nobody looks while working. `load_pre` and `run_gate` say
nothing. The provenance does not record the interpreter (`sys.version`, and
whether it is free-threaded or 32-bit), nor `drvarma.engine_load_error()`,
which are the two things that would tell why.

## Impact

In the P08, five groups worked on the port: macOS arm64 and Windows AMD64, sima
0.2.1-0.2.4. Each estimate of the four-series system took 10-20 minutes and
`structure` passed 25. None knew why. Their assistants concluded that sima
"does not answer" and two of them replaced it:
- one with a statsmodels VAR, and the warning that said so was later removed
  from the conclusions;
- one with OLS in its own script.

Others limited iterations and relaxed tolerances, or renounced the full VAR
"for computational cost". Since the Python version is not recorded, the
cause (drvarma BUG-0031: no wheel for 3.15) cannot be confirmed from the
scripts.

## Reproduction

`python3 bugs/BUG-0020-repro/repro.py` blocks the extension, loads a pair and
looks for the engine in `load_pre`'s output and the interpreter in the
provenance:

```
provenance: {'sima': '0.2.4', 'drvarma': '0.3.4', 'fue': '0.1.22', 'drvec': '0.1.2',
             'backend': 'drvarma engine python, eigensolver scipy', 'platform': 'linux x86_64', 'tier': 'exact'}
load_pre about the engine: NOTHING
OPEN
```

## Root cause

The fallback was made visible in drvarma (BUG-0005) for a terminal user. sima
inherited a warning channel that MCP does not carry, and the provenance was
designed for the platform tier, not for the interpreter.

## Fix

- `load_pre`, when `engine_backend() == "python"`, opens with a block such as
  «! drvarma runs on its pure-Python port (reason: <engine_load_error>; Python
  <version>). A VAR(1) of four series can take more than an hour. Reinstall
  with a Python that has binary wheels (3.10-3.14): uv tool install --python
  3.13 atsw==…». Repeat it in every `estimate` while it lasts.
- The provenance gains `python` (`sys.version`, plus `sys._is_gil_enabled()`
  and the bitness) and `engine_load_error`.
- The same block for fue's engine, which art already prints as «motor Python»
  in its scripts.

## Validation

The repro passes: the warning is in `load_pre` and the interpreter in the
provenance.

## Resolution (2026-11-27)

- `provenance.engine_notice()`: when drvarma or fue computes on its port, a
  block «! ENGINE: … compute on the pure-Python port …» with the interpreter,
  the import error, the cost, and the reinstall line. `load_pre`, `estimate`
  and `structure` open with it while it lasts. Asked for with
  `*_NO_ENGINE`, it says so and does not alarm.
- The provenance gains `python` (implementation, version, bitness,
  free-threaded) and `drvarma_load_error` / `fue_load_error` when an engine
  did not load; the PROVENANCE line prints the Python.
- The cause on the drvarma side is fixed in drvarma BUG-0031 (one abi3 wheel
  for every CPython >= 3.10). `tests/test_bug0020_motor_python.py`.

