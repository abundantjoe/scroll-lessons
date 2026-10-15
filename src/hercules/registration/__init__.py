# Provenance: Project HERCULES | owner the owner | [id removed]
"""Registration of a 9 um CT volume onto a ~2.4 um rescan of the same scroll.

Modules: c6 (method C6: axis-flip test, per-patch 3-D phase correlation,
affine translation field, forward/inverse maps), synthetic (TEST HELPER ONLY:
synthetic 9 um / rescan pairs with a known C6 transform).
"""
from hercules.registration.c6 import (
    ArrayReader,
    C6Transform,
    Orientation,
    OrientedReader,
    candidate_orientations,
    downsample_area,
    evaluate_patches,
    fit_affine,
    map_9_to_r,
    map_r_to_9,
    ncc,
    phase_correlate_3d,
    register,
    scale_factor,
)

__all__ = [
    "ArrayReader",
    "C6Transform",
    "Orientation",
    "OrientedReader",
    "candidate_orientations",
    "downsample_area",
    "evaluate_patches",
    "fit_affine",
    "map_9_to_r",
    "map_r_to_9",
    "ncc",
    "phase_correlate_3d",
    "register",
    "scale_factor",
]
