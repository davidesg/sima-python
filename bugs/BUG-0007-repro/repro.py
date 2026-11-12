"""BUG-0007: route U writes a .pre that fue cannot read. raw.py inserts its
provenance comment ("* Built by sima's raw entry (route U), ...") as the FIFTH
line of the file, inside the fixed header, after fue has written it. fue (and
drvarma, which validates with fue's reader) read the header by position: the
frequency header moves from line 6 to line 7 and the file is refused,
"line 7: the frequency must be 1, 4, 12 or 'number' (it is '**')". drvec
tolerates it (its own reader), so sima's VEC runs, but the files cannot go
back to fue or to atsw-gui's sim_gui (the drvarma gate).

LRM_u.pre is the johansen_juselius example's, as route U wrote it.

    python3 bugs/BUG-0007-repro/repro.py      # exits 1 while open
    FUE=/path/to/fue python3 bugs/BUG-0007-repro/repro.py   # also runs fue
"""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
pre = os.path.join(HERE, "LRM_u.pre")
lines = open(pre).read().split("\n")

# fue's layout: a 4-line box, a blank line, then "** Frequency ..." on line 6.
shape_ok = lines[5].startswith("** Frequency")
print("line 6 is the frequency header:", shape_ok, "| line 5 is:", repr(lines[4][:60]))

fue_ok = None
fue = os.environ.get("FUE") or shutil.which("fue")
if fue:
    with tempfile.TemporaryDirectory() as d:
        shutil.copy(pre, os.path.join(d, "X.inp"))
        r = subprocess.run([fue, "X"], cwd=d, capture_output=True, text=True)
        fue_ok = r.returncode == 0
        print("fue reads it:", fue_ok, "" if fue_ok else
              "| " + [l for l in (r.stdout + r.stderr).splitlines() if "Error" in l][:1][0]
              if any("Error" in l for l in (r.stdout + r.stderr).splitlines()) else "")
else:
    print("fue not found (set FUE): checking the layout only")

sys.exit(0 if shape_ok and fue_ok is not False else 1)
