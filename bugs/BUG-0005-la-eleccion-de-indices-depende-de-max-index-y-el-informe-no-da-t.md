---
id: BUG-0005
title: identify_echelon cambia de elección con max_index (la muestra común encoge) sin decir sobre cuántas observaciones calcula la tabla; el MANUAL lo atribuye a la ruta U
status: fixed
severity: medium
component: evidence
found_in: 0.1.0
fixed_in: 0.1.0
reported: 2026-10-14
reporter: David / Claude — ejemplo lutkepohl_poskitt, comparación con el aparte de flour_prices
tags:
  - identify_echelon
  - forma-echelon
  - docs
references:
  - drvarma src/drvarma/echelon.py search (~l. 387): t0 = h + n_max + grado de los factores
  - src/sima/mcp_server.py identify_echelon (~l. 938)
  - docs/MANUAL-echelon.md §5.1; examples/lutkepohl_poskitt/TUTORIAL.md, «An aside: route U on the same data»
---

## Summary

La búsqueda de Lütkepohl y Poskitt compara todos los candidatos sobre una
muestra común que empieza en t0 = h + n_max. Al subir `max_index` la muestra
encoge (precios de la harina, h = 1: T 95 con n_max 3, T 92 con n_max 6) y la
tabla entera cambia: log|S| de (0, 0, 0) pasa de 5.3605 a 5.4205 y la
elección de SC y HQ pasa de **(1, 0, 0)** a **(0, 0, 0)**.

El informe no dice T ni la muestra, así que dos llamadas que sólo difieren en
`max_index` dan dos respuestas sin explicación. La sospecha inicial, que la
búsqueda de ruta U dependía del ARMA de los univariantes, era falsa: con las
MA(1) de `flour_prices` y con los modelos de art (paseo aleatorio, AR(1),
AR(1)) las tablas son idénticas para el mismo `max_index`.

La documentación ya cayó en la confusión. MANUAL-echelon §5.1 dice que en
ruta U «the search on the differences chooses (1, 0, 0), with both
criteria», y el aparte del tutorial de lutkepohl_poskitt lo presenta como lo
que cambia la ruta U. Es el `max_index` (3 por defecto frente a 6 en el
tutorial, el de Lütkepohl y Poskitt).

## Impact

Medio: el nodo N2 decide los índices, y en datos cortos el límite de la
búsqueda, que parece un mero tope, cambia la respuesta. El analista no tiene
cómo verlo, y el MANUAL le da una explicación equivocada.

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0005-repro/repro.py` — los dos juegos de
univariantes (MA(1) de flour_prices y los de art), max_index 3 y 6; sale con
1 mientras la elección cambie sin que el informe diga la T de la tabla.

## Root cause

drvarma `echelon.search`: `t0 = h + n_max + _lag_of(filters)`. Es el diseño
(una muestra común para que los criterios sean comparables), pero ni drvarma
ni sima lo exponen.

## Fix

1. El encabezado de la tabla dice la muestra: «T = 92 (1972.10 – 1980.11):
   long VAR(h) + n_max»; y una línea cuando la elección con un `max_index`
   menor sería otra, o al menos la advertencia de que la muestra depende de
   `max_index`.
2. MANUAL-echelon §5.1 y el aparte del tutorial: la diferencia (1, 0, 0) /
   (0, 0, 0) es de `max_index` (T 95 frente a 92), no de la ruta. Con
   n_max 6 los dos juegos de univariantes dan (0, 0, 0).

## Validation

Arreglado en sima (`identify_echelon`), sin tocar drvarma: tras la tabla,
«The table is computed on T = 92 of the 99 observations of the stationary
vector: every candidate on the same sample, which starts after the long VAR's
1 lag plus max_index = 6. A different max_index changes that sample, and on a
short series it can change the choice.» El repro sale con 0; test
`tests/test_echelon.py::test_identify_echelon_says_its_sample`. El punto 2
(MANUAL §5.1 y el aparte del tutorial) se corrigió en el PR #5.
