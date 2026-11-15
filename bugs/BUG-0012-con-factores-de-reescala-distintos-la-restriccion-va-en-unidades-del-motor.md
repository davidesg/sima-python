---
id: BUG-0012
title: Con ficheros de factores de reescala distintos, todo lo que cruza series va en unidades del motor — una β = −1 cierta se rechaza con p = 0.0000 y nada avisa
status: fixed
severity: high
component: vec
found_in: 0.2.2
fixed_in: 0.2.3 (unreleased)
reported: 2026-11-15
reporter: David / Claude — auditoría de la escala en la escalera completa
tags:
  - scale
  - vec
  - restriction
  - units
references:
  - src/sima/mcp_vec.py (test_restriction: fixb2, fixb2row, alpha), src/sima/vec.py:441-444, :852, :914-919 (theta)
  - src/sima/evidence.py (la tabla del VARMA: los cruzados), :920 (el corte 0.005 de los pesos canónicos)
  - src/sima/mcp_server.py:622-627 (_set_yardstick compara lambda, d, D; no el factor)
  - atsw-gui gui/sim/src/pagina.c:27-30, :397-401 (la regla de la GUI: cada cosa en las unidades de su serie)
  - atsw-gui engines/drvec/src/drvec.c:7282-7294 (el aviso del C)
  - bugs/BUG-0012-repro/repro.py
---

## Summary

Cada `.pre` trae su factor de reescala y el sistema se construye en
w = factor·BoxCox(z). Si los factores no coinciden, cada coeficiente entre
series lleva el cociente de los dos, y sima lo presenta y lo contrasta tal
cual. Dos series en logaritmos con log Y − log X estacionario (β = (1, −1)):

```
factor Y=100, X=100:  beta = -0.994222   alpha = 0.309104 (t 2.299)    H0 beta = -1: LR = 0.03, p = 0.8692
factor Y=100, X=1:    beta = -0.009955   alpha = 30.732151 (t 306.595) H0 beta = -1: LR = 37.46, p = 0.0000
```

El mismo dato y el mismo ajuste (la misma verosimilitud en unidades de y). En
el VARMA, el cruzado AR1[Y<-X] sale 45.84 en vez de 0.4584. Ni `load_pre`, ni
`prepare_vec`, ni `estimate_vec` dicen que los ficheros no comparten factor;
drvec C lo avisa y el porte no (drvec `bugs/py-pre-mixed-refactors-silent`).

## Impact

Alto. `test_restriction(fixb2="-1")` contrasta en realidad β = −factor_Y1/factor_i,
y rechaza una hipótesis cierta sin que nada lo indique; «theta, the long-run
coefficients» se lee cien veces fuera; los errores típicos se degradan (t de α
306 frente a 2.3: los pasos del hessiano no son conmensurables, ya medido en
drvec C, `HOMOLOGATION.md`). Ocurre hoy sin que nadie haga nada raro: la GUI de
atsw-gui escribe factor 1 en toda serie nueva y art escribe 100, así que basta
mezclar un fichero de cada origen.

## Reproduction

`bugs/BUG-0012-repro/repro.py`: series sintéticas. Sale con 1 mientras los
ficheros mezclados rechacen la hipótesis que los de factor común aceptan.

## Root cause

sima no mira el factor de los ficheros salvo para tres conversiones por serie
(la d.t. de la previsión, los residuos de las figuras). Todo lo que cruza
series se toma de los motores en sus unidades.

## Fix

`sima.scale`, con la regla de `fue.scale` (`display_cross`):

- **al cargar** (`load_pre`) se dice si los ficheros no comparten factor o λ, y
  si alguno queda fuera de la banda de escala del optimizador;
- **lo que sima escribe** va en las unidades de cada serie: los cruzados de la
  tabla del VARMA (`AR1[Y<-X]`) y θ, los coeficientes de largo plazo;
- **lo que el analista impone** (`fixb2`, `fixb2row`) se entiende en esas
  unidades y se lleva a las del motor antes de pasarlo a drvec. Si las series
  sobre las que se normalizan las relaciones no comparten factor, una fila no
  puede llevar un solo valor y se dice.

El `.out` de drvec sigue en las unidades del motor: es el del C. drvec avisa
ahora, como el C, de que los ficheros no comparten factor (drvec 0.1.2). Una
restricción `alpha` sigue en unidades del motor.

## Validation

El repro sale 0: con Y a 100 y X a 1, H0: β = −1 da LR = 0.02, p = 0.885 (antes
37.46 y 0.0000); con factor común, 0.03 y 0.869.
