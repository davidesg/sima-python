---
id: BUG-0007
title: La ruta U escribe .pre que fue no lee (la línea de procedencia dentro de la cabecera)
status: fixed
severity: medium
component: raw
found_in: 0.2.0
fixed_in: 0.2.2
reported: 2026-11-12
reporter: David / Claude — integración del VEC en sim_gui (atsw-gui, S10c)
tags:
  - raw
  - route-u
  - pre
references:
  - src/sima/raw.py (PROVENANCE, la inserción tras write_pre)
---

## Summary

La entrada en crudo (ruta U) escribe el `.pre` de cada serie con fue y
después le inserta la línea de procedencia («* Built by sima's raw entry
(route U), not reviewed in art») como **quinta línea**, dentro de la cabecera
fija. fue lee esa cabecera por posición: la de la frecuencia pasa de la línea
6 a la 7 y el fichero se rechaza («line 7: the frequency must be 1, 4, 12 or
'number' (it is '**')»).

## Impact

Los `.pre` de la ruta U no vuelven a fue ni a nada que valide con su lector:
drvarma (y por tanto la puerta de sim_gui en atsw-gui) los rechaza. drvec los
tolera con su propio lector, así que el VEC de sima corre y el fallo no se ve
dentro de sima. Afecta a los cuatro `.pre` del ejemplo `johansen_juselius`.

## Reproduction

    python3 bugs/BUG-0007-repro/repro.py
    FUE=/ruta/a/fue python3 bugs/BUG-0007-repro/repro.py   # además corre fue

Sale con 1 mientras esté abierto: la línea 6 no es la cabecera de la
frecuencia y fue no lo lee. Con la línea quitada, sale con 0.

## Root cause

`raw.py`, tras `model.write_pre(...)`: `lines.insert(4, PROVENANCE)`. La
posición 4 está dentro del bloque fijo de la cabecera de fue.

## Fix

Que la procedencia no rompa el formato: ponerla donde fue admite texto libre
(o en un fichero aparte, o en el guion), no entre las líneas fijas. Hay que
regenerar los `.pre` del ejemplo `johansen_juselius`.

## Validation

El repro sale con 0 con los `.pre` regenerados, y fue los lee.

## Arreglo

La cabecera de fue son cinco líneas que pueden llevar cualquier cosa (fue.c
[3.0]); la quinta, en el `.pre` que escribe fue, es la línea en blanco bajo el
recuadro. `raw.build_one` pone ahí la procedencia, en lugar de insertarla: la
frecuencia sigue en la sexta y el `.pre` vuelve a fue y a drvarma. El `.inp`
de la ruta U ya la llevaba dentro de esas cinco líneas.

Los cuatro `.pre` de `johansen_juselius` (y la copia del repro) se han
regenerado con `build_one` sobre `data/denmark.csv`: salen idénticos a los de
antes con la línea en blanco quitada, y los `.out` byte a byte. Como la clave
de la caché lleva el digest de los ficheros, la carpeta del rank test pasa de
`sima_jobs/290f7ee278756890` a `sima_jobs/9f38d2e4a3c1b869`: misma carga útil
(versiones, motor, nivel) con los digests nuevos, y `rank.out`, `rank.boot` y
`result.json` sin tocar —drvec lee los `.pre` con el cast de fue, que salta los
comentarios, así que los números no dependen de esa línea—. `example.json` apunta
a la carpeta nueva. `tests/test_raw_entry.py` comprueba que la procedencia está
en la quinta línea y la frecuencia en la sexta.
