# Provenance: Project HERCULES | owner the owner | [id removed]
"""Frozen-encoder feature cache for LC384 training (task devloop-r1). Numbers only; pixel arrays never printed.

Input: D2 pair shards of the pairs0139 sibling (npz: images uint8 (N,21,128,128) = render slices 5..25, label uint8
(N,128,128) 1 ink / 0 blank / 255 ignored) and their registry rows (JSON lines: tile_id, segment, canvas9_y0,
canvas9_x0, shard, shard_index). Only rows listed in --allow (a JSON list of tile_ids that passed the DEV-window and
clean-control exclusions; built by lc_pool.py) are cached.
Per tile: the model window is stack index 2..18 = render slices 7..23 (the centre 17 of the -n 31 render, identical to
official flat inference's select_layer_indices on a 31-slice render); --order reverse reverses it (REV control).
Normalisation: official normalize_flat_patch(tifxyz_robust), i.e. exactly what inference applies per patch.
Encoder: frozen base stem + 2-D encoder (lc_model.LC384.encode), fp32, eval mode.
Output (<out>/): level{0..5}.npy memory-mappable arrays (N, C, h, w) in --dtype (fp16 default) ; labels.npy (N,128,128)
uint8; tiles.json (tile_id, segment, y0, x0 per row, and 'nbr' = 9 row indices of the 3 x 3 neighbourhood at +-128 px on
the same segment, -1 where the neighbour is not in the cache); manifest.json with sha256 of every file and input."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lc_model as LM  # noqa: E402

SHAPES = [(32, 128, 128), (64, 64, 64), (128, 32, 32), (256, 16, 16), (320, 8, 8), (320, 4, 4)]
Z_LO, Z_HI = 2, 19  # stack index 2..18
DT = {"fp16": np.float16, "fp32": np.float32}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def window(stack21, order):
    w = stack21[Z_LO:Z_HI]
    return w[::-1] if order == "reverse" else w


def normalise(win_zyx):
    from vesuvius.ink_detection.inference.infer import normalize_flat_patch
    return normalize_flat_patch(np.asarray(win_zyx, dtype=np.float32), "tifxyz_robust")


def neighbour_index(rows):
    pos = {(r["segment"], int(r["y0"]), int(r["x0"])): i for i, r in enumerate(rows)}
    for r in rows:
        r["nbr"] = [pos.get((r["segment"], int(r["y0"]) + dy * 128, int(r["x0"]) + dx * 128), -1) for dy, dx in LM.OFFSETS]
    for i, r in enumerate(rows):
        assert r["nbr"][LM.CENTRE] == i
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", required=True, help="directory of pair shard npz files")
    ap.add_argument("--registry", required=True, help="directory of registry *.jsonl")
    ap.add_argument("--allow", required=True, help="JSON list of allowed tile_ids")
    ap.add_argument("--out", required=True)
    ap.add_argument("--order", choices=("forward", "reverse"), default="forward")
    ap.add_argument("--dtype", choices=tuple(DT), default="fp16")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--batch", type=int, default=8)
    a = ap.parse_args(argv)
    torch.set_num_threads(a.threads)
    os.makedirs(a.out, exist_ok=True)
    allow = set(json.load(open(a.allow)))
    rows = []
    for fn in sorted(os.listdir(a.registry)):
        if fn.endswith(".jsonl"):
            for line in open(os.path.join(a.registry, fn)):
                r = json.loads(line)
                if r.get("shard") and r.get("tile_id") in allow:
                    rows.append(dict(tile_id=r["tile_id"], segment=r["segment"], y0=int(r["canvas9_y0"]), x0=int(r["canvas9_x0"]),
                                     shard=r["shard"], shard_index=int(r["shard_index"]), shard_sha256=r.get("shard_sha256")))
    rows.sort(key=lambda r: (r["segment"], r["y0"], r["x0"]))
    assert len({r["tile_id"] for r in rows}) == len(rows), "duplicate tile ids"
    rows = neighbour_index(rows)
    N = len(rows)
    mm = [np.lib.format.open_memmap(f"{a.out}/level{l}.npy", mode="w+", dtype=DT[a.dtype], shape=(N,) + s) for l, s in enumerate(SHAPES)]
    labels = np.lib.format.open_memmap(f"{a.out}/labels.npy", mode="w+", dtype=np.uint8, shape=(N, 128, 128))
    model, _, _ = LM.build("basedec")
    model.eval()
    t0 = time.time()
    shard_sha = {}
    by_shard = {}
    for i, r in enumerate(rows):
        by_shard.setdefault(r["shard"], []).append(i)
    for sh, idx in by_shard.items():
        p = os.path.join(a.shards, sh)
        shard_sha[sh] = sha(p)
        exp = rows[idx[0]]["shard_sha256"]
        assert exp is None or exp == shard_sha[sh], f"shard hash mismatch {sh}"
        z = np.load(p)
        imgs, labs = z["images"], z["label"]
        assert imgs.dtype == np.uint8 and imgs.shape[1:] == (21, 128, 128)
        for j0 in range(0, len(idx), a.batch):
            jj = idx[j0:j0 + a.batch]
            x = torch.stack([torch.from_numpy(normalise(window(imgs[rows[i]["shard_index"]], a.order))).unsqueeze(0) for i in jj])
            with torch.inference_mode():
                sk = model.encode(x)
            for l in range(6):
                mm[l][jj] = sk[l].numpy().astype(DT[a.dtype])
            for i in jj:
                labels[i] = labs[rows[i]["shard_index"]]
    for m in mm + [labels]:
        m.flush()
    del mm, labels
    json.dump(rows, open(f"{a.out}/tiles.json", "w"))
    man = dict(provenance="Project HERCULES | owner the owner | [id removed]", n_tiles=N, order=a.order, dtype=a.dtype,
               window_stack_index=[Z_LO, Z_HI - 1], normalisation="official normalize_flat_patch tifxyz_robust",
               base_sha256=LM.BASE_SHA, seconds=round(time.time() - t0, 1), shard_sha256=shard_sha,
               n_neighbours_present=int(sum(sum(v >= 0 for v in r["nbr"]) - 1 for r in rows)),
               files={f: sha(f"{a.out}/{f}") for f in sorted(os.listdir(a.out)) if f != "manifest.json"},
               code_sha256={f: sha(os.path.join(HERE, f)) for f in ("lc_cache.py", "lc_model.py")})
    json.dump(man, open(f"{a.out}/manifest.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in man.items() if k not in ("files", "shard_sha256")}))


class Cache:
    """Read side for training: memory-mapped levels, labels, neighbour table."""

    def __init__(self, d):
        self.d = d
        self.levels = [np.load(f"{d}/level{l}.npy", mmap_mode="r") for l in range(6)]
        self.labels = np.load(f"{d}/labels.npy", mmap_mode="r")
        self.rows = json.load(open(f"{d}/tiles.json"))
        self.nbr = np.array([r["nbr"] for r in self.rows], np.int64)
        self.n = len(self.rows)

    def batch(self, idx):
        idx = np.asarray(idx)
        cen = [torch.from_numpy(np.ascontiguousarray(self.levels[l][idx])).float() for l in range(6)]
        nb = self.nbr[idx]
        present = torch.from_numpy(nb >= 0)
        safe = np.where(nb >= 0, nb, idx[:, None])
        n4 = torch.from_numpy(np.ascontiguousarray(self.levels[4][safe.ravel()])).float().view(len(idx), 9, *SHAPES[4])
        n5 = torch.from_numpy(np.ascontiguousarray(self.levels[5][safe.ravel()])).float().view(len(idx), 9, *SHAPES[5])
        return cen, n4, n5, present


if __name__ == "__main__":
    main()
