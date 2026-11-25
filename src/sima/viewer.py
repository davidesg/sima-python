"""Open a figure in the system's viewer, as art does.

The figure travels INSIDE the answer (ImageContent), and that is the main
channel; but a host that does not paint the image leaves the analyst without
it, and half of a guided analysis is figures. So each PNG sima writes is also
handed to the desktop's viewer: os.startfile on Windows, `open` on macOS,
`xdg-open` elsewhere. Ported from art's `_visor_procede` / `_abrir_visor`
(art's BUG-0111 and BUG-0121), with the same keys:

  SIMA_NO_VIEWER / pytest   off, always;
  SIMA_VIEWER               on where it would be off: under the MCP server on
                            Windows, whose desktop host intercepts os.startfile
                            and turns it into "attach this file?".

Failing to open a window never fails the analysis, and never passes unseen:
the reason is kept in LAST_ERROR.
"""
from __future__ import annotations

import os
import sys

LAST_ERROR = ""

#: set by the MCP server's main(): under it, Windows stays off unless SIMA_VIEWER
UNDER_SERVER = False


def should_open(under_server: bool, osname: str, env, under_pytest: bool) -> bool:
    """Is the shell asked to open the figure? Decides; does not act."""
    if under_pytest or env.get("SIMA_NO_VIEWER"):
        return False
    if under_server and osname == "nt" and not env.get("SIMA_VIEWER"):
        return False
    return True


def launch(path: str) -> str:
    """Hand `path` to the viewer. Returns why it failed, or ""."""
    import subprocess
    if sys.platform.startswith("win"):
        try:
            os.startfile(path)          # type: ignore[attr-defined]
            return ""
        except Exception as e:                               # noqa: BLE001
            return f"{type(e).__name__}: {e}"
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        pr = subprocess.run([opener, path], capture_output=True, text=True, timeout=5)
        if pr.returncode != 0:
            return (pr.stderr or pr.stdout or
                    f"{opener} exited with code {pr.returncode}").strip()
    except FileNotFoundError:
        return f"{opener} is not installed"
    except subprocess.TimeoutExpired:
        pass                            # the viewer stayed in the foreground: normal
    except Exception as e:                                   # noqa: BLE001
        return f"{type(e).__name__}: {e}"
    return ""


def show(path: str) -> str:
    """Open `path` when the keys allow it; returns `path`."""
    global LAST_ERROR
    LAST_ERROR = ""
    if should_open(UNDER_SERVER, os.name, os.environ, "pytest" in sys.modules):
        LAST_ERROR = launch(path)
    return path
