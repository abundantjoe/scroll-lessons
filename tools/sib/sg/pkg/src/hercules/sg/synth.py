# Provenance: Project HERCULES | owner the owner | [id removed]
"""Synthetic SG inputs with known answers (no real data, no images).

``passing_inputs()`` builds a complete sg_check input that passes every computed item:
3 rows x 7 letters of 3.0 mm height at a 5.0 mm row pitch, read by 3 discovery readers
and 3 fresh confirmation readers with <= 30 px jitter.  Tests mutate one part at a time
to make exactly one item fail.
"""

from __future__ import annotations

import copy
import math

import numpy as np

from hercules.scorer.letters import CANONICAL_KINDS

VOXEL_UM = 9.366
METADATA = {"scan": {"tomo": {"acquisition": {"detector": {"samplePixelSize": VOXEL_UM / 1000.0}}}}}
PPM = 1000.0 / VOXEL_UM  # canvas px per mm
CANVAS_WH = (8000, 8000)
ORIGIN = (3000.0, 3000.0)
N_ROWS, PER_ROW = 3, 7
LETTER_H_MM, PITCH_MM, ADVANCE_MM = 3.0, 5.0, 2.5
CONF_READERS = ("c1", "c2", "c3")
DISC_READERS = ("d1", "d2", "d3")
SLICE_M_READERS = ("m1", "m2", "m3")  # every SG read has its own fresh readers (ruling B13)
SLICE_P_READERS = ("p1", "p2", "p3")


def text_letters(seed: int = 7, angle_deg: float = 0.0, n_rows: int = N_ROWS, per_row: int = PER_ROW,
                 pitch_mm: float = PITCH_MM, height_mm: float = LETTER_H_MM) -> list[dict]:
    """True letters: kinds cycle through the alphabet (no two neighbours share a kind)."""
    rng = np.random.default_rng(seed)
    kinds = list(CANONICAL_KINDS)
    order = rng.permutation(len(kinds))
    out = []
    t = math.radians(angle_deg)
    for r in range(n_rows):
        for i in range(per_row):
            u, v = i * ADVANCE_MM * PPM, r * pitch_mm * PPM
            x = ORIGIN[0] + u * math.cos(t) - v * math.sin(t)
            y = ORIGIN[1] + u * math.sin(t) + v * math.cos(t)
            out.append({"ch": kinds[int(order[(r * per_row + i) % len(kinds)])], "x": x, "y": y,
                        "h": height_mm * PPM})
    return out


def read(letters, reader_ids, seed: int, jitter: float = 30.0, firm_readers=None, drop=()) -> dict:
    """Each reader names every letter (except indices in ``drop``) with jitter; box from h."""
    rng = np.random.default_rng(seed)
    firm_readers = reader_ids[:2] if firm_readers is None else firm_readers
    out = {}
    for rid in reader_ids:
        ns = []
        for i, l in enumerate(letters):
            if i in drop:
                continue
            x, y = l["x"] + rng.uniform(-jitter, jitter), l["y"] + rng.uniform(-jitter, jitter)
            h = l["h"]
            ns.append({"ch": l["ch"], "x": x, "y": y, "conf": "firm" if rid in firm_readers else "tentative",
                       "box": [x - 0.4 * h, y - 0.5 * h, x + 0.4 * h, y + 0.5 * h]})
        out[rid] = ns
    return out


def noise_tile(seed: int, n_per_reader: int = 3, reader_ids=("n1", "n2", "n3"), size: float = 2135.0) -> dict:
    """Null tile: sparse random namings (random kinds, random places)."""
    rng = np.random.default_rng(seed)
    out = {}
    for rid in reader_ids:
        out[rid] = [{"ch": CANONICAL_KINDS[int(rng.integers(len(CANONICAL_KINDS)))], "x": float(rng.uniform(0, size)),
                     "y": float(rng.uniform(0, size)), "conf": "tentative", "box": [0, 0, 1, 1]}
                    for _ in range(n_per_reader)]
    return out


def agreed_tile(n_agreed: int, seed: int) -> dict:
    """Tile where exactly ``n_agreed`` letters are named by two readers (distinct kinds, far apart)."""
    kinds = list(CANONICAL_KINDS)
    a = [{"ch": kinds[i % 24], "x": 400.0 * (i % 5), "y": 400.0 * (i // 5), "conf": "tentative"} for i in range(n_agreed)]
    return {"n1": a, "n2": copy.deepcopy(a), "n3": []}


def rotation_matrix(center, angle_deg: float) -> list[list[float]]:
    """Same convention as cv2.getRotationMatrix2D (positive = counter-clockwise on screen)."""
    a = math.radians(angle_deg)
    al, be = math.cos(a), math.sin(a)
    cx, cy = center
    return [[al, be, (1 - al) * cx - be * cy], [-be, al, be * cx + (1 - al) * cy]]


def apply_affine(readers, m):
    m = np.asarray(m, dtype=float)
    return {rid: [{**n, "x": m[0, 0] * n["x"] + m[0, 1] * n["y"] + m[0, 2],
                   "y": m[1, 0] * n["x"] + m[1, 1] * n["y"] + m[1, 2]} for n in ns] for rid, ns in readers.items()}


def passing_inputs(n_null_disc: int = 200, n_null_sg: int = 40) -> dict:
    letters = text_letters()
    disc_text = read(letters, DISC_READERS, seed=1, drop=set(range(1, 21, 2)))
    disc = {rid: {"text": disc_text[rid], "nontext": []} for rid in DISC_READERS}
    conf = read(letters, CONF_READERS, seed=2)
    centre = (ORIGIN[0] + 7.5 * PPM, ORIGIN[1] + 5 * PPM)
    rot = rotation_matrix(centre, 15.0)
    sealers = read(letters, ("s1", "s2", "s3"), seed=9, jitter=60.0)
    from .gate import compute_R  # R is declared from the discovery namings before confirmation

    rect = compute_R({rid: r["text"] for rid, r in disc.items()}, PPM, CANVAS_WH)["rect"]
    return {
        "R_declared": {"rect": rect, "record": "SYNTH-R"},
        "volume_metadata": METADATA,
        "canvas_px_per_voxel": 1.0,
        "canvas_wh": list(CANVAS_WH),
        "m": 1,
        "discovery": {"readers": disc},
        "discovery_calibration": {"null_tiles": [
            {"tile_id": f"dn{i:03d}", "readers": {rid: {"text": t, "nontext": []} for rid, t in noise_tile(i).items()}}
            for i in range(n_null_disc)]},
        "confirmation": {"readers": conf},
        "empirical_null": {"tiles": [{"tile_id": f"sn{i:02d}", "readers": noise_tile(1000 + i)} for i in range(n_null_sg)]},
        "batches": [{"batch_id": "b1", "canary": {"score": 0.8, "ref_ceiling": 1.0}, "blank": {"readers": {"c1": [], "c2": [], "c3": []}}}],
        "opposite_order": {"readers": {"c1": [conf["c1"][0]], "c2": [], "c3": []}},
        "slice_rereads": {"-1": read(letters, SLICE_M_READERS, seed=3), "+1": read(letters, SLICE_P_READERS, seed=4)},
        "second_lineage": {"meta": {"seed": 2, "fold": "B", "trained_on_this_scroll": False, "is_base": False},
                           "readers": read(letters, ("l1", "l2", "l3"), seed=5, drop=set(range(0, 21, 3)))},
        "primary_lineage": {"seed": 1, "fold": "A"},
        "retrace": {"overlap_fraction": 0.75, "neighbour_contradiction": False,
                    "readers": read(letters, ("t1", "t2", "t3"), seed=6, drop=set(range(0, 21, 4)))},
        "copy_test": {"result": {"status": "PASS", "max_abs_ncc": 0.41, "max_signed_ncc": 0.41, "min_signed_ncc": -0.38,
                                 "n_eff_min": 45.0, "neff_floor_enforced": True, "n_rotations": 24,
                                 "n_letters": len(letters), "n_patches": 500}},
        "copy_test_null": {"status": "INFORMATIVE", "n_null_tiles": 40, "false_flags": 0, "record": "SYNTH-CTN"},
        "trained_on_this_scroll": False,
        "band_1203_0846A": {"in_band": False},
        "rotation": {"canvas_to_display": rot, "readers": apply_affine(read(letters, ("o1", "o2", "o3"), seed=8), rot)},
        "attestations": {k: {"status": "PASS", "record": f"SYNTH-{k}"} for k in ("0", "8", "10", "12", "14_profile", "14_tests")},
        "_sealers_for_band": sealers,
    }
