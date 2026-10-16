---
id: BUG-0006
title: Un MA(1) propio se para en θ = −1, el pliegue del cast, y estimate lo da por convergido, con t significativas y «Next: evaluate»
status: open
severity: medium
component: evidence
found_in: 0.1.0
fixed_in:
reported: 2026-10-16
reporter: David / Claude — ejemplo lutkepohl_poskitt, ruta V, índices (1, 1, 1)
tags:
  - estimate
  - forma-echelon
  - pared-MA
references:
  - drvarma src/drvarma/ladder.py _ma_boundary (~l. 55), canonicalize (~l. 448), _fit (~l. 1143)
  - src/sima/mcp_server.py estimate (~l. 1250, el aviso de la pared)
---

## Summary

En la forma echelon (1, 1, 1) de los precios de la harina (ruta V), dos MA(1)
propios acaban en **exactamente −1.000000**:

- θ_Minneapolis: e.t. 0.112, t −8.94 *
- θ_KansasCity: e.t. 0.197, t −5.07 *

El optimizador dice «converged» (termcode 1) y los errores típicos son de
fdhess. `estimate` no avisa de nada y propone «Next: evaluate».

La pared conjunta no lo detecta: la mayor raíz inversa del MA del sistema
tiene módulo 0.99916, fuera de la tolerancia de 5e-5, así que
`ma_boundary` = 0. Pero el punto no es un máximo interior: es el pliegue
del cast.

## Impact

Medio. El informe presenta como significativos dos coeficientes que están en
la frontera, y sus errores típicos no valen. El protocolo («never report a
point on the wall as an optimum», N4b `study_estimation`) no se dispara,
porque el único aviso depende de `ma_boundary`. Le pasa a cualquier MA(1)
propio cuya verosimilitud empuje hacia la no invertibilidad mientras los
cruces mantienen el MA conjunto dentro.

## Reproduction

`PYTHONPATH=src python3 bugs/BUG-0006-repro/repro.py`. Carga el ejemplo, sigue
la ruta V y estima los índices (1, 1, 1). Sale con 1 mientras haya un θ propio
en |θ| = 1 sin aviso o con asterisco.

## Root cause

El MA(1) propio se pliega: un |x| > 1 se lee como 1/x, que es la forma
invertible. Con el resto fijo, el cast da el mismo modelo a ambos lados:

| θ_Minneapolis | −0.9999 | −1.0 | −1.0001 |
|---|---|---|---|
| mayor raíz MA conjunta | 0.999097 | 0.999160 | 0.999097 |

La verosimilitud es simétrica en torno a −1, así que el gradiente se anula
allí por construcción. El cuasi-Newton se para en ese punto y declara
convergencia (criterio 1). La curvatura que mide fdhess en un pliegue no es
la de un máximo.

`_ma_boundary` sólo mira las raíces de la matriz Θ₁ conjunta. Con cruces MA
libres, un θ propio en ±1 no pone una raíz conjunta en el círculo, y el
pliegue pasa sin que nadie lo vea.

## Fix

Propuesto, sin aplicar:

1. drvarma: cuenta como frontera, además de la pared conjunta, todo
   coeficiente propio plegado que pare en |θ| ≥ 1 − MA_WALL_TOL. Por ejemplo
   `Fit.own_fold`; o incluirlo en `converged`, como hizo BUG-0010 con la
   pared.
2. sima `estimate`: si hay pliegue, quita el asterisco de esos coeficientes,
   cambia el «Next» a `study_estimation` y dilo en el bloque del optimizador:
   «stopped at the fold of an own MA(1): not an interior optimum».
3. `study_estimation`: tratar el pliegue como la pared, con un perfil en θ
   propio y la alternativa sin la parte MA (el VAR(1), que es lo que hizo el
   ejemplo).

## Validation

El repro sale con 0. Habrá un test sobre el (1, 1, 1) del ejemplo, y otro de
drvarma que compruebe que un θ propio en ±1 no cuenta como convergencia.
