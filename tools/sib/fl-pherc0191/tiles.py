# Provenance: Project HERCULES | owner the owner | [id removed]
"""First Letters tiles (DECL-FL-1 item 1, item 2 numbers). No image is viewed; numbers only.

2 x 2 cm tiles on the render canvas (2136 px at 9.362 um), grid origin (0, 0).
Valid = render centre slice (index n//2, the surface) != 0. Keep tiles with valid >= 0.5.
Prediction u8 (official infer output), invalid pixels set to 0, cv2.INTER_AREA to 1068 px
(53.4 px/mm), PNG. ink_score (DECL-FL-2 pre-screen) = fraction of pixels >= 128 among
valid pixels of the resized tile (valid mask resized INTER_AREA, >= 0.5).
"""
import argparse, hashlib, json, os
import numpy as np, cv2, tifffile, zarr

VOX_MM = 0.009362
T = int(round(20.0 / VOX_MM))  # 2136
OUT = 1068


def render_valid(path):
    z = zarr.open(path, mode="r")
    a = z["0"] if hasattr(z, "keys") and "0" in z else z
    n = a.shape[0]
    return np.asarray(a[n // 2]) != 0, a.shape


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", required=True)
    ap.add_argument("--pred", nargs="+", required=True, help="direction=path.tif")
    ap.add_argument("--segment", required=True)
    ap.add_argument("--source", default="auto")
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    valid, shp = render_valid(a.render)
    H, W = valid.shape
    os.makedirs(a.outdir, exist_ok=True)
    rows = []
    for spec in a.pred:
        d, p = spec.split("=", 1)
        pred = tifffile.imread(p)
        pred = np.asarray(pred).squeeze()
        assert pred.dtype == np.uint8 and pred.shape == (H, W), (pred.dtype, pred.shape, (H, W))
        for r in range(H // T):
            for c in range(W // T):
                v = valid[r * T:(r + 1) * T, c * T:(c + 1) * T]
                vf = float(v.mean())
                if vf < 0.5:
                    continue
                t = pred[r * T:(r + 1) * T, c * T:(c + 1) * T].copy()
                t[~v] = 0
                small = cv2.resize(t, (OUT, OUT), interpolation=cv2.INTER_AREA)
                vm = cv2.resize(v.astype(np.float32), (OUT, OUT), interpolation=cv2.INTER_AREA) >= 0.5
                ink = float((small[vm] >= 128).mean()) if vm.any() else 0.0
                name = f"{d}_r{r:02d}_c{c:02d}.png"
                fn = os.path.join(a.outdir, name)
                ok, buf = cv2.imencode(".png", small)
                assert ok
                open(fn, "wb").write(buf.tobytes())
                rows.append(dict(segment=a.segment, direction=d, r=r, c=c, file=name,
                                 png_sha256=hashlib.sha256(buf.tobytes()).hexdigest(),
                                 valid_fraction=round(vf, 5), px_per_mm=OUT / 20.0,
                                 source=a.source, ink_score=round(ink, 6),
                                 canvas_xywh=[c * T, r * T, T, T]))
    man = dict(scroll="PHerc0191", segment=a.segment, source=a.source, render_shape=list(shp),
               tile_px_native=T, tile_px_out=OUT, voxel_um=VOX_MM * 1000,
               valid_rule="render centre slice != 0", tiles=rows)
    json.dump(man, open(os.path.join(a.outdir, "manifest.json"), "w"), indent=1)
    print(json.dumps(dict(segment=a.segment, n_tiles=len(rows), H=H, W=W)))


if __name__ == "__main__":
    main()
