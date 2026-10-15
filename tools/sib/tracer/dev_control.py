# Provenance: Project HERCULES | owner the owner | [id removed]
"""Team-surface agreement with the half-pitch-shifted control, plus m7-consistency of both surfaces.

For one traced surface (after v2 truncation) and its team surface:
* half-pitch: at up to 300 sampled vertices, walk the m7 prediction along +n and -n (0.5 vox steps,
  up to 60 vox), skip the current sheet (the contiguous >= 170 run through the vertex, or the first
  run within 3 vox), and record the distance to the next >= 170 voxel; pitch = min of the two sides;
  half_pitch = median(pitch) / 2 (D0-SETTLED item 8: measured by code, never hard-coded).
* control: the traced vertices shifted by +half_pitch and by -half_pitch along their normals;
  frac_within_3 of each shifted set against the team surface; control = max of the two.
* m7 consistency: distance from sampled vertices of our surface and of the team surface (team
  vertices within 40 vox of our surface) to the nearest m7 >= 170 voxel.
Numbers only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/user/dominion/src")
from hercules.geometry.tifxyz import read_tifxyz, valid_mask, vertex_normals  # noqa: E402
from m7probe import TH, dist_to_prediction, open_m7  # noqa: E402
from surfmetrics import distance_to_surface  # noqa: E402


def profile_pitch(arr, p: np.ndarray, n: np.ndarray, maxd: float = 60.0, h: float = 0.5) -> float | None:
    ts = np.arange(-maxd, maxd + h, h)
    q = p[None, :] + ts[:, None] * n[None, :]
    zyx = np.round(q[:, ::-1]).astype(np.int64)
    lo, hi = zyx.min(0), zyx.max(0) + 1
    if np.any(lo < 0) or np.any(hi > np.array(arr.shape)):
        return None
    block = arr[lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]]
    v = block[zyx[:, 0] - lo[0], zyx[:, 1] - lo[1], zyx[:, 2] - lo[2]] >= TH
    c = len(ts) // 2
    near = np.nonzero(v[max(0, c - 6):c + 7])[0]
    if near.size == 0:
        return None
    # current sheet run: the run containing the in-band hit closest to the centre
    k = max(0, c - 6) + near[np.argmin(np.abs(near + max(0, c - 6) - c))]
    a = k
    while a > 0 and v[a - 1]:
        a -= 1
    b = k
    while b < len(v) - 1 and v[b + 1]:
        b += 1
    d = []
    fw = np.nonzero(v[b + 1:])[0]
    if fw.size:
        d.append(ts[b + 1 + fw[0]] - ts[c])
    bw = np.nonzero(v[:a])[0]
    if bw.size:
        d.append(ts[c] - ts[bw[-1]])
    return float(min(d)) if d else None


def analyse_control(ours_pts: np.ndarray, team_dir: Path, arr, seed: int = 0, n_pitch: int = 300,
                    n_m7: int = 800) -> dict:
    rng = np.random.default_rng(seed)
    v = valid_mask(ours_pts)
    nrm = vertex_normals(ours_pts)
    ok = v & np.all(np.isfinite(nrm), axis=-1)
    P, N = ours_pts[ok].astype(np.float64), nrm[ok].astype(np.float64)
    tm = read_tifxyz(team_dir)
    d_ours = distance_to_surface(P, tm.points, 1.0 / float(tm.scale[0]))
    sel = rng.choice(len(P), min(n_pitch, len(P)), replace=False)
    pitches = [profile_pitch(arr, P[i], N[i]) for i in sel]
    pitches = np.array([x for x in pitches if x is not None])
    half = float(np.median(pitches) / 2) if pitches.size else None
    res = {"n_vertices": int(len(P)), "frac_within_3": float(np.mean(d_ours <= 3.0)),
           "n_pitch_samples": int(pitches.size),
           "pitch_pct": [float(x) for x in np.percentile(pitches, [10, 25, 50, 75, 90])] if pitches.size else None,
           "half_pitch": half}
    if half is not None:
        cp = [float(np.mean(distance_to_surface(P + s * half * N, tm.points, 20.0) <= 3.0)) for s in (+1, -1)]
        res["control_plus"], res["control_minus"] = cp
        res["control"] = max(cp)
        res["margin_vs_control"] = res["frac_within_3"] - res["control"]
    sm = rng.choice(len(P), min(n_m7, len(P)), replace=False)
    do = dist_to_prediction(arr, P[sm])
    tp = tm.points[valid_mask(tm.points)].astype(np.float64)
    from scipy.spatial import cKDTree
    near_team = tp[cKDTree(P).query(tp, k=1, workers=4)[0] <= 40.0]
    res["ours_m7_frac_le_1p5"] = float(np.mean(do <= 1.5))
    res["ours_m7_median"] = float(np.median(do))
    if len(near_team):
        st = rng.choice(len(near_team), min(n_m7, len(near_team)), replace=False)
        dt = dist_to_prediction(arr, near_team[st])
        res["team_near_m7_frac_le_1p5"] = float(np.mean(dt <= 1.5))
        res["team_near_m7_median"] = float(np.median(dt))
        res["team_near_n"] = int(len(near_team))
    # disagreement: of our vertices > 3 vox from the team surface, how many are on m7
    far = d_ours[sm] > 3.0
    res["ours_far_from_team_on_m7_frac"] = float(np.mean(do[far] <= 1.5)) if far.any() else None
    return res


if __name__ == "__main__":
    # usage: dev_control.py <run dir under /work/dev> ...   (uses metrics/v2_surface of each run)
    arr = open_m7()
    for d in sys.argv[1:]:
        d = Path(d)
        r = json.loads((d / "result.json").read_text())
        if "metrics" not in r:
            continue
        m = read_tifxyz(d / "metrics" / "v2_surface")
        team = Path("/work/s3/PHerc1203/segments/raw") / r["segment"]
        c = analyse_control(m.points, team, arr)
        c.update({"config": r["config"], "segment": r["segment"]})
        (d / "control.json").write_text(json.dumps(c, indent=1) + "\n")
        with open("/home/user/dominion/logs/sib/tracer/dev/control.jsonl", "a") as f:
            f.write(json.dumps(c) + "\n")
        print(json.dumps(c), flush=True)
