---
id: BUG-0017
title: Una prueba de las cachés que falla deja su bootstrap corriendo, desligado, sin nada que lo pare
status: open
severity: low
component: tests
found_in: 0.2.4
fixed_in:
reported: 2026-11-17
reporter: David / Claude — suite de sima contra drvarma 0.3.4
tags:
  - jobs
  - tests
references:
  - tests/test_example_caches.py (test_the_tutorial_rank_returns_at_once, _rerun)
  - BUG-0015 (el fallo de caché que lo dispara)
  - bugs/BUG-0017-repro/repro.py
---

## Resumen

`test_the_tutorial_rank_returns_at_once` lanza el contraste de rango del
tutorial con `wait=5`. Cuando la caché no casa (un drvarma nuevo, BUG-0015), el
trabajo se lanza, la prueba falla en sus asertos, y el trabajo sigue
corriendo, desligado como lo están los de sima, en la carpeta temporal de la
prueba. `_rerun` hace lo mismo si su espera o un aserto fallan. El 16 y
17-nov-2026, cinco de ellos siguieron once horas después de la suite,
compitiendo por la CPU con todo lo demás.

## Impacto

Bajo para el usuario; alto para quien corre la suite: deja la máquina cargada
durante horas sin que se vea.

## Reproducción

`bugs/BUG-0017-repro/repro.py`: corre esa prueba para lutkepohl_e1 bajo pytest
con un plugin que fuerza el fallo de caché, y busca los procesos que quedan en
su carpeta temporal (y los para). Sale 1 mientras quede alguno.

## Arreglo propuesto

Un fixture que cancele (`jobs.cancel`) los trabajos que la prueba lanzó, al
acabar, pase o falle.
