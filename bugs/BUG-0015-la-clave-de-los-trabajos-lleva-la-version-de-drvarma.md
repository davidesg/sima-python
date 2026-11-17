---
id: BUG-0015
title: La clave de un trabajo lleva la versión de drvarma (y de fue) — cada publicación de drvarma invalida las cachés de los ejemplos
status: wontfix
severity: medium
component: jobs
found_in: 0.2.3
fixed_in: by design (0.2.5)
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

La clave guarda las versiones para que cualquier cambio que pueda mover el
resultado lo invalide. Con el motor C, las réplicas del bootstrap son del C,
que lee los `.pre` él mismo. Pero los ajustes observados y el estadístico LR
los calcula el porte de drvec en Python **también con el motor C** («the
port's observed fits are done, they ran while the C did», `drvec.rank_test`).
Y ese porte usa el optimizador y la verosimilitud de drvarma (`_qnewt`,
`elf_c`) y lee los `.pre` con fue (`cast_us`, `forecast`). Una versión de
drvarma o de fue puede, por tanto, mover el LR observado sin tocar un byte del
C.

## Decisión: es así por diseño (17-nov-2026)

Quitar drvarma y fue de la clave cuando el motor es C (la primera propuesta)
no es seguro, por lo de arriba. Una huella del código que el bootstrap usa
sería más fina, pero frágil (qué módulos cuentan, y la extensión compilada).
Se queda la clave como está, y el coste se asume en el protocolo:
`docs/PUBLISHING.md`, paso 4. Una publicación de fue o de drvarma va seguida
de una de sima con las cachés rehechas. Con BUG-0016 arreglado, rehacerlas ya
no falla a medias.

El repro queda de guarda, con el sentido invertido: sale 0 mientras la versión
de drvarma cambie la clave, y 1 si alguien la quita.
