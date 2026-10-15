# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 Stage 1a/1b (DECL-D3-A1 items 2-3): render and store the fold-A and replay tile pools. Numbers only.

Storage format (both pools): images.npy uint8 (N, 21, 128, 128) = render slices 5..25 of an official
vc_render_tifxyz -n 31 --flip-normals render (C2-NT forward window 7..23 = stack indices 2..18; +-2 jitter fits);
inklabels.npy uint8 (N, 128, 128) in {0, 1}; supervision.npy uint8 (N, 128, 128) in {0, 1} (0 = ignored);
manifest.json with the tile list, per-tile hashes and label pixel counts, and file sha256s.

fa:     tiles = /work/d3/work/fa_tiles.json PRIMARY text tiles (306; count-B exclusion) whose every mesh-valid pixel
        is >= 144 vox (3-D) from any J mesh point (the '>= 144 vox crops' of item 2) -> each tile rendered as its own
        128 x 128 crop (crop = tile, so no rendered crop contains a pixel < 144 vox from J). 0841 volume
        20250821151531 at 9.366 um. Labels from bank ref9 on the same canvas: ink = ref9 >= 150, blank = ref9 <= 100,
        rest and ~valid9 ignored.
replay: PHerc0139 w035, w039, w040, w041, w044, official native 9.362 um label set 20260918 (downloaded to
        /work/d3/data/s3). Candidates: 128 px tiles on the official base-training patch grid (stride 32) with
        >= 90 % supervised pixels. Draw: quota 3000 / 5 = 600 per segment, a segment with fewer candidates gives all
        of them and the shortfall is re-split equally over segments with spare candidates (repeat); draws by
        numpy default_rng(20260925). Renders: one crop per connected component of the selected tiles' union (bounding
        box), 0139 volume 20250728140407 at 9.362 um. Labels: ink = inklabels > 0 inside supervision; blank =
        supervision without ink; unsupervised ignored.
Every render is ledgered in /work/d3/work/ledger.tsv (host, cpu, command, start, end, exit, output tree sha256).
Usage: build_pools.py fa|replay|cleanup_fa|cleanup_replay
v2 (after the ~10:20Z restart): renders via /work/d3/scripts/vc_d3.sh (proxy from $HTTPS_PROXY); a crop that fails
twice (ledger count) is dropped and recorded; pool < 280 stops (INFEASIBLE); cleanup_* deletes zarr renders after
the pool is stored. The replay pool was built by v1 (build_pools_v1.py, sha256 a08c5b49...)."""
import os, sys, json, time, hashlib, subprocess, datetime, socket
os.environ.setdefault("OMP_NUM_THREADS", "3")
import numpy as np, zarr

D3 = "/work/d3"
WK = f"{D3}/work"
LEDGER = f"{WK}/ledger.tsv"
SEED = 20260925
Z0, Z1 = 5, 26                      # stored render slices 5..25
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
CPU = "cpus=3/%d %s" % (os.cpu_count(), next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo")
                                                 if l.startswith("model name")), "cpu"))
HOST = socket.gethostname()
VOL41 = "s3://vesuvius-challenge-open-data/PHerc0841/volumes/20250821151531-9.366um-1.2m-113keV-masked.zarr/"
VOL39 = "s3://vesuvius-challenge-open-data/PHerc0139/volumes/20250728140407-9.362um-1.2m-113keV-masked.zarr/"
BANK = "/work/bank/0841"
S39 = f"{D3}/data/s3/PHerc0139/segments"
REPLAY_SEGS = ["20260317000000-w035_2026031718", "20260302000000-w039_2026030210", "20250831000000-w040_2025083102",
               "20260108000000-w041_2026010816", "20260115000000-w044_2026011522"]


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def tree_sha256(root):
    rows = []
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            rows.append(f"{sha256(p)}  ./{os.path.relpath(p, root)}\n")
    rows.sort(key=lambda r: r.split("  ", 1)[1])
    return hashlib.sha256("".join(rows).encode()).hexdigest()


def ledger(cmd, start, end, rc, out_sha):
    new = not os.path.exists(LEDGER)
    with open(LEDGER, "a", encoding="utf-8") as f:
        if new:
            f.write("host\tcpu\tcommand\tstart_utc\tend_utc\texit\toutput_sha256\n")
        f.write("\t".join([HOST, CPU, cmd.replace("\t", " ").replace("\n", " "), start, end, str(rc), out_sha]) + "\n")


VC = "/work/d3/scripts/vc_d3.sh"     # = /work/bin/vc with the proxy taken from $HTTPS_PROXY (v2)


def prior_failures(out):
    if not os.path.exists(LEDGER):
        return 0
    n = 0
    for line in open(LEDGER, encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if len(f) == 7 and f[5] not in ("0", "exit") and f"--zarr-output {out}" in f[2] and f[2].rstrip().endswith(out):
            n += 1
    return n


def render(vol, vox, seg_tifxyz, x, y, w, h, out):
    """official vc_render_tifxyz -n 31 --flip-normals crop; returns ((31, h, w) uint8 array, tree sha), or
    (None, None) once the crop has failed twice (ledger rows count; DECL-D3-A2 item 1)."""
    done = f"{out}.done.json"
    if os.path.exists(done):
        d = json.load(open(done))
        return np.asarray(zarr.open(f"{out}/0", mode="r")[:]), d["tree_sha256"]
    while prior_failures(out) < 2:
        res = _render_once(vol, vox, seg_tifxyz, x, y, w, h, out)
        if res is not None:
            return res
    return None, None


def _render_once(vol, vox, seg_tifxyz, x, y, w, h, out):
    done = f"{out}.done.json"
    if os.path.exists(out):
        subprocess.run(["rm", "-rf", out], check=True)
    cmd = ["vc_render_tifxyz", "-v", vol, "--remote-url", vol, "--segmentation", seg_tifxyz, "--scale", "1",
           "--group-idx", "0", "--num-slices", "31", "--slice-step", "1", "--voxel-size", vox,
           "--voxel-unit", "micrometer", "--flip-normals", "--crop-x", str(x), "--crop-y", str(y),
           "--crop-width", str(w), "--crop-height", str(h), "--cache-gb", "2", "--zarr-output", out]
    env = dict(os.environ, VC_CPUS="3", OMP_NUM_THREADS="3")
    start = utc()
    with open(f"{out}.log", "w") as lf:
        pr = subprocess.run([VC, *cmd], stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=WK)
    end = utc()
    sha = tree_sha256(out) if pr.returncode == 0 and os.path.exists(out) else "missing"
    ledger(f"VC_CPUS=3 OMP_NUM_THREADS=3 {VC} " + " ".join(cmd), start, end, pr.returncode, sha)
    if pr.returncode != 0:
        print(f"render failed rc={pr.returncode}: {out}", flush=True)
        os.replace(f"{out}.log", f"{out}.fail{prior_failures(out)}.log")
        return None
    a = np.asarray(zarr.open(f"{out}/0", mode="r")[:])
    assert a.shape == (31, h, w) and a.dtype == np.uint8, (a.shape, a.dtype)
    json.dump(dict(tree_sha256=sha, start=start, end=end, command=" ".join(cmd)), open(done, "w"))
    return a, sha


def write_pool(name, images, ink, sup, tiles, meta):
    pd = f"{D3}/pool_{name}"
    os.makedirs(pd, exist_ok=True)
    np.save(f"{pd}/images.npy", images)
    np.save(f"{pd}/inklabels.npy", ink)
    np.save(f"{pd}/supervision.npy", sup)
    files = {f: sha256(f"{pd}/{f}") for f in ("images.npy", "inklabels.npy", "supervision.npy")}
    man = dict(provenance=PROV, pool=name, generated_utc=utc(), n_tiles=int(len(tiles)),
               storage=dict(images="uint8 (N, 21, 128, 128) = render slices 5..25 of -n 31 (stack index 2..18 = "
                                   "slices 7..23 = C2-NT forward window)",
                            inklabels="uint8 (N, 128, 128) {0,1}", supervision="uint8 (N, 128, 128) {0,1}, 0 = ignored",
                            shapes=[list(images.shape), list(ink.shape), list(sup.shape)]),
               label_px=dict(ink=int(ink.sum()), blank=int(((sup > 0) & (ink == 0)).sum()),
                             ignored=int((sup == 0).sum()), total=int(sup.size)),
               files_sha256=files, meta=meta, tiles=tiles,
               script=dict(path=os.path.abspath(__file__), sha256=sha256(os.path.abspath(__file__))))
    json.dump(man, open(f"{pd}/manifest.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in man.items() if k not in ("tiles",)}, indent=1), flush=True)
    return man


def build_fa():
    fl = json.load(open(f"{WK}/fa_tiles.json"))
    sel = [t for t in fl["tiles"] if t["ge144"]]
    dropped = [t for t in fl["tiles"] if not t["ge144"]]
    rd = f"{WK}/render_fa"
    os.makedirs(rd, exist_ok=True)
    N = len(sel)
    images = np.zeros((N, Z1 - Z0, 128, 128), np.uint8)
    ink = np.zeros((N, 128, 128), np.uint8); sup = np.zeros((N, 128, 128), np.uint8)
    tiles = []
    cache = {}
    failed, keep = [], np.ones(N, bool)
    t0 = time.time()
    for i, t in enumerate(sel):
        s, y, x = t["segment"], t["y0"], t["x0"]
        short = s.split("-")[0][-6:]        # 213127 / 214732 / 022814 (unique per segment)
        ts = s.split("-")[0]
        mesh = f"{BANK}/s3/PHerc0841/segments/{s}/mesh/{ts}-on-20250821151531-9.366um.tifxyz"
        out = f"{rd}/{short}_y{y}_x{x}.zarr"
        a, tsha = render(VOL41, "9.366", mesh, x, y, 128, 128, out)
        if a is None:                        # failed twice: dropped and recorded
            failed.append(dict(segment=s, y0=y, x0=x, render=out, failures=prior_failures(out)))
            keep[i] = False
            continue
        images[i] = a[Z0:Z1]
        if s not in cache:
            cache.clear()
            cache[s] = (np.load(f"{BANK}/canvas9/{s}/ref9.npy", mmap_mode="r"),
                        np.load(f"{BANK}/canvas9/{s}/valid9.npy", mmap_mode="r"))
        ref, val = cache[s]
        r = np.asarray(ref[y:y + 128, x:x + 128], np.float32); v = np.asarray(val[y:y + 128, x:x + 128]).astype(bool)
        k = (r >= 150) & v; b = (r <= 100) & v
        ink[i] = k; sup[i] = k | b
        tiles.append(dict(idx=i, segment=s, y0=y, x0=x, render=out, render_tree_sha256=tsha,
                          image_sha256=hashlib.sha256(images[i].tobytes()).hexdigest(),
                          label_sha256=hashlib.sha256(ink[i].tobytes() + sup[i].tobytes()).hexdigest(),
                          ink_px=int(k.sum()), blank_px=int(b.sum()), ignored_px=int(128 * 128 - (k | b).sum()),
                          render_valid_px=int((images[i] > 0).any(0).sum()),
                          min_3d_dist_to_J_vox=t["min_3d_dist_vox"], text_px=t["text_px"], valid_px=t["valid_px"]))
        if i % 25 == 0:
            print(f"fa {i}/{N} t={time.time()-t0:.0f}s", flush=True)
    if failed:                                # compact: drop tiles whose render failed twice
        images, ink, sup = images[keep], ink[keep], sup[keep]
        for j, t in enumerate(tiles):
            t["idx"] = j
    if len(tiles) < 280:
        raise SystemExit(f"fold-A pool {len(tiles)} < 280: D3 INFEASIBLE on current material (DECL-D3-A2 item 1)")
    meta = dict(source="DECL-D3-A1 item 2 / DECL-D3-A2 item 1; /work/d3/work/fa_tiles.json (sha256 %s)" % sha256(f"{WK}/fa_tiles.json"),
                render_failed_twice_dropped=failed,
                n_primary_text=fl["n_text"], n_ge144=N, n_kept=len(tiles), n_dropped_lt144=len(dropped),
                dropped=[dict(segment=t["segment"], y0=t["y0"], x0=t["x0"], min_3d_dist_vox=t["min_3d_dist_vox"])
                         for t in dropped],
                per_segment_kept={s: sum(1 for t in tiles if t["segment"] == s) for s in fl["per_segment"]},
                volume=VOL41, voxel_size_um=9.366, render="per-tile 128 x 128 crop, -n 31, --flip-normals",
                labels="bank canvas9 ref9: ink >= 150, blank <= 100, rest and ~valid9 ignored",
                ref9_sha256={s: sha256(f"{BANK}/canvas9/{s}/ref9.npy") for s in fl["per_segment"]},
                valid9_sha256={s: sha256(f"{BANK}/canvas9/{s}/valid9.npy") for s in fl["per_segment"]},
                seconds=round(time.time() - t0, 1))
    write_pool("fa", images, ink, sup, tiles, meta)


def sat(m):
    a = np.zeros((m.shape[0] + 1, m.shape[1] + 1), np.int64)
    a[1:, 1:] = m.astype(np.int64).cumsum(0).cumsum(1)
    return a


def build_replay():
    from scipy import ndimage
    cands, labs = {}, {}
    for s in REPLAY_SEGS:
        L = f"{S39}/{s}/ink-labels/9.362um-volume-20250728140407/20260918"
        il = np.asarray(zarr.open(f"{L}/inklabels.zarr", mode="r")["0"][:]) > 0
        su = np.asarray(zarr.open(f"{L}/supervision.zarr", mode="r")["0"][:]) > 0
        labs[s] = (il, su)
        S = sat(su); H, W = su.shape
        ys = np.arange(0, H - 128 + 1, 32); xs = np.arange(0, W - 128 + 1, 32)
        n = S[ys[:, None] + 128, xs[None, :] + 128] - S[ys[:, None], xs[None, :] + 128] \
            - S[ys[:, None] + 128, xs[None, :]] + S[ys[:, None], xs[None, :]]
        cands[s] = [(int(ys[a]), int(xs[b])) for a, b in zip(*np.nonzero(10 * n >= 9 * 128 * 128))]
    # quota draw: 3000 / 5, shortfall re-split equally over segments with spare candidates
    rng = np.random.default_rng(SEED)
    quota = {s: 0 for s in REPLAY_SEGS}
    remaining = 3000
    while remaining > 0:
        spare = [s for s in REPLAY_SEGS if quota[s] < len(cands[s])]
        if not spare:
            break
        share, extra = divmod(remaining, len(spare))
        given = 0
        for j, s in enumerate(spare):
            add = min(share + (1 if j < extra else 0), len(cands[s]) - quota[s])
            quota[s] += add; given += add
        remaining -= given
        if given == 0:
            break
    picks = {}
    for s in REPLAY_SEGS:
        order = rng.permutation(len(cands[s]))[:quota[s]]
        picks[s] = sorted(cands[s][k] for k in order)
    rd = f"{WK}/render_replay"
    os.makedirs(rd, exist_ok=True)
    N = sum(len(v) for v in picks.values())
    images = np.zeros((N, Z1 - Z0, 128, 128), np.uint8)
    ink = np.zeros((N, 128, 128), np.uint8); sup = np.zeros((N, 128, 128), np.uint8)
    tiles, renders = [], []
    t0 = time.time()
    i = 0
    for s in REPLAY_SEGS:
        il, su = labs[s]
        ts = s.split("-")[0]; short = s.split("-")[1][:4]
        mesh = f"{S39}/{s}/mesh/{ts}-on-20250728140407-9.362um.tifxyz"
        u = np.zeros(su.shape, bool)
        for (y, x) in picks[s]:
            u[y:y + 128, x:x + 128] = True
        lab, nc = ndimage.label(u)
        objs = ndimage.find_objects(lab)
        comp_of = {}
        for (y, x) in picks[s]:
            comp_of[(y, x)] = int(lab[y, x])
        for c, sl in enumerate(objs, start=1):
            ry0, ry1, rx0, rx1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
            out = f"{rd}/{short}_c{c:02d}_y{ry0}_x{rx0}_{ry1-ry0}x{rx1-rx0}.zarr"
            a, tsha = render(VOL39, "9.362", mesh, rx0, ry0, rx1 - rx0, ry1 - ry0, out)
            renders.append(dict(segment=s, component=c, y0=ry0, x0=rx0, h=ry1 - ry0, w=rx1 - rx0, render=out,
                                render_tree_sha256=tsha))
            for (y, x) in picks[s]:
                if comp_of[(y, x)] != c:
                    continue
                images[i] = a[Z0:Z1, y - ry0:y - ry0 + 128, x - rx0:x - rx0 + 128]
                sp = su[y:y + 128, x:x + 128]; k = il[y:y + 128, x:x + 128] & sp
                ink[i] = k; sup[i] = sp
                tiles.append(dict(idx=i, segment=s, y0=y, x0=x, render=out, render_tree_sha256=tsha,
                                  image_sha256=hashlib.sha256(images[i].tobytes()).hexdigest(),
                                  label_sha256=hashlib.sha256(ink[i].tobytes() + sup[i].tobytes()).hexdigest(),
                                  ink_px=int(k.sum()), blank_px=int((sp & ~k).sum()), ignored_px=int((~sp).sum()),
                                  render_valid_px=int((images[i] > 0).any(0).sum())))
                i += 1
            print(f"replay {s[15:19]} comp {c}/{nc} tiles {i}/{N} t={time.time()-t0:.0f}s", flush=True)
    assert i == N
    cy0, cx0, cn = 2816, 2816, 2136     # D1 canary organizer window on w044 (reported, not excluded)
    can = sum(1 for t in tiles if t["segment"] == REPLAY_SEGS[4] and t["y0"] < cy0 + cn and t["y0"] + 128 > cy0
              and t["x0"] < cx0 + cn and t["x0"] + 128 > cx0)
    meta = dict(source="DECL-D3-A1 item 3", seed=SEED, grid_stride=32, min_supervised_frac=0.9,
                candidates={s: len(cands[s]) for s in REPLAY_SEGS}, quota=quota,
                picked={s: len(picks[s]) for s in REPLAY_SEGS}, volume=VOL39, voxel_size_um=9.362,
                render="one crop per connected component of the selected tiles' union, -n 31, --flip-normals",
                renders=renders,
                labels="native 9.362 um label set 20260918: ink = inklabels > 0 inside supervision; blank = supervision "
                       "without ink; unsupervised ignored",
                label_files_sha256={s: {f: sha256(os.path.join(dp, f2)) for dp, _, fs in
                                        os.walk(f"{S39}/{s}/ink-labels/9.362um-volume-20250728140407/20260918")
                                        for f2 in fs for f in [os.path.relpath(os.path.join(dp, f2), S39)]}
                                    for s in REPLAY_SEGS},
                tiles_overlapping_D1_canary_window_w044=can, seconds=round(time.time() - t0, 1))
    write_pool("replay", images, ink, sup, tiles, meta)


def cleanup(name):
    """delete the intermediate zarr renders once the pool holds their tiles (tree sha256s stay in manifest + ledger)."""
    man = json.load(open(f"{D3}/pool_{name}/manifest.json"))
    for f, h in man["files_sha256"].items():
        assert sha256(f"{D3}/pool_{name}/{f}") == h
    rd = f"{WK}/render_{name}"
    n = sum(1 for e in os.listdir(rd) if e.endswith(".zarr"))
    subprocess.run(f"rm -rf {rd}/*.zarr", shell=True, check=True)
    print(f"cleanup {name}: deleted {n} zarr renders in {rd} (kept .done.json / .log files)", flush=True)


if __name__ == "__main__":
    {"fa": build_fa, "replay": build_replay, "cleanup_fa": lambda: cleanup("fa"),
     "cleanup_replay": lambda: cleanup("replay")}[sys.argv[1]]()
