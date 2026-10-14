---
id: BUG-0004
title: En ruta V, evaluate mide contra univariantes ligeros que elige solo, sin decir cuáles son ni aceptar los del analista
status: fixed
severity: medium
component: server
found_in: 0.1.0
fixed_in: 0.1.0
reported: 2026-10-14
reporter: David / Claude — ejemplo lutkepohl_poskitt, ruta V (tutorial) frente a ruta U con los modelos de art
tags:
  - evaluate
  - ruta-v
  - vara-de-medir
references:
  - src/sima/mcp_server.py _yardstick_files (~l. 473): los `<SERIE>_u.pre` de raw.build_univariate
  - src/sima/mcp_server.py evaluate (~l. 1541, 1560)
---

## Summary

En ruta V la vara de N5 son los `<SERIE>_u.pre` que `raw.build_univariate`
construye la primera vez, «light; not reviewed in art». El constructor elige
dentro del empate de art: en el ejemplo, Buffalo (0,1,0), Minneapolis MA(1)
θ −0.25 y Kansas City MA(1) θ −0.20. Los modelos del analista en art son
(0,1,0), AR(1) y AR(1).

El cociente de N5 depende de esa elección:

| RMSE h = 1 (72 meses de estimación) | VAR(1) restringido | vara ligera | AR(1) de art |
|---|---|---|---|
| Minneapolis | 7.035 | 7.478 → **0.941** | 7.046 → ≈ 1.00 |
| Kansas City | 7.424 | 7.422 → 1.000 | 7.224 → 1.03 |

La única ganancia del tutorial (0.94 en Minneapolis) desaparece contra el
AR(1) de art. El informe no dice qué modelos son la vara (sólo la ruta del
fichero) y `evaluate` no tiene forma de recibir otros.

## Impact

Medio: N5 es el nodo que decide si el VARMA tiene razón de existir. Una vara
elegida en silencio dentro de un empate puede fabricar o borrar una ganancia
del orden de las que se están leyendo (5 %).

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0004-repro/repro.py` — con `flour_prices.csv`
del ejemplo: ruta V, el VAR(1) restringido de Lütkepohl y Poskitt, N5 con 72
meses y h = 6; sale con 1 mientras el bug siga abierto. La cifra de art
(7.046) sale de la sesión de ruta U con los `.pre` de art (BUG-0002-repro).

## Fix

1. El informe de N5 en ruta V nombra la vara, serie a serie: su ARIMA y el
   fichero, y si es la del constructor ligero, cuál tomó y entre cuáles del
   empate de art (`yardstick.json`, que escribe al construirla). Dice además
   que los cocientes dependen de esa elección y cómo dar otra.
2. `evaluate(yardstick=...)` acepta los univariantes del analista, un fichero
   de fue por serie: las mismas series y la misma transformación (λ, d, D) que
   las especificaciones, o se rechaza con el motivo. Queda en la sesión:
   `forecast_uncertainty` y `structure` la usan también. En ruta U la vara ya
   son los ficheros cargados.

El paso 9 del tutorial de `lutkepohl_poskitt` lo cuenta. Tests:
`tests/test_yardstick.py` (3).

## Validation

El repro sale con 0. Con los `.pre` de art como vara, la misma evaluación da
para Minneapolis a h = 1 RMSE 7.035 frente a 7.046 (cociente 0.999), lo que el
informe anotaba desde la ruta U; con la vara ligera, 7.035 frente a 7.478
(0.941), y el informe dice ahora que esa vara es el MA(1) que el constructor
tomó, el primero del empate.
