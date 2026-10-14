---
id: BUG-0002
title: El LR de estimate dice «against the diagonal system (the univariates)» y es contra el mismo modelo sin términos cruzados
status: fixed
severity: low
component: evidence
found_in: 0.1.0
fixed_in: 0.1.0
reported: 2026-10-14
reporter: David / Claude — ejemplo lutkepohl_poskitt en ruta U con los modelos de art, forma echelon
tags:
  - estimate
  - evidence
  - forma-echelon
references:
  - src/sima/evidence.py estimation_text (~l. 651): «against the diagonal system (the univariates)»
  - src/sima/mcp_server.py estimate (~l. 1135 y 1142): «against the same model without cross terms»
---

## Summary

El informe de `estimate` describe el mismo LR de dos maneras que no casan. La
cabecera (mcp_server) dice «The LR below is against the same model without
cross terms; the univariates come at N5», y la línea del LR (evidence) dice
«against the diagonal system (the univariates)».

Lo que se calcula es lo primero (`L.lr_test()`, el mismo modelo sin cruces).
En ruta U con la forma echelon no coincide con los univariantes: con índices
(0, 0, 0) el LR = 437.511 tiene 3 g.l. —sólo las covarianzas de las
innovaciones—, pero los univariantes de Minneapolis y Kansas City llevan un
AR(1) que la forma echelon ha sustituido. En ruta V tampoco hay univariantes
en el modelo restringido, y la cabecera lo dice expresamente.

## Impact

Bajo: el número es correcto. Pero el analista lee que el sistema bate a sus
univariantes por 437 puntos de LR cuando la comparación con los univariantes
es la de N5, y aquí ni siquiera tienen la misma dinámica propia.

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0002-repro/repro.py` — con los `.pre` de art
del ejemplo (Buffalo (0,1,0), Minneapolis y Kansas City AR(1)); sale con 1
mientras el bug siga abierto.

## Root cause

`evidence.estimation_text` escribe la etiqueta de la ruta U con el ladder
clásico, donde el diagonal SÍ son los univariantes; no se actualizó cuando
llegaron la ruta V y la forma echelon.

## Fix

`evidence.estimation_text`: «against the same model without cross terms (the
diagonal system): LR = …», lo que se calcula y lo que dice la cabecera. La
comparación con los univariantes es la de N5. Test:
`tests/test_echelon_route_u.py::test_the_lr_is_against_the_model_without_cross_terms`.

## Validation

El repro sale con 0: a (0, 0, 0) la línea del LR dice «against the same model
without cross terms (the diagonal system): LR = 437.511, df = 3».
