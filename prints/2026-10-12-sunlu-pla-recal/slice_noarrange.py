import sys, subprocess, os
sys.path.insert(0, os.path.expanduser("~/dev/bambu-print-model/skills/print-model/scripts"))
import orca
_run = subprocess.run
def run(cmd, **kw):
    if cmd and str(cmd[0]).endswith("OrcaSlicer") or "--slice" in cmd: cmd = list(cmd) + ["--arrange", "0"]
    return _run(cmd, **kw)
subprocess.run = run
orca.main()
