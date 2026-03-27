"""Runtime hook to make bundled Tcl/Tk discoverable in frozen builds."""
import os
import sys


def _base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


base = _base_dir()
tcl_dir = os.path.join(base, "tcl8.6")
tk_dir = os.path.join(base, "tk8.6")

if os.path.isdir(tcl_dir):
    os.environ["TCL_LIBRARY"] = tcl_dir
if os.path.isdir(tk_dir):
    os.environ["TK_LIBRARY"] = tk_dir

