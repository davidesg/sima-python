---
id: BUG-0011
title: Un VARMA cuya búsqueda no salió del arranque diagonal se presenta como estimación, y su LR = 0 como prueba de que no hay dinámica cruzada
status: open
severity: high
component: estimate
found_in: 0.2.2
fixed_in:
reported: 2026-11-15
reporter: David / Claude — auditoría de la escala en la escalera completa
tags:
  - scale
  - optimiser
  - varma
references:
  - src/sima/mcp_server.py (estimate), src/sima/evidence.py (la tabla y la línea del LR)
  - drvarma ladder.py (Ladder.fit, el estado de la búsqueda)
  - art BUG-0257, drtran BUG-68 (la escala que lo provoca)
  - bugs/BUG-0011-repro/repro.py
---

## Summary

Con dos series en torno a 10 000 y λ = −1, estimadas por fue con
`refactor = 100` (lo que escribe art), la serie estacionaria vale
99.99 ± 0.0001 y el optimizador se para en su primer paso. sima lo presenta
como un ajuste:

```
optimiser: stopped: the last step found no lower point (1 iterations)
  AR1[Y<-X]      0.000000    0.100000     0.00
  AR1[X<-Y]      0.000000    0.100000     0.00
against the same model without cross terms (the diagonal system): LR = 0.000, df = 3, p = 1.0000
```

Los coeficientes cruzados son la semilla (0) y sus errores típicos la semilla
de la búsqueda (0.1000). Los mismos ficheros con `refactor = 10 000` dan
AR1[Y<-X] = 0.4577 (t = 12.2) y LR = 120.9.

## Impact

Alto: «no hay dinámica cruzada, p = 1» es una conclusión científica y aquí es
un artefacto de la escala. Nada lo distingue de un resultado. Igual con los
motores C de las ruedas que con los de Python puro (auditoría del
15-nov-2026). Con el mismo dato, mtram (drtran) sí estima la transferencia en
esta muestra y no en otra de 160 observaciones: el caso es marginal para
drtran y no lo es para la escalera de drvarma.

## Reproduction

`bugs/BUG-0011-repro/repro.py`: series sintéticas. Sale con 1 mientras sima dé
LR = 0.000 para los ficheros con `refactor = 100`.

## Root cause

Dos cosas. La escala (art BUG-0257): μ ≈ 100 con una dispersión de 1e-4 no se
puede mover por pasos relativos. Y, propio de sima: una búsqueda que acaba en
la primera iteración sin mejorar el arranque no es un ajuste, y `estimate` la
trata como tal.

## Fix

Un ajuste que no mejora la verosimilitud del arranque diagonal en ninguna
iteración se dice como lo que es —la búsqueda no arrancó—, sin tabla de
coeficientes ni LR, con la causa probable (la escala de los ficheros: la
comprobación de `load_pre`, BUG-0012) y qué hacer. La comprobación de escala
al cargar evita llegar aquí.

## Validation

Pendiente.
