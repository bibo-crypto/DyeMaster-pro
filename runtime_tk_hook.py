"""Runtime hook to make bundled Tcl/Tk discoverable in frozen builds."""
import os
import sys


def _base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


base = _base_dir()

# In onedir builds, Tcl/Tk usually lives under "<app>/_internal/".
candidate_roots = [base, os.path.join(base, "_internal")]

for root in candidate_roots:
    tcl_dir = os.path.join(root, "tcl8.6")
    tk_dir = os.path.join(root, "tk8.6")
    if os.path.isdir(tcl_dir):
        os.environ["TCL_LIBRARY"] = tcl_dir
    if os.path.isdir(tk_dir):
        os.environ["TK_LIBRARY"] = tk_dir
    if "TCL_LIBRARY" in os.environ and "TK_LIBRARY" in os.environ:
        break
