# Provenance: Project HERCULES | owner the owner | [id removed]
"""Independent check of every fitted canvas affine M (affines.json) in the renderer pixel convention: for 20000
random valid 9.362 um canvas pixels p, X9 = 9.362 um mesh surface point sampled at p (RenderCanvas.pixel_to_grid,
bilinear), X2 = T(2.399 um mesh surface point sampled at M p). |X9 - X2| (9.362 um voxels) is the 3-D registration
error of the label map; the same for plain scaling by the metadata voxel ratio (pixel centres, p2 = (p+0.5)F - 0.5).
Output /work/p139/affine_validation.json."""
import json
import numpy as np
from hercules.geometry.tifxyz import read_tifxyz, valid_mask
from hercules.pipeline.canvas import canvas_for
from meshfit import load_T

S = "/work/p139/s3/PHerc0139/segments"
F = 9.362 / 2.399    # voxel sizes from the two volumes' metadata.json (checked in the report)


def sample(points, cv, rows, cols):
    v, u = cv.pixel_to_grid(rows, cols)
    H, W = points.shape[:2]
    ok = (v >= 0) & (u >= 0) & (v <= H - 1) & (u <= W - 1)
    v = np.clip(v, 0, H - 1.000001); u = np.clip(u, 0, W - 1.000001)
    r = np.floor(v).astype(int); c = np.floor(u).astype(int); t = (v - r)[:, None]; s = (u - c)[:, None]
    p = points.astype(np.float64); vm = valid_mask(points)
    ok &= vm[r, c] & vm[r, c + 1] & vm[r + 1, c] & vm[r + 1, c + 1]
    x = (1 - t) * ((1 - s) * p[r, c] + s * p[r, c + 1]) + t * ((1 - s) * p[r + 1, c] + s * p[r + 1, c + 1])
    return x, ok


def main():
    aff = json.load(open("/work/p139/affines.json"))["segments"]
    T = load_T()
    rng = np.random.default_rng(20260925)
    out = {}
    for s, a in aff.items():
        ts = s.split("-")[0]
        m9 = read_tifxyz(f"{S}/{s}/mesh/{ts}-on-20250728140407-9.362um.tifxyz")
        m2 = read_tifxyz(f"{S}/{s}/mesh/{ts}-on-20260102150214-2.399um.tifxyz")
        c9 = canvas_for(m9.points, m9.scale); c2 = canvas_for(m2.points, m2.scale)
        Hc, Wc = c9.shape
        rows = rng.uniform(0, Hc - 1, 200000); cols = rng.uniform(0, Wc - 1, 200000)
        rows = np.round(rows); cols = np.round(cols)
        X9, ok9 = sample(m9.points, c9, rows, cols)
        idx = np.nonzero(ok9)[0][:20000]
        rows, cols, X9 = rows[idx], cols[idx], X9[idx]
        M = np.array(a["M_pix9_to_pix2"])
        res = {}
        for name, (r2, c2_) in {"fitted": (M[0, 0] * rows + M[0, 1] * cols + M[0, 2], M[1, 0] * rows + M[1, 1] * cols + M[1, 2]),
                                "plain_scaling": ((rows + 0.5) * F - 0.5, (cols + 0.5) * F - 0.5)}.items():
            X2, ok2 = sample(m2.points, c2, r2, c2_)
            X2 = X2 @ T[:, :3].T + T[:, 3]
            d = np.linalg.norm(X9 - X2, axis=1)[ok2]
            res[name] = dict(n=int(ok2.sum()), p50_vox=float(np.median(d)), p95_vox=float(np.percentile(d, 95)),
                             p99_vox=float(np.percentile(d, 99)), max_vox=float(d.max()),
                             p95_um=float(np.percentile(d, 95) * 9.362))
        out[s] = res
        print(s.split("-")[1][:5], res["fitted"]["p50_vox"], res["fitted"]["p99_vox"], res["fitted"]["max_vox"],
              "| plain p50", round(res["plain_scaling"]["p50_vox"], 2), "p99", round(res["plain_scaling"]["p99_vox"], 2), flush=True)
    json.dump(dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
                   voxel_ratio=F, segments=out), open("/work/p139/affine_validation.json", "w"), indent=1)


if __name__ == "__main__":
    main()
