import math
import os

import numpy as np
import pytest

STEP = 20.0


def cylinder_grid(radius, centre_xy, shape_hw, step, angle_deg, *, s0=0.0, z0=0.0):
    """Isometric grid on a cylinder (axis z), rotated angle_deg to iso-z."""
    H, W = shape_hw
    a = np.radians(angle_deg)
    vv, uu = np.mgrid[0:H, 0:W].astype(np.float64)
    s = step * (uu * np.cos(a) - vv * np.sin(a)) + s0
    z = step * (uu * np.sin(a) + vv * np.cos(a)) + z0
    phi = s / radius
    return np.stack([centre_xy[0] + radius * np.cos(phi), centre_xy[1] + radius * np.sin(phi), z], -1)


def sphere_grid(R, n, step=STEP):
    r, c = np.mgrid[0:n, 0:n].astype(float)
    a = (c - (n - 1) / 2) * step / R
    b = (r - (n - 1) / 2) * step / R
    return np.stack([np.sin(a) * np.cos(b), np.sin(b), np.cos(a) * np.cos(b)], -1) * R + 2000.0


def plane_grid(n_r, n_c, step=STEP):
    r, c = np.mgrid[0:n_r, 0:n_c].astype(float)
    e1 = np.array([1.0, 0.0, 1.0]) / math.sqrt(2)
    e2 = np.array([0.0, 1.0, 0.0])
    return 500.0 + step * (c[..., None] * e1 + r[..., None] * e2)


abf = pytest.mark.skipif(not os.environ.get("FLATCHECK_ABF_CMD"), reason="optional ABF++ path not configured")
