# Provenance: Project HERCULES | owner the owner | [id removed]
"""Usage: timed.py <out.json> <command...>. Runs the command and writes its wall time, exit code and peak RSS
(getrusage RUSAGE_CHILDREN ru_maxrss, kB) as JSON; exits with the command's exit code."""
import json
import resource
import subprocess
import sys
import time

out, cmd = sys.argv[1], sys.argv[2:]
t0 = time.time()
rc = subprocess.call(cmd)
json.dump(dict(command=cmd, exit_code=rc, wall_s=round(time.time() - t0, 2),
               peak_rss_kb=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss), open(out, "w"), indent=1)
sys.exit(rc)
