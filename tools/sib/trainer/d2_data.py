# Provenance: Project HERCULES | owner the owner | [id removed]
"""D2 trainer data interface (DECL-D2): pair registries, npz shards, D3 pools, synthetic data, patch registry.

Numbers only: nothing here renders, writes or opens an image file.

Pair registry (schema "hercules-d2-pairs/1"), written by the pairs sessions (see logs/sib/trainer/DATA_INTERFACE.md):
  registry.json = {schema, source, scroll, volume, voxel_um (from the volume's metadata.json), stack_depth: 21,
                   render: {n: 31, stack_first_slice: 5}, mesh_stride_px, halo_px: 64,
                   shards: [{file, sha256, n}]}
  shard npz keys (N patches of S x S px, S >= the largest tile that will be trained):
    image      uint8 (N, 21, S, S)     9 um render stack (render slices 5..25 of -n 31)
    target     uint8 (N, S, S)         teacher map on the 9 um canvas (2.4 um organizer map via the fitted affine)
    valid      uint8 (N, S, S)         1 where image and target are both defined
    patch_id   str   (N,)              unique within the registry
    segment    str   (N,)              organizer segment id
    canvas_yx  int64 (N, 2)            top-left of the S x S patch on the segment canvas (px)
    mesh_xyz   float32 (N, G, G, 3)    volume-frame mesh points (voxels) of the patch dilated by halo_px on every
                                       side, sampled every mesh_stride_px px: G = (S + 2 halo) // stride + 1; NaN = no mesh
Labels (DECL-D2): ink = target >= 150, blank = target <= 100, the rest and valid == 0 ignored.

D3 pool format (tools/d3/build_pools.py): images.npy (N, 21, 128, 128), inklabels.npy, supervision.npy, manifest.json
(already thresholded labels). Used for the D3-equivalence test and for replay sources."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field

import numpy as np

PAIRS_SCHEMA = "hercules-d2-pairs/1"
INK_MIN, BLANK_MAX = 150, 100
STACK_DEPTH = 21


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def labels_from_target(target: np.ndarray, valid: np.ndarray | None = None,
                       ink_min: int = INK_MIN, blank_max: int = BLANK_MAX) -> tuple[np.ndarray, np.ndarray]:
    """DECL-D2 label rule -> (ink {0,1} uint8, supervision {0,1} uint8)."""
    t = np.asarray(target)
    if t.dtype != np.uint8:
        raise ValueError(f"target must be uint8 0..255, got {t.dtype}")
    ink = t >= ink_min
    blank = t <= blank_max
    sup = ink | blank
    if valid is not None:
        sup &= np.asarray(valid).astype(bool)
    return (ink & sup).astype(np.uint8), sup.astype(np.uint8)


@dataclass
class Source:
    """One training source held in RAM: images (N, 21, S, S) uint8; ink/sup (N, S, S) uint8 {0,1}."""
    name: str
    role: str                      # "train" (NULL/REV apply) or "replay"
    images: np.ndarray
    ink: np.ndarray
    sup: np.ndarray
    registry_sha256: str
    patch_id: list = field(default_factory=list)
    segment: list = field(default_factory=list)
    canvas_yx: np.ndarray | None = None
    mesh_xyz: np.ndarray | None = None
    meta: dict = field(default_factory=dict)

    def __len__(self):
        return int(self.images.shape[0])

    @property
    def size(self) -> int:
        return int(self.images.shape[-1])


def load_pairs_registry(path: str, name: str | None = None, role: str = "train",
                        ink_min: int = INK_MIN, blank_max: int = BLANK_MAX) -> Source:
    reg = json.load(open(path))
    if reg.get("schema") != PAIRS_SCHEMA:
        raise ValueError(f"{path}: schema {reg.get('schema')!r} != {PAIRS_SCHEMA!r}")
    if int(reg.get("stack_depth", 0)) != STACK_DEPTH:
        raise ValueError(f"{path}: stack_depth must be {STACK_DEPTH}")
    if "voxel_um" not in reg:
        raise ValueError(f"{path}: voxel_um missing (must come from the volume's metadata.json)")
    root = os.path.dirname(os.path.abspath(path))
    imgs, inks, sups, pid, seg, cyx, mxyz = [], [], [], [], [], [], []
    for sh in reg["shards"]:
        f = os.path.join(root, sh["file"])
        got = sha256_file(f)
        if got != sh["sha256"]:
            raise ValueError(f"shard {f}: sha256 {got} != registry {sh['sha256']}")
        with np.load(f, allow_pickle=False) as z:
            im = z["image"]
            if im.dtype != np.uint8 or im.ndim != 4 or im.shape[1] != STACK_DEPTH or im.shape[2] != im.shape[3]:
                raise ValueError(f"{f}: image must be uint8 (N, 21, S, S), got {im.dtype} {im.shape}")
            if int(sh["n"]) != im.shape[0]:
                raise ValueError(f"{f}: n {sh['n']} != {im.shape[0]}")
            k, s = labels_from_target(z["target"], z["valid"] if "valid" in z.files else None, ink_min, blank_max)
            imgs.append(im); inks.append(k); sups.append(s)
            pid += [str(x) for x in z["patch_id"]]
            seg += [str(x) for x in z["segment"]]
            cyx.append(z["canvas_yx"].astype(np.int64))
            mxyz.append(z["mesh_xyz"].astype(np.float32) if "mesh_xyz" in z.files else None)
    if len(set(pid)) != len(pid):
        raise ValueError(f"{path}: duplicate patch_id")
    mesh = None if any(m is None for m in mxyz) else np.concatenate(mxyz)
    return Source(name=name or reg["source"], role=role, images=np.concatenate(imgs), ink=np.concatenate(inks),
                  sup=np.concatenate(sups), registry_sha256=sha256_file(path), patch_id=pid, segment=seg,
                  canvas_yx=np.concatenate(cyx), mesh_xyz=mesh,
                  meta=dict(kind="pairs", registry=os.path.abspath(path), scroll=reg.get("scroll"),
                            volume=reg.get("volume"), voxel_um=reg["voxel_um"],
                            mesh_stride_px=reg.get("mesh_stride_px"), halo_px=reg.get("halo_px"),
                            label_rule=dict(ink_min=ink_min, blank_max=blank_max)))


def load_d3_pool(pd: str, name: str, role: str) -> Source:
    """tools/d3/build_pools.py format (manifest-verified, labels already thresholded)."""
    man_path = os.path.join(pd, "manifest.json")
    man = json.load(open(man_path))
    for f, h in man["files_sha256"].items():
        got = sha256_file(os.path.join(pd, f))
        if got != h:
            raise ValueError(f"{pd}/{f}: sha256 {got} != manifest {h}")
    im = np.load(os.path.join(pd, "images.npy"))
    ink = np.load(os.path.join(pd, "inklabels.npy"))
    sup = np.load(os.path.join(pd, "supervision.npy"))
    tiles = man.get("tiles") or []
    pid = [str(t.get("id", i)) if isinstance(t, dict) else str(t) for i, t in enumerate(tiles)] or \
          [str(i) for i in range(len(im))]
    return Source(name=name, role=role, images=im, ink=ink, sup=sup, registry_sha256=sha256_file(man_path),
                  patch_id=pid, segment=[""] * len(im), meta=dict(kind="d3_pool", dir=os.path.abspath(pd)))


def load_stagec(root: str, name: str, role: str = "train", allow_ids: str | None = None,
                ink_min: int = INK_MIN, blank_max: int = BLANK_MAX, data_root: str | None = None) -> Source:
    """pairs-session stage-C layout (tools/sib/pairs0814/stage_c.py): <root>/shards.json
    {shards: [{shard, branch?, n, bytes, sha256, patch_ids}]}. A shard is either a packed npz or (since pairs0814
    ede21e3) a staged block npz given by a repo-relative path (logs/sib/pairs0814/... on one branch,
    data/sib/pairs0814b/... on another); paths resolve against data_root (a materialised tree of both branches),
    falling back to root. npz keys: images uint8 (N, 21, P, P), ref9, labels {0, 1, 255}, valid, xyz (N, 17, 17, 3),
    patch_id, optional segment. Segment and canvas box come from <root>/pair_registry.json when present.
    Only the patch_ids listed for a shard are used. Labels are recomputed from ref9 (DECL-D2 rule) and must equal
    the stored labels. allow_ids: declared allowlist (sha256 recorded)."""
    man_path = os.path.join(root, "shards.json")
    man = json.load(open(man_path))
    keep = None
    meta = dict(kind="stagec", dir=os.path.abspath(root), data_root=os.path.abspath(data_root or root),
                label_rule=dict(ink_min=ink_min, blank_max=blank_max), mesh_stride_px=24, halo_px=0, mesh_kind="grid",
                halo_note="xyz covers the patch only; FL-09 halo must be added by the checker")
    if allow_ids:
        keep = set(json.load(open(allow_ids)))
        meta.update(allow_ids=os.path.abspath(allow_ids), allow_ids_sha256=sha256_file(allow_ids))
    preg = {}
    rp = os.path.join(root, "pair_registry.json")
    if os.path.exists(rp):
        preg = {r["patch_id"]: r for r in json.load(open(rp))["patches"]}
        meta["pair_registry_sha256"] = sha256_file(rp)
    imgs, inks, sups, pid, seg, cyx, mx = [], [], [], [], [], [], []
    mism = 0
    for sh in man["shards"]:
        cands = [os.path.join(data_root, sh["shard"])] if data_root else []
        cands.append(os.path.join(root, sh["shard"]))
        f = next((c for c in cands if os.path.exists(c)), cands[-1])
        got = sha256_file(f)
        if got != sh["sha256"]:
            raise ValueError(f"shard {f}: sha256 {got} != shards.json {sh['sha256']}")
        want = [i for i in sh.get("patch_ids", []) if keep is None or i in keep]
        with np.load(f, allow_pickle=False) as z:
            ids = [str(x) for x in z["patch_id"]]
            if not sh.get("patch_ids"):
                want = [i for i in ids if keep is None or i in keep]
            zseg = [str(x) for x in z["segment"]] if "segment" in z.files else None
            for pid_ in want:
                i = ids.index(pid_)
                k, sp = labels_from_target(z["ref9"][i], z["valid"][i].astype(np.uint8), ink_min, blank_max)
                mism += int(np.sum(z["labels"][i] != np.where(sp == 1, k, 255)))
                im = z["images"][i]
                if im.dtype != np.uint8 or im.ndim != 3 or im.shape[0] != STACK_DEPTH:
                    raise ValueError(f"{f}[{pid_}]: images must be uint8 (21, P, P)")
                r = preg.get(pid_, {})
                imgs.append(im); inks.append(k); sups.append(sp); pid.append(pid_)
                seg.append(r.get("segment") or (zseg[i] if zseg else ""))
                cyx.append((int(r.get("y0", -1)), int(r.get("x0", -1))))
                mx.append(z["xyz"][i].astype(np.float32))
    if mism:
        raise ValueError(f"{root}: stored labels differ from the DECL-D2 rule on {mism} px")
    if not imgs:
        raise ValueError(f"{root}: no patch selected")
    if len(set(pid)) != len(pid):
        raise ValueError(f"{root}: duplicate patch_id")
    meta.update(label_recount_mismatch_px=0, n_patches=len(imgs))
    return Source(name=name, role=role, images=np.stack(imgs), ink=np.stack(inks), sup=np.stack(sups),
                  registry_sha256=sha256_file(man_path), patch_id=pid, segment=seg, canvas_yx=np.array(cyx, np.int64),
                  mesh_xyz=np.stack(mx), meta=meta)


def load_tilegrid(root: str, name: str, role: str = "train", mosaic: int = 1, allow_ids: str | None = None,
                  ink_min: int = INK_MIN, blank_max: int = BLANK_MAX) -> Source:
    """pairs-session tile-grid layout (as written by tools/sib/pairs0139/build_pairs.py on its own branch):
    <root>/registry/*.jsonl rows {tile_id, segment, canvas9_y0, canvas9_x0, size, xyz_centre, xyz_corners, shard,
    shard_index, shard_sha256, ...} (every candidate; kept tiles carry a shard) and <root>/shards/<name>.npz with
    images uint8 (N, 21, 128, 128) (render slices 5..25), label uint8 {0, 1, 255}, inkmap uint8 (area-averaged map),
    tile_id. Labels: label 1 must have inkmap >= 150 and label 0 inkmap <= 100 (checked; mismatch -> refused);
    ink = label == 1, supervised = label != 255.
    mosaic k > 1: patches are the complete k x k blocks of kept tiles of one segment whose top-left tile sits at a
    canvas position divisible by k * size (non-overlapping, grid-aligned, deterministic); adjacent tiles are crops of
    the same render, so a block is an exact (k * size) px crop. Tiles outside complete blocks are not used.
    The 3-D registry holds each patch's tile corners and centres (xyz_corners / xyz_centre, voxels); a mesh-based
    FL-09 check can re-sample the segment mesh from segment + canvas_yx."""
    import glob
    rows = []
    for f in sorted(glob.glob(os.path.join(root, "registry", "*.jsonl"))):
        rows += [json.loads(l) for l in open(f) if l.strip()]
    kept = [r for r in rows if r.get("shard")]
    keep = None
    meta = dict(kind="tilegrid", dir=os.path.abspath(root), mosaic=mosaic,
                label_rule=dict(ink_min=ink_min, blank_max=blank_max), halo_px=0,
                registry_files_sha256={os.path.basename(f): sha256_file(f)
                                       for f in sorted(glob.glob(os.path.join(root, "registry", "*.jsonl")))})
    if allow_ids:
        keep = set(json.load(open(allow_ids)))
        meta.update(allow_ids=os.path.abspath(allow_ids), allow_ids_sha256=sha256_file(allow_ids))
        kept = [r for r in kept if r["tile_id"] in keep]
    shard_ok, tiles = {}, {}
    for r in kept:
        sh = r["shard"]
        if sh not in shard_ok:
            f = os.path.join(root, "shards", sh)
            got = sha256_file(f)
            if got != r["shard_sha256"]:
                raise ValueError(f"shard {f}: sha256 {got} != registry {r['shard_sha256']}")
            with np.load(f, allow_pickle=False) as z:
                shard_ok[sh] = {k: z[k] for k in ("images", "label", "inkmap", "tile_id")}
        z = shard_ok[sh]
        i = int(r["shard_index"])
        if str(z["tile_id"][i]) != r["tile_id"]:
            raise ValueError(f"{sh}[{i}]: tile_id {z['tile_id'][i]} != registry {r['tile_id']}")
        lab, imap = z["label"][i], z["inkmap"][i]
        bad = int(np.sum((lab == 1) & (imap < ink_min)) + np.sum((lab == 0) & (imap > blank_max))
                  + np.sum((lab != 255) & (imap > blank_max) & (imap < ink_min)))
        if bad:
            raise ValueError(f"{r['tile_id']}: {bad} px of label disagree with the DECL-D2 rule on inkmap")
        if lab.shape != (int(r["size"]),) * 2:
            raise ValueError(f"{r['tile_id']}: tile size mismatch")
        tiles[(r["segment"], int(r["canvas9_y0"]), int(r["canvas9_x0"]))] = (r, z["images"][i], lab)
    t = int(kept[0]["size"]) if kept else 128
    imgs, inks, sups, pid, seg, cyx, mx = [], [], [], [], [], [], []
    for (sg, y0, x0) in sorted(tiles):
        if mosaic > 1 and (y0 % (mosaic * t) or x0 % (mosaic * t)):
            continue
        block = [[tiles.get((sg, y0 + a * t, x0 + b * t)) for b in range(mosaic)] for a in range(mosaic)]
        if any(c is None for rr in block for c in rr):
            continue
        im = np.concatenate([np.concatenate([c[1] for c in rr], axis=2) for rr in block], axis=1)
        lab = np.concatenate([np.concatenate([c[2] for c in rr], axis=1) for rr in block], axis=0)
        imgs.append(im); inks.append((lab == 1).astype(np.uint8)); sups.append((lab != 255).astype(np.uint8))
        pid.append("+".join(c[0]["tile_id"] for rr in block for c in rr) if mosaic > 1 else block[0][0][0]["tile_id"])
        seg.append(sg); cyx.append((y0, x0))
        # per tile the 2 x 2 lattice of its corner pixel centres, row-major (the pairs0139 corner order is
        # (Y, X), (Y, X+T-1), (Y+T-1, X), (Y+T-1, X+T-1)); contam_check triangulates each as a quad
        mx.append(np.array([c[0]["xyz_corners"] for rr in block for c in rr], np.float32).reshape(-1, 2, 2, 3))
    if not imgs:
        raise ValueError(f"{root}: no patch (mosaic {mosaic})")
    meta.update(n_tiles_kept=len(tiles), n_patches=len(imgs), tile_px=t,
                mesh_kind="tilequads",
                mesh_points_note="per tile: 2 x 2 corner lattice (voxels), not a dense grid")
    reg_digest = hashlib.sha256(canonical_json(meta["registry_files_sha256"])).hexdigest()
    return Source(name=name, role=role, images=np.stack(imgs), ink=np.stack(inks), sup=np.stack(sups),
                  registry_sha256=reg_digest, patch_id=pid, segment=seg, canvas_yx=np.array(cyx, np.int64),
                  mesh_xyz=np.stack(mx), meta=meta)


def load_blockpairs(root: str, name: str, role: str = "train", allow_ids: str | None = None,
                    ink_min: int = INK_MIN, blank_max: int = BLANK_MAX) -> Source:
    """pairs-session stage-B layout, before stage C (tools/sib/pairs0814/stage_b.py; also pairs0814b):
    <root>/registry/*.jsonl rows {patch_id, segment, y0, x0, size, passed, staged, staged_sha256, ...} and
    <root>/<staged> npz per block with images uint8 (N, 21, P, P), ref9, labels {0, 1, 255}, valid, xyz (N, 17, 17, 3),
    patch_id. Only passed rows are used; the block file sha256 is checked against the row; labels are recomputed from
    ref9 by the DECL-D2 rule and checked against the stored labels."""
    import glob
    rows = []
    for f in sorted(glob.glob(os.path.join(root, "registry", "*.jsonl"))):
        rows += [json.loads(l) for l in open(f) if l.strip()]
    rows = [r for r in rows if r.get("passed") and r.get("staged")]
    meta = dict(kind="blockpairs", dir=os.path.abspath(root), label_rule=dict(ink_min=ink_min, blank_max=blank_max),
                mesh_stride_px=24, halo_px=0, mesh_kind="grid",
                registry_files_sha256={os.path.basename(f): sha256_file(f)
                                       for f in sorted(glob.glob(os.path.join(root, "registry", "*.jsonl")))})
    if allow_ids:
        keep = set(json.load(open(allow_ids)))
        meta.update(allow_ids=os.path.abspath(allow_ids), allow_ids_sha256=sha256_file(allow_ids))
        rows = [r for r in rows if r["patch_id"] in keep]
    by_file: dict[str, list] = {}
    for r in sorted(rows, key=lambda r: (r["staged"], r["patch_id"])):
        by_file.setdefault(r["staged"], []).append(r)
    imgs, inks, sups, pid, seg, cyx, mx = [], [], [], [], [], [], []
    mism = 0
    for rel, rs in by_file.items():
        f = os.path.join(root, rel)
        got = sha256_file(f)
        for r in rs:
            if r["staged_sha256"] != got:
                raise ValueError(f"{f}: sha256 {got} != registry {r['staged_sha256']} ({r['patch_id']})")
        with np.load(f, allow_pickle=False) as z:
            ids = [str(x) for x in z["patch_id"]]
            for r in rs:
                i = ids.index(r["patch_id"])
                k, sp = labels_from_target(z["ref9"][i], z["valid"][i].astype(np.uint8), ink_min, blank_max)
                mism += int(np.sum(z["labels"][i] != np.where(sp == 1, k, 255)))
                im = z["images"][i]
                if im.dtype != np.uint8 or im.shape[0] != STACK_DEPTH or im.shape[1:] != (r["size"], r["size"]):
                    raise ValueError(f"{f}[{r['patch_id']}]: image must be uint8 (21, P, P)")
                imgs.append(im); inks.append(k); sups.append(sp); pid.append(r["patch_id"]); seg.append(r["segment"])
                cyx.append((int(r["y0"]), int(r["x0"]))); mx.append(z["xyz"][i].astype(np.float32))
    if mism:
        raise ValueError(f"{root}: stored labels differ from the DECL-D2 rule on {mism} px")
    if not imgs:
        raise ValueError(f"{root}: no passed, staged patch")
    meta["n_patches"] = len(imgs)
    return Source(name=name, role=role, images=np.stack(imgs), ink=np.stack(inks), sup=np.stack(sups),
                  registry_sha256=hashlib.sha256(canonical_json(meta["registry_files_sha256"])).hexdigest(),
                  patch_id=pid, segment=seg, canvas_yx=np.array(cyx, np.int64), mesh_xyz=np.stack(mx), meta=meta)


def load_source(spec: dict) -> Source:
    kind = spec.get("kind", "pairs")
    if spec.get("allow_ids") and spec.get("allow_ids_sha256") and \
            sha256_file(spec["allow_ids"]) != spec["allow_ids_sha256"]:
        raise ValueError(f"source {spec['name']}: allow_ids file changed since the config was made")
    if kind in ("tilegrid", "tilegrid3", "tilegrid4"):
        mos = dict(tilegrid=1, tilegrid3=3, tilegrid4=4)[kind]
        src = load_tilegrid(spec["path"], spec["name"], spec.get("role", "train"), mos, spec.get("allow_ids"),
                            spec.get("ink_min", INK_MIN), spec.get("blank_max", BLANK_MAX))
    elif kind == "blockpairs":
        src = load_blockpairs(spec["path"], spec["name"], spec.get("role", "train"), spec.get("allow_ids"),
                              spec.get("ink_min", INK_MIN), spec.get("blank_max", BLANK_MAX))
    elif kind == "stagec":
        src = load_stagec(spec["path"], spec["name"], spec.get("role", "train"), spec.get("allow_ids"),
                          spec.get("ink_min", INK_MIN), spec.get("blank_max", BLANK_MAX), spec.get("data_root"))
    elif kind == "pairs":
        src = load_pairs_registry(spec["path"], spec.get("name"), spec.get("role", "train"),
                                  spec.get("ink_min", INK_MIN), spec.get("blank_max", BLANK_MAX))
    elif kind == "d3_pool":
        src = load_d3_pool(spec["path"], spec["name"], spec.get("role", "train"))
    else:
        raise ValueError(f"unknown source kind {kind!r}")
    if spec.get("sha256") and spec["sha256"] != src.registry_sha256:
        raise ValueError(f"source {src.name}: registry sha256 {src.registry_sha256} != config {spec['sha256']}")
    return src


# ---------------------------------------------------------------- synthetic data (tests and throughput only)

def _smooth_noise(rng: np.random.Generator, shape, sigma_px: float) -> np.ndarray:
    """Band-limited noise by FFT low-pass (deterministic for a given rng state)."""
    a = rng.standard_normal(shape).astype(np.float32)
    f = np.fft.rfftn(a, axes=(-2, -1))
    ky = np.fft.fftfreq(shape[-2])[:, None]
    kx = np.fft.rfftfreq(shape[-1])[None, :]
    f *= np.exp(-2 * (np.pi * sigma_px) ** 2 * (ky ** 2 + kx ** 2)).astype(np.float32)
    out = np.fft.irfftn(f, s=shape[-2:], axes=(-2, -1))
    out -= out.mean()
    out /= out.std() + 1e-6
    return out


def write_synthetic_registry(out_dir: str, n: int, size: int, seed: int, source: str = "synthetic",
                             shard_n: int = 64, mesh_stride: int = 16, halo: int = 64,
                             voxel_um: float = 9.362) -> str:
    """SYNTHETIC pair registry (random textures, random 'teacher' blobs). Never real data; for tests/throughput."""
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(seed)
    shards = []
    g = (size + 2 * halo) // mesh_stride + 1
    for s0 in range(0, n, shard_n):
        m = min(shard_n, n - s0)
        base = _smooth_noise(rng, (m, size, size), 3.0)
        zprof = np.exp(-0.5 * ((np.arange(STACK_DEPTH) - 10) / 4.0) ** 2).astype(np.float32)
        img = 110 + 40 * zprof[None, :, None, None] + 25 * base[:, None]
        img += 6 * rng.standard_normal(img.shape).astype(np.float32)
        tgt = _smooth_noise(rng, (m, size, size), 6.0)
        tgt = np.clip(128 + 90 * tgt, 0, 255).astype(np.uint8)
        img[:, 8:13] += (tgt[:, None].astype(np.float32) - 128) * 0.15      # weak ink-like coupling
        img = np.clip(img, 0, 255).astype(np.uint8)
        valid = np.ones((m, size, size), np.uint8)
        valid[:, :, : size // 16] = 0
        pid = np.array([f"{source}-{s0 + i:06d}" for i in range(m)])
        segs = np.array([f"SYN{(s0 + i) % 3}" for i in range(m)])
        cyx = np.stack([np.arange(s0, s0 + m) * size, np.zeros(m, np.int64)], 1).astype(np.int64)
        yy, xx = np.meshgrid(np.arange(g) * mesh_stride - halo, np.arange(g) * mesh_stride - halo, indexing="ij")
        mesh = np.zeros((m, g, g, 3), np.float32)
        for i in range(m):
            mesh[i, ..., 0] = xx + cyx[i, 1] + 1000.0
            mesh[i, ..., 1] = yy + cyx[i, 0] + 1000.0
            mesh[i, ..., 2] = 500.0 + 1000.0 * ((s0 + i) % 3)
        f = f"shard_{s0 // shard_n:04d}.npz"
        np.savez(os.path.join(out_dir, f), image=img, target=tgt, valid=valid, patch_id=pid, segment=segs,
                 canvas_yx=cyx, mesh_xyz=mesh)
        shards.append(dict(file=f, sha256=sha256_file(os.path.join(out_dir, f)), n=int(m)))
    reg = dict(schema=PAIRS_SCHEMA, source=source, scroll="SYNTHETIC", volume="SYNTHETIC", voxel_um=voxel_um,
               voxel_um_source="SYNTHETIC (not from any metadata.json)", stack_depth=STACK_DEPTH,
               render=dict(n=31, stack_first_slice=5), mesh_stride_px=mesh_stride, halo_px=halo, shards=shards,
               synthetic=True)
    p = os.path.join(out_dir, "registry.json")
    json.dump(reg, open(p, "w"), indent=1, sort_keys=True)
    return p


def write_synthetic_d3_pool(pd: str, n: int, seed: int) -> str:
    """SYNTHETIC pool in the tools/d3/build_pools.py format (for the D3-equivalence test)."""
    os.makedirs(pd, exist_ok=True)
    rng = np.random.default_rng(seed)
    base = _smooth_noise(rng, (n, 128, 128), 3.0)
    img = np.clip(120 + 30 * base[:, None] + 8 * rng.standard_normal((n, STACK_DEPTH, 128, 128)), 0, 255)
    img = img.astype(np.uint8)
    t = _smooth_noise(rng, (n, 128, 128), 6.0)
    ink = (t > 0.5).astype(np.uint8)
    sup = ((t > 0.5) | (t < 0.0)).astype(np.uint8)
    ink &= sup
    np.save(os.path.join(pd, "images.npy"), img)
    np.save(os.path.join(pd, "inklabels.npy"), ink)
    np.save(os.path.join(pd, "supervision.npy"), sup)
    man = dict(synthetic=True, tiles=[dict(id=f"syn{i}") for i in range(n)],
               files_sha256={f: sha256_file(os.path.join(pd, f)) for f in
                             ("images.npy", "inklabels.npy", "supervision.npy")})
    json.dump(man, open(os.path.join(pd, "manifest.json"), "w"), indent=1)
    return pd


# ---------------------------------------------------------------- patch registry (FL-09 contamination input)

def write_patch_registry(path: str, sources: list[Source], draw_counts: dict[str, np.ndarray]) -> dict:
    """Every pool patch (drawn or not: the conservative set) with its segment, canvas box and 3-D mesh points.

    Writes an npz (uncompressed, deterministic key order) and returns a summary with its sha256."""
    arrays, summary = {}, dict(schema="hercules-d2-patch-registry/1", sources=[])
    for k, s in enumerate(sources):
        p = f"s{k}_"
        arrays[p + "patch_id"] = np.array(s.patch_id, dtype="U64")
        arrays[p + "segment"] = np.array(s.segment, dtype="U64")
        arrays[p + "draws"] = np.asarray(draw_counts.get(s.name, np.zeros(len(s), np.int64)), np.int64)
        if s.canvas_yx is not None:
            arrays[p + "canvas_yx"] = s.canvas_yx.astype(np.int64)
        if s.mesh_xyz is not None:
            arrays[p + "mesh_xyz"] = s.mesh_xyz.astype(np.float32)
        summary["sources"].append(dict(index=k, name=s.name, role=s.role, n=len(s), size_px=s.size,
                                       registry_sha256=s.registry_sha256,
                                       has_mesh_xyz=s.mesh_xyz is not None,
                                       mesh_stride_px=s.meta.get("mesh_stride_px"), halo_px=s.meta.get("halo_px"),
                                       voxel_um=s.meta.get("voxel_um"),
                                       n_drawn=int(np.sum(arrays[p + "draws"] > 0))))
    with open(path, "wb") as fh:
        np.savez(fh, **arrays)
    summary["path"] = os.path.abspath(path)
    summary["sha256"] = sha256_file(path)
    summary["fl09_ready"] = all(x["has_mesh_xyz"] for x in summary["sources"])
    summary["fl09_method"] = "tools/sib/trainer/contam_check.py (CORR-RETRACE-RULE: point-to-surface, fail-closed)"
    return summary


# FL-09 / exclusion checks on a patch registry: tools/sib/trainer/contam_check.py (point-to-triangulated-surface
# distances and the fail-closed same-papyrus rule of RULES.md CORR-RETRACE-RULE). The earlier point-to-sampled-point
# helper was removed so that no clearance is computed the superseded way.
