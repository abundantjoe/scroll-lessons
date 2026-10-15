"""Optional official ABF++ (vc_flatten) path through abf/abf_uv_dump.cpp.
Enabled when the environment variable FLATCHECK_ABF_CMD holds a command
prefix that runs the driver (see abf/README.md)."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import tifffile

from . import tifxyz as TX


def available() -> bool:
    return bool(os.environ.get("FLATCHECK_ABF_CMD"))


def flatten_abf(points: np.ndarray, step: float, workdir: str | os.PathLike | None = None) -> tuple[np.ndarray, dict]:
    cmd = os.environ.get("FLATCHECK_ABF_CMD")
    if not cmd:
        raise RuntimeError("ABF++ path not configured: set FLATCHECK_ABF_CMD (see abf/README.md)")
    tmp = None
    if workdir is None:
        tmp = workdir = tempfile.mkdtemp(prefix="flatcheck_abf_", dir=os.environ.get("FLATCHECK_TMP"))
    try:
        w = Path(workdir)
        src, out = w / "patch.tifxyz", w / "uv"
        TX.write(src, TX.Tifxyz(np.asarray(points, np.float32), (1 / step, 1 / step), "patch"), overwrite=True)
        if out.exists():
            shutil.rmtree(out)
        r = subprocess.run(shlex.split(cmd) + [str(src), str(out)], capture_output=True, text=True)
        txt = r.stdout + r.stderr
        m = re.search(r"Scaling UVs by ([0-9.eE+-]+)", txt)
        info = {"exit_code": r.returncode, "abf_rescale_factor": float(m.group(1)) if m else None, "log_tail": txt[-600:]}
        if r.returncode != 0:
            if "abfFlatten failed" in txt:
                return np.full(points.shape[:2] + (2,), np.nan), info
            raise RuntimeError(f"ABF++ driver did not run (exit {r.returncode}): {txt[-300:]}")
        u = tifffile.imread(out / "u.tif").astype(np.float64)
        v = tifffile.imread(out / "v.tif").astype(np.float64)
        uv = np.stack([u, v], -1)
        uv[(u == -1) | (v == -1)] = np.nan
        return uv, info
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
