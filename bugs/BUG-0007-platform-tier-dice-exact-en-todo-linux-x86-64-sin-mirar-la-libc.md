---
id: BUG-0007
title: platform_tier() dice «exact» en todo Linux x86_64 sin mirar la libc; la caché de un ejemplo se sirve en una libm que no la reproduce
status: open
severity: low
component: jobs
found_in: 0.2.0
fixed_in:
reported: 2026-10-30
reporter: David / Claude — prueba de instalación limpia de atsw 2.1.0 en diez distribuciones
tags:
  - jobs
  - cache
  - platform
references:
  - src/sima/provenance.py platform_tier
  - src/sima/jobs.py make_key (el nivel entra en la clave)
  - tests/test_example_caches.py::test_rerunning_the_mixed_case_reproduces_its_bytes
  - drvec-python bugs/py-tests-exact-libc (el mismo criterio en sus pruebas)
---

## Summary

`platform_tier()` devuelve `"exact"` cuando `sys.platform == "linux"` y la
máquina es x86_64, sin mirar la libc. El nivel entra en la clave de la caché de
un job, y una clave que casa se presenta como «la misma computación, no una
aproximación». Entre versiones de la libm no lo es: en la prueba de instalación
limpia de atsw 2.1.0 (2026-10-30, diez distribuciones en podman, las ruedas de
PyPI), los bytes del caso mixto de `test_example_caches` difieren en AlmaLinux 8
(glibc 2.28) y Rocky 9 (glibc 2.34), y los `.out` de drvec también en Alpine
(musl). De glibc 2.35 a 2.41 (Ubuntu 22.04 y 24.04, Debian 12 y 13, openSUSE
15.6, Fedora 41) se reproducen byte a byte.

## Impact

Bajo. Las cachés de los ejemplos se construyen en glibc ≥ 2.35 y se sirven en
glibc 2.28 o musl como si se hubieran calculado allí. Las diferencias medidas
están en la duodécima cifra (un `-7.567e-12` frente a `-7.539e-12`, un
`-0.000000` frente a `0.000000`): no cambian ninguna conclusión, pero la
promesa de la clave («misma clave, mismos bytes») no se cumple, y la prueba de
bytes del caso mixto falla en esas plataformas. En Alpine la caché no casa de
todos modos, porque el motor del bootstrap (Python, sin C de drvec) está en la
clave.

## Reproduction

`bugs/BUG-0007-repro/repro.py` pregunta `platform_tier()` con la libc de cada
plataforma medida y compara con lo medido. Sale con 1 mientras alguna libc cuyos
bytes difieren dé `"exact"`.

    PYTHONPATH=src python3 bugs/BUG-0007-repro/repro.py

## Root cause

`provenance.platform_tier` decide el nivel por sistema y arquitectura. La
identidad de bytes depende además de la libm, que es parte de la libc.

## Fix

Propuesto: `"exact"` sólo con glibc ≥ 2.35 en Linux x86_64, la frontera medida.
En musl, `platform.libc_ver()` devuelve `('', '')`: hay que detectarlo aparte
(`/etc/alpine-release` o `os.confstr`), no tomarlo por glibc. Si la frontera se
mueve, se mide de nuevo con la misma prueba en contenedores.

## Validation

El repro, y la prueba de bytes del caso mixto en AlmaLinux 8, Rocky 9 y Alpine
(se salta en vez de fallar), con la caché del ejemplo sin servirse allí.
