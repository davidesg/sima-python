---
id: BUG-0014
title: Con factores de reescala distintos, α y su restricción (α = Aψ) van en unidades del motor — una restricción cierta se rechaza con p = 0.0072
status: fixed
severity: high
component: vec
found_in: 0.2.3
fixed_in: 0.2.4
reported: 2026-11-16
reporter: David / Claude — lo que quedaba de la ronda de la escala (atsw-gui docs/ESTUDIO-escala.md)
tags:
  - scale
  - vec
  - restriction
  - units
references:
  - src/sima/vec.py (alpha_reading; restriction_kw)
  - src/sima/scale.py (to_engine_alpha)
  - BUG-0012 (β, sus restricciones y θ en unidades de cada serie: α se quedó fuera)
  - bugs/BUG-0014-repro/repro.py
---

## Resumen

BUG-0012 llevó a unidades de cada serie las restricciones sobre β (`fixb2`,
`fixb2row`) y θ cuando los ficheros no comparten factor de reescala. α se quedó
en las del motor, en las dos caras:

- `estimate_vec` (`alpha_reading`) imprimía α del motor: con Y a factor 100 y X
  a 1, α_Y = 30.73, cuando en unidades de las series es 0.307;
- `test_restriction(alpha=...)` imponía α = Aψ en unidades del motor.

La fila i de α es la ecuación de la serie i: en las unidades en que se presenta
es K_i veces la del motor (K_i, el factor de presentación de la serie, salvo un
factor común a la columna que ψ absorbe). Una restricción que liga filas —α_Y =
c·α_X— es otra restricción en el motor:

```
refactor Y=100, X=100: alpha Y +0.3091, X +0.0263   H0 alpha = A psi: LR = 0.0,    p = 0.9997
refactor Y=100, X=1:   alpha Y +30.7322, X +0.0252  H0 alpha = A psi: LR = 7.2179, p = 0.0072
```

Mismos datos, mismo ajuste, la misma A (la α estimada con el factor común): se
rechaza una restricción que se cumple exactamente.

## Impacto

Alto cuando ocurre: el contraste contesta mal sin avisar. Sólo con ficheros de
factores (o λ) distintos; la debilidad exógena —una fila a cero— es la misma en
las dos unidades y no se ve afectada.

## Reproducción

`bugs/BUG-0014-repro/repro.py`, sobre los datos de BUG-0012: sale 1 mientras
α se imprima distinto con factores mezclados o la restricción cierta se
rechace.

## Arreglo

`scale.to_engine_alpha`: la fila i de A se divide por `cross(i, última)` (su
factor de presentación, salvo uno común). `restriction_kw` la aplica cuando los
ficheros no comparten factor; `alpha_reading` multiplica α por
`cross(i, la serie de normalización)`, como θ, y lo dice. Los t no cambian. Con
un factor común nada cambia.
