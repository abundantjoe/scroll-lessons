# Provenance: Project HERCULES | owner the owner | [id removed]
"""Planted-fault injectors (TEST / RUNNER ONLY).

Every injector returns an artefact whose record is internally CONSISTENT (hashes
recomputed for the faulted stack), i.e. the fault is what an honest-looking pipeline
bug would produce; it must be caught by the fault's own content check, never merely
by a hash mismatch.
"""

from __future__ import annotations

import numpy as np

from hercules.geometry.render_synth import cylinder_grid

FAULTS = ("offset8", "swap_depth", "mirror", "off_by_one", "retrace", "wrong_voxel")

OFFSET_DIRECTIONS = [(dy, dx) for dy in (-8, 0, 8) for dx in (-8, 0, 8) if (dy, dx) != (0, 0)]
WRONG_VOXELS_UM = (9.362, 9.4, 9.36, 7.91, 8.64, 3.24, 2.403, 2.399, 10.0)


def offset_origin(origin_yx, rng) -> tuple[tuple[int, int], tuple[int, int]]:
    """Origin actually rendered for an 8 px offset fault (the record keeps the original)."""
    d = OFFSET_DIRECTIONS[int(rng.integers(len(OFFSET_DIRECTIONS)))]
    return (origin_yx[0] + d[0], origin_yx[1] + d[1]), d


def swap_depth(stack: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(stack[::-1])


def mirror(stack: np.ndarray, rng) -> tuple[np.ndarray, str]:
    kind = ("flip_lr", "flip_ud")[int(rng.integers(2))]
    out = stack[:, :, ::-1] if kind == "flip_lr" else stack[:, ::-1, :]
    return np.ascontiguousarray(out), kind


def off_by_one_shift(rng) -> int:
    return (-1, 1)[int(rng.integers(2))]


def wrong_voxel(true_um: float, rng) -> float:
    cands = [v for v in WRONG_VOXELS_UM if abs(v - true_um) > 1e-9]
    cands.append(round(true_um * (1 + 1e-4), 6))  # a rounding-level error
    return float(cands[int(rng.integers(len(cands)))])


def retrace_of(radius: float, centre_xy, window_shape_hw, window_step: float, window_s0: float, window_z0: float,
               rng, *, step: float = 20.0, noise_sd: float | None = None, shape_hw=None,
               phi_ref: float = 0.0) -> tuple[np.ndarray, dict]:
    """A different trace of the SAME sheet (cylinder of ``radius``) overlapping the window:
    own grid phase, in-plane rotation, radial noise and extent."""
    Hw, Ww = window_shape_hw
    arc_w, z_w = (Ww - 1) * window_step, (Hw - 1) * window_step
    frac = float(rng.uniform(0.3, 1.0))              # overlapping fraction of the window span
    ang = float(rng.uniform(-10, 10))
    sd = float(rng.uniform(0.0, 0.5)) if noise_sd is None else float(noise_sd)
    s0 = window_s0 + float(rng.uniform(-(1 - frac), 1 - frac)) * arc_w + float(rng.uniform(0, step))
    z0 = window_z0 + float(rng.uniform(-(1 - frac), 1 - frac)) * z_w + float(rng.uniform(0, step))
    if shape_hw is None:
        shape_hw = (max(4, int(round(z_w / step)) + 2), max(4, int(round(arc_w / step)) + 2))
    p = cylinder_grid(radius, centre_xy, shape_hw, step, ang, s0=s0, z0=z0, phi_ref=phi_ref).astype(np.float64)
    if sd > 0:
        d = p[..., :2] - np.asarray(centre_xy)[None, None, :]
        d /= np.linalg.norm(d, axis=-1, keepdims=True)
        e = rng.normal(0.0, sd, p.shape[:2])
        p[..., 0] += e * d[..., 0]
        p[..., 1] += e * d[..., 1]
    return p, {"frac": frac, "angle_deg": ang, "noise_sd": sd, "s0": s0, "z0": z0, "step": step}
