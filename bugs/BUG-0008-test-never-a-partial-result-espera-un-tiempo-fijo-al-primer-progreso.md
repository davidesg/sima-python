---
id: BUG-0008
title: test_never_a_partial_result espera 0.6 s fijos al primer progreso del job; en una máquina cargada falla
status: open
severity: low
component: tests
found_in: 0.2.0
fixed_in:
reported: 2026-10-30
reporter: David / Claude — prueba de instalación limpia de atsw 2.1.0 en diez distribuciones
tags:
  - jobs
  - tests
  - flaky
references:
  - tests/test_jobs.py::test_never_a_partial_result
  - src/sima/jobs.py submit (status "running" tras Popen), Ticks
---

## Summary

`submit()` marca el job como `"running"` en cuanto ha lanzado el proceso, antes
de que el hijo (`python -m sima.jobs run`) haya importado sima, numpy y drvec.
Hasta que el hijo escribe su primer `progress.json`, `status()["progress"]` es
`{}`. La prueba espera 0.6 s fijos tras ver `"running"` y exige ya las cuatro
claves del progreso. En la prueba de instalación limpia de atsw 2.1.0
(2026-10-30, tres contenedores a la vez en cuatro núcleos) falló así en Debian 12
y en Alpine: `assert set() == {'done', 'total', 'what', 'updated'}`.

## Impact

Bajo: es la prueba, no el código. Lo que el usuario ve en ese intervalo es un
job «running» sin recuentos todavía, que es cierto. Pero la prueba falla de
forma intermitente en CI cargados y en máquinas lentas.

## Reproduction

`bugs/BUG-0008-repro/repro.py` hace que el hijo arranque 1 s tarde (un
`sitecustomize` que duerme sólo en `python -m sima.jobs run`, como en una
máquina cargada) y corre la prueba. Sale con 1 mientras falle.

    PYTHONPATH=src python3 bugs/BUG-0008-repro/repro.py

## Root cause

Un tiempo fijo en la prueba, donde lo que hay que esperar es un estado: el
primer progreso escrito.

## Fix

Propuesto: que la prueba espere, con un plazo largo, a que `progress` tenga
recuentos (como `_wait_status` espera un estado), y sólo entonces compruebe que
son recuentos y que `done < total`. Los `steps` del job deben dar margen para
que no termine mientras tanto.

## Validation

El repro, y la prueba bajo carga.
