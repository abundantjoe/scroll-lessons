# Provenance: Project HERCULES | owner the owner | [id removed]
"""Label-quality ranking of PHerc0139 segments for the D2 pairs (numbers only; no image is viewed).
Label source for every pair = the organizer 2.399 um ink map (model 20260417190342): ink >= 150, blank <= 100,
rest ignored. Ranking (fixed before any number was computed):
  Tier A = segments with the official 2.399 um human label set 20260918, ranked by Cohen's kappa between the ink-map
           labels and the human labels (ink = inklabels > 0 inside supervision; blank = supervision without ink) on
           pixels where both are defined.
  Tier B = the rest, ranked by crispness = n(map >= 150) / n(map >= 101) over mesh-valid canvas pixels.
Mesh-valid 2.399 um canvas pixel P: nearest grid vertex floor((P + 10.5) / 20) valid (renderer, s = 0.05).
Usage: labelq.py SEG... (appends to /work/p139/labelq.jsonl)."""
import json, sys, glob, os, time
import numpy as np, tifffile, zarr
from hercules.geometry.tifxyz import read_tifxyz, valid_mask
from fetch import get, listing

S = "/work/p139/s3/PHerc0139/segments"


def inkmap_key(seg):
    objs, _ = listing(f"PHerc0139/segments/{seg}/ink-detection/", "/")
    k = [o for o, _ in objs if "-2.399um-" in o and "20260417190342" in o and o.endswith(".tif")]
    assert len(k) == 1, k
    return k[0]


def mesh_valid(seg, shape):
    ts = seg.split("-")[0]
    m = read_tifxyz(f"{S}/{seg}/mesh/{ts}-on-20260102150214-2.399um.tifxyz")
    vm = valid_mask(m.points)
    H, W = vm.shape
    ri = np.minimum((np.arange(shape[0]) + 10.5) // 20, H - 1).astype(int)
    ci = np.minimum((np.arange(shape[1]) + 10.5) // 20, W - 1).astype(int)
    return vm[ri][:, ci]


def kappa(a, b):
    n = a.size
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")


def one(seg):
    t0 = time.time()
    key = inkmap_key(seg)
    p, h = get(key)
    im = tifffile.imread(p)
    assert im.dtype == np.uint8 and im.ndim == 2, (im.dtype, im.shape)
    val = mesh_valid(seg, im.shape)
    v = im[val]
    n_ink = int((v >= 150).sum()); n_amb = int(((v > 100) & (v < 150)).sum()); n_blank = int((v <= 100).sum())
    r = dict(segment=seg, short=seg.split("-")[1].split("_")[0], inkmap_key=key, inkmap_sha256=h,
             shape=list(im.shape), n_valid=int(val.sum()), n_ink=n_ink, n_amb=n_amb, n_blank=n_blank,
             crispness=n_ink / max(1, n_ink + n_amb), outside_valid_nonzero=int((im[~val] > 0).sum()))
    L = f"PHerc0139/segments/{seg}/ink-labels/2.399um-volume-20260102150214/20260918"
    objs, _ = listing(L + "/")
    if objs:
        for k, _ in objs:
            if k.split("/")[-4] in ("inklabels.zarr", "supervision.zarr") or "/0/" in k or k.endswith("zarr.json"):
                if "/0/" in k or k.endswith(".zarr/zarr.json"):
                    get(k)
        lab = np.asarray(zarr.open(f"/work/p139/s3/{L}/inklabels.zarr", mode="r")["0"][:]) > 0
        sup = np.asarray(zarr.open(f"/work/p139/s3/{L}/supervision.zarr", mode="r")["0"][:]) > 0
        assert lab.shape == im.shape, (lab.shape, im.shape)
        dec = sup & ((im >= 150) | (im <= 100))
        a = im[dec] >= 150; b = lab[dec]
        r["human"] = dict(label_set="20260918@20260102150214", n_supervised=int(sup.sum()), n_both=int(dec.sum()),
                          map_ink_human_ink=int((a & b).sum()), map_ink_human_blank=int((a & ~b).sum()),
                          map_blank_human_ink=int((~a & b).sum()), map_blank_human_blank=int((~a & ~b).sum()),
                          agreement=float((a == b).mean()), kappa=kappa(a, b),
                          supervised_outside_mesh_valid=int((sup & ~val).sum()))
    r["seconds"] = round(time.time() - t0, 1)
    with open("/work/p139/labelq.jsonl", "a") as f:
        f.write(json.dumps(r) + "\n")
    print(json.dumps({k: v for k, v in r.items() if k not in ("inkmap_key",)}), flush=True)
    os.remove(p) if os.environ.get("LABELQ_DELETE") else None


if __name__ == "__main__":
    for s in sys.argv[1:]:
        one(s)
