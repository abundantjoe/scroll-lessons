"""Synthetic surfaces and volumes with known geometry, for tests and for seeing what a layer jump looks like."""
import numpy as np
from .tifxyz import write

def cylinder_patch(R, theta0, theta1, z0, z1, n=60, cx=0.0, cy=0.0, jump_at=None, jump_dr=0.0):
    """A patch of a cylinder of radius R about axis (cx, cy); rows = z, cols = theta.
    With jump_at (0..1 along theta) and jump_dr, the radius steps to R+jump_dr past that point: a layer jump."""
    th = np.linspace(theta0, theta1, n); z = np.linspace(z0, z1, n)
    T, Zg = np.meshgrid(th, z); r = np.full_like(T, float(R))
    if jump_at is not None:
        r[T > theta0 + jump_at * (theta1 - theta0)] = R + jump_dr
    return (cx + r * np.cos(T)).astype(np.float32), (cy + r * np.sin(T)).astype(np.float32), Zg.astype(np.float32)

def shell_volume(shape, cx, cy, radii, thickness=2.0, value=200):
    """A uint8 volume (z, y, x) with bright cylindrical shells at the given radii about (cx, cy)."""
    zz, yy, xx = np.indices(shape); rr = np.hypot(xx - cx, yy - cy); v = np.zeros(shape, np.uint8)
    for R in radii:
        v[np.abs(rr - R) <= thickness] = value
    return v

def save_patch(d, **kw):
    X, Y, Z = cylinder_patch(**kw); write(d, X, Y, Z); return X, Y, Z
