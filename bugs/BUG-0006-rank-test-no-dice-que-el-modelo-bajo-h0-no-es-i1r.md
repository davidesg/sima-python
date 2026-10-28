---
id: BUG-0006
title: rank_test no dice que el modelo bajo H0 no es I(1, r); lo presenta como un bootstrap fallido
status: fixed
severity: medium
component: vec
found_in: 0.2.0
fixed_in: 0.2.0
reported: 2026-10-28
reporter: David / Claude — revisión de la documentación de drvec en sima
tags:
  - rank_test
  - drvec
  - bootstrap
references:
  - drvec-python src/drvec/api.py rank_test (Bootstrap(..., i1r=...)), src/drvec/rank.py i1r_check
  - atsw-gui #93 (drvec C, BUG-64): la comprobación I(1, r) antes de simular
  - src/sima/vec.py job_rank_test, propose_rank, rank_report
---

## Summary

drvec C 0.13 (800a540) comprueba, antes de simular, que el modelo ajustado
bajo H0 es I(1, r) (Cavaliere, Rahbek y Taylor 2012, algoritmo 1, paso ii):
todas las raíces AR de [∇Y2 ; W] fuera del círculo unidad y la covarianza de
largo plazo de ∇Y2 no singular. Si no lo es, no saca ninguna muestra y lo dice
en `Bootstrap.i1r` (la raíz AR más pequeña y la medida de rango).

sima no leía ese campo. La comparación salía con 0 réplicas, una fila de NaN
y «fewer than 10 replications ok, no critical value», y la única alternativa
era «rerun with a larger B». Se leía como un bootstrap fallido cuando es un
hallazgo sobre el modelo, y un B mayor no lo cambia.

## Impact

Cualquier rank_test cuyo modelo bajo H0 no sea I(1, r): un orden de
integración mal leído (I(2), una d que revisar) o una tendencia común perdida.
El analista recibía un consejo equivocado (subir B) y ninguna pista de la causa.

## Reproduction

    PYTHONPATH=src python3 bugs/BUG-0006-repro/repro.py   # sale con 1 mientras esté abierto

Fuerza la comprobación en r = 1 del E1 de Lütkepohl (como el test de drvec,
tests/test_rank.py::test_a_model_that_is_not_i1r_is_said_and_not_simulated) y
mira el informe.

## Root cause

`vec.job_rank_test` copiaba de cada `Bootstrap` el LR, las réplicas y los
críticos, pero no `i1r`; `propose_rank` y `rank_report` sólo distinguían
«críticos sí / no».

## Fix

`job_rank_test` guarda `i1r`. `propose_rank` no propone rango y dice por qué;
`rank_report` pone en la tabla «the model under H0 is not I(1, r): not
simulated», explica cuál de las dos condiciones falla, y ofrece releer los
órdenes de integración, otra especificación o adoptar el rango por teoría. La
figura de plot_rank_bootstrap lo anota.

## Validation

El repro sale con 0. `tests/test_vec_i1r.py`.
