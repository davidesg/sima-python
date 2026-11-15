---
id: BUG-0013
title: estimate_vec dice «standard errors from the finite-difference Hessian» cuando el fdhess de drvec no salió y la tabla lleva los de BFGS
status: fixed
severity: medium
component: vec
found_in: 0.2.2
fixed_in: 0.2.3 (unreleased)
reported: 2026-11-15
reporter: David / Claude — auditoría de la escala en la escalera completa
tags:
  - standard-errors
  - provenance
  - scale
references:
  - src/sima/vec.py:561 (la frase, fija)
  - drvec api.FitResult.fdhess (.ok)
  - bugs/BUG-0013-repro/repro.py
---

## Summary

La cabecera de `estimate_vec` lleva escrito «standard errors from the
finite-difference Hessian». Con dos series en logaritmos y factor 1 en los dos
ficheros (lo que escribe la GUI de atsw-gui), el `-fdhess` de drvec no sale
(`FitResult.fdhess.ok` es False) y los errores típicos son los de BFGS. La
cabecera dice lo contrario.

No es cosmético: la t de β es −28.4 con factor 1 y −10.5 con factor 100, el
mismo dato y el mismo ajuste. Con factor ≥ 10 fdhess sale y sus errores
típicos son estables de 10 a 10⁴; con ≤ 1 no sale.

## Impact

Medio: la procedencia de un error típico es parte del resultado, y sima
advierte en otros sitios de que los de BFGS no se citan.

## Reproduction

`bugs/BUG-0013-repro/repro.py`. Sale con 1 mientras la cabecera nombre el
hessiano por diferencias en un ajuste cuyo fdhess no es ok.

## Fix

La cabecera dice lo que lleva la tabla: el hessiano por diferencias cuando
`FitResult.fdhess.ok`, y si no, que son los de BFGS porque el otro no salió y
que eso es lo que pasa con una escala fuera de la banda del optimizador.

## Validation

El repro sale 0.
