---
id: BUG-0001
title: load_pre muestra un paseo aleatorio (0,1,0) como «AR 1» en la tabla de los modelos
status: open
severity: low
component: server
found_in: 0.1.0
fixed_in: 
reported: 2026-10-14
reporter: David / Claude — ejemplo lutkepohl_poskitt en ruta U con los modelos de art
tags:
  - load_pre
  - evidence
references:
  - src/sima/evidence.py series_table (l. 28): p, q = s.orders()
  - drvarma src/drvarma/ladder.py Ladder.orders (~l. 236): len(phi) del polinomio expandido
---

## Summary

La tabla de N0 («The univariate models») da `AR 1` a Buffalo, cuyo `.pre` de
art es un (0,1,0): ∇ln Buffalo = a_t. fue necesita un AR de relleno cuando el
modelo no tiene ningún operador —un AR(1) con el coeficiente FIJO a 0.0—, y
`Ladder.orders()` (drvarma) devuelve `len(phi)` del polinomio expandido, que
cuenta ese relleno como un orden.

## Impact

Bajo: sólo la tabla. La puerta y las estimaciones no se ven afectadas (el
coeficiente está fijo a cero y la identidad logL_joint = Σ logL_i es exacta).
Pero el analista lee «AR 1» de un modelo que construyó sin AR. Es la misma
confusión que art tiene en `_lleva_arma` (art BUG-0248, punto 5).

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0001-repro/repro.py` — con el `.pre` (0,1,0) de
Buffalo y el AR(1) de Minneapolis del ejemplo; sale con 1 mientras el bug siga
abierto.

## Root cause

drvarma `Ladder.orders()`: `len(phi)` del polinomio expandido, sin mirar si los
coeficientes son libres. `orders()` sólo lo usa esta tabla.

## Fix

En drvarma, `orders()` cuenta sólo los factores con algún coeficiente libre
(o cuyo polinomio no sea idénticamente cero). El mismo criterio que art
BUG-0241 (`guion_adopt`): un factor con todas sus banderas fijas no es un
orden estimado.

## Validation

El repro: Buffalo sale `AR 0`, Minneapolis `AR 1`.
