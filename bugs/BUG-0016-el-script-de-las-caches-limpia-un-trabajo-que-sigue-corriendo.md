---
id: BUG-0016
title: tools/build_example_caches.py limpia la carpeta de un trabajo sin comprobar que ha terminado — el trabajo pierde sus ficheros y falla
status: open
severity: low
component: tools
found_in: 0.2.4
fixed_in:
reported: 2026-11-17
reporter: David / Claude — reconstrucción de las cachés para drvarma 0.3.4
tags:
  - jobs
  - cache
  - tools
references:
  - tools/build_example_caches.py (build, sanitize)
  - bugs/BUG-0016-repro/repro.py
---

## Resumen

`build()` recoge las carpetas de los trabajos de rango cuando `rank_test(wait=6 h)`
vuelve, y `sanitize()` les borra toda subcarpeta (la `c/` donde escribe drvec
C), el pid y las horas. No comprueba que el trabajo haya acabado. El
16-nov-2026 el sistema de control de martin_manjon_treadway (R0T, R10, R3)
falló así:

```
FileNotFoundError: .../sima_jobs/d58cc15755040c25/c/drvecjob.boot
```

Su `job.json` ya llevaba la marca `"shipped"` del script. Rehecho solo, dio el
mismo resultado que antes. Queda sin explicar por qué `rank_test` volvió antes
de que el trabajo acabara.

## Impacto

Bajo: sólo afecta a quien reconstruye las cachés. Pero cuesta horas, y un
trabajo fallido se puede confundir con un resultado distinto.

## Reproducción

`bugs/BUG-0016-repro/repro.py`: un contraste de rango pequeño sobre el E1 de
Lütkepohl, lanzado con `wait=0` (vuelve mientras corre), y luego `sanitize()`
sobre su carpeta. Sale 1 mientras el trabajo acabe fallido.

## Arreglo propuesto

Antes de `sanitize`, esperar a que cada trabajo esté en un estado final y
exigir `done`; `sanitize` se niega con un trabajo vivo.
