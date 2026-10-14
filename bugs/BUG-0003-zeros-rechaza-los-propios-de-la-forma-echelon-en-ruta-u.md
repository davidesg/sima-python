---
id: BUG-0003
title: En ruta U, zeros (y simplify) rechazan los coeficientes propios de la forma echelon, que ya no son de art
status: fixed
severity: medium
component: server
found_in: 0.1.0
fixed_in: 0.1.0
reported: 2026-10-14
reporter: David / Claude — ejemplo lutkepohl_poskitt en ruta U con los modelos de art, forma echelon
tags:
  - estimate
  - simplify
  - zeros
  - forma-echelon
references:
  - src/sima/mcp_server.py _split_zeros (~l. 342): `if s.route != "V": raise`
  - src/sima/mcp_server.py simplify (~l. 1213, 1230): `s.route == "V" and _OWN.fullmatch(nm)`
  - src/sima/mcp_server.py _model_ladder (~l. 382): own="free" si hay índices y la ruta no es V
---

## Summary

En ruta U, `estimate(indices=..., zeros="theta_Buffalo[B^1], ...")` falla con

    'theta_Buffalo[B^1]' is a coefficient of a univariate model: on route U
    the diagonal is art's — simplify it there.

En la forma echelon eso no es cierto. `_model_ladder` pasa `own="free"` y la
propia cabecera de `estimate` dice «On route U the own AR(n_i)/MA(n_i)
replaces each univariate model's regular ARMA». Los φ_i/θ_i de la forma
echelon son de sima, no de art, y «simplify it there» no tiene dónde hacerse.

Consecuencia en el ejemplo: el VAR(1) dentro de (1, 1, 1) —la forma echelon
sin su parte MA, el paso de Lütkepohl y Poskitt— no se puede escribir.
`simplify` sobre un ajuste echelon en ruta U tiene el mismo filtro
(`s.route == "V"`), así que tampoco propone nunca quitar un propio, aunque en
(1, 1, 1) θ_Minneapolis y θ_KansasCity estén en −1.000.

## Impact

Medio: la forma echelon en ruta U no se puede simplificar por sus
coeficientes propios, que es justo donde está el sobreajuste (dos MA propios
en la pared). Hay que rodearlo con la ruta V o con el ladder clásico, que no
es el mismo modelo.

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0003-repro/repro.py` — con los `.pre` de art
del ejemplo (Buffalo (0,1,0), Minneapolis y Kansas City AR(1)); sale con 1
mientras el bug siga abierto.

## Root cause

El criterio «propio = de art» es por ruta (`s.route != "V"`) y debería ser por
modelo: propio de art sólo cuando la fila conserva el ARMA del univariante
(`own="spec"`). Con índices de Kronecker en ruta U (`own="free"`) el propio es
libre, como en ruta V.

## Fix

En `_split_zeros` y en los dos filtros de `simplify`, aceptar los propios
cuando `s.route == "V"` **o** el ajuste es una forma echelon (índices no
vacíos). Comprobar que `_files_for` / el Ladder aplican el cero propio a la
parte libre de la fila y no al factor de fila (estacional o de frecuencia
fija), que sigue siendo de art. Actualizar el docstring de `estimate`
(«own ... on route V only») y el MANUAL-jenkins-alavi §2.5.

## Validation

Arreglado en sima y en drvarma:

- drvarma (rama `ladder`): `LadderSeries.with_regular(k, zeros=)` y
  `Ladder(..., own="free", own_zeros=)` fijan a cero retardos de la parte
  propia libre, que salen también de los mínimos cuadrados del arranque.
- sima: `_own_is_free` —ruta V, o forma echelon con índices— decide si
  `zeros` y `simplify` alcanzan los propios; en ruta U sin índices siguen
  siendo de art.

El repro sale con 0. En el ejemplo, el VAR(1) dentro de (1, 1, 1) en ruta U da
logL −667.677245, el de la ruta V, y su VAR(1) restringido −669.129921, el de
su Tabla 2; `simplify` propone `phi_KansasCity[B^1]`, como ellos. Tests:
`tests/test_echelon_route_u.py` (sima) y
`test_echelon_rowfactor.py::test_own_zeros_hold_the_free_own_lags_at_zero`
(drvarma). MANUAL-echelon §2.3 y §5.3, MANUAL-jenkins-alavi §2.5.
