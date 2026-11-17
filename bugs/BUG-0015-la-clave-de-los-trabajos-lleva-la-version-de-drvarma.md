---
id: BUG-0015
title: La clave de un trabajo lleva la versión de drvarma (y de fue) — cada publicación de drvarma invalida las cachés de los ejemplos
status: open
severity: medium
component: jobs
found_in: 0.2.3
fixed_in:
reported: 2026-11-17
reporter: David / Claude — publicación de drvarma 0.3.4 y sima 0.2.4
tags:
  - jobs
  - cache
  - examples
references:
  - src/sima/jobs.py (make_key: "versions" de drvec, drvarma y fue)
  - docs/PUBLISHING.md, paso 4
  - bugs/BUG-0015-repro/repro.py
---

## Resumen

`jobs.make_key` mete en la clave de todo trabajo las versiones de drvec,
drvarma y fue. El bootstrap del rango es de drvec (su C o su porte en
Python): con los mismos datos, argumentos, drvec y motor, un drvarma nuevo da
el mismo resultado y otra clave.

```
key with drvarma 0.3.3: 77c69e8ba807def9
key with drvarma 0.3.4: 18f437d856c82dfb
```

## Impacto

Medio. drvarma 0.3.4 sólo cambió una página HTML. Aun así, con ella en PyPI,
los siete cachés de sima 0.2.3 dejaron de casar: los tutoriales repetían el
bootstrap (minutos en vez de al instante) hasta que salió sima 0.2.4 con los
cachés rehechos. Costó 4 h de máquina y cancelar la publicación de drvarma
durante una clase. Cada publicación de drvarma ata la de sima.

## Reproducción

`bugs/BUG-0015-repro/repro.py`: la clave del mismo contraste de rango con
drvarma 0.3.3 y 0.3.4. Sale 1 mientras difieran.

## Causa

La clave guarda las versiones por prudencia: cualquier cambio en la suite
invalida el resultado. Pero el resultado del bootstrap sólo depende de los
datos, los argumentos, el motor (drvec y su C), la semilla y la plataforma, que
la clave ya lleva aparte.

## Arreglo (por decidir)

Que la clave lleve lo que cambia el resultado: drvec y su C, la plataforma, los
datos y los argumentos; no la versión de drvarma ni la de fue. Decisión de
diseño de sima, pendiente de David.
