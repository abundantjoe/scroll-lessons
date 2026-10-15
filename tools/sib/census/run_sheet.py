# Provenance: Project HERCULES | owner the owner | [id removed]
"""Tracing run sheet for one census volume (no tracing is run here).

Per z-level (3 seeds): the xy band [z_min-R-1, z_max+R+1] and the xz / yz slice
ranges covering the level's seeds (+-R+1), their bytes from the S3 listing,
the sync command (tools/sib/tracer/sync_normalgrids.py, tracer branch) and the
gated-tracer commands (build c, vc_grow_seg_from_seed, docker wrapper as in
tools/sib/tracer/synth.py vc_cmd) at 45 and 75 generations. The tracer preset
is left as <PRESET> (chosen by T0; presets reject_dist_th 1.5/2.0/2.5,
compactness on, optional space_line_weight 0.1).
"""
from __future__ import annotations

import argparse
import json
import math
import sys

import numpy as np

VC_IMG = "ghcr.io/scrollprize/vc3d-deps/linux:sha-0c371b1d472c5281b703d65517e980d945da693f"
BIN_GATED = "/work/villa-gated/volume-cartographer/build/hrc-gated-c2/bin"
MEASURED_45_S = 259.743272771  # tracer sibling, build c, 1203 dev seed ...163231537, 45 gen, 1 thread (pilot_L15_prebuild_c.jsonl)


def clip(a, b, n):
    return max(0, int(math.floor(a))), min(n - 1, int(math.ceil(b)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--sizes", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sj = json.load(open(a.seeds))
    sz = dict(np.load(a.sizes))
    Z, Y, X = len(sz["xy"]), len(sz["xz"]), len(sz["yz"])
    scroll, vid = sj["scroll"], sj["volume_id"]
    m7 = sj["m7_zarr"]
    ng_s3 = m7.replace(".zarr", ".normal-grids")
    ng_local = f"/work/ng/{scroll}"
    seeds = [s for s in sj["seeds"] if s.get("seed_xyz")]
    out = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
               scroll=scroll, volume_id=vid, m7_zarr=m7, normal_grids_s3=ng_s3, normal_grids_local=ng_local,
               status="PLAN ONLY: do not trace before the orchestrator declares T0 and the census run",
               voxel_um_from_metadata=sj["voxel_um_from_metadata"], per_gen={})
    for g in (45, 75):
        R = 20 * g
        levels = []
        union = {p: np.zeros(n, bool) for p, n in (("xy", Z), ("xz", Y), ("yz", X))}
        for k in sorted({s["level"] for s in seeds}):
            ss = [s for s in seeds if s["level"] == k]
            xs = [s["seed_xyz"][0] for s in ss]
            ys = [s["seed_xyz"][1] for s in ss]
            zs = [s["seed_xyz"][2] for s in ss]
            rr = dict(xy=clip(min(zs) - R - 1, max(zs) + R + 1, Z), xz=clip(min(ys) - R - 1, max(ys) + R + 1, Y),
                      yz=clip(min(xs) - R - 1, max(xs) + R + 1, X))
            new = 0
            by = {}
            for p, (lo, hi) in rr.items():
                by[p] = int(sz[p][lo:hi + 1].sum())
                seg = np.zeros_like(union[p])
                seg[lo:hi + 1] = True
                new += int(sz[p][seg & ~union[p]].sum())
                union[p] |= seg
            levels.append(dict(level=k, seeds=[dict(id=s["id"], seed_xyz=s["seed_xyz"]) for s in ss], ranges=rr,
                               bytes=by, bytes_total=sum(by.values()), new_bytes_if_kept=new,
                               sync_cmd=(f"/opt/hv/bin/python tools/sib/tracer/sync_normalgrids.py {ng_s3}/ {ng_local} "
                                         f"logs/sib/census/sync/{scroll}_ng_manifest.jsonl "
                                         f"xy:{rr['xy'][0]}-{rr['xy'][1]} xz:{rr['xz'][0]}-{rr['xz'][1]} yz:{rr['yz'][0]}-{rr['yz'][1]}")))
        params = {"mode": "seed", "step_size": 20, "min_area_cm": 0.2, "generations": g, "thread_limit": 1,
                  "direction_fields": [], "voxelsize": sj["voxel_um_from_metadata"], "normal_grid_path": ng_local,
                  "<PRESET>": "reject_dist_th and compactness (and space_line_weight) as declared after T0"}
        cmds = []
        for s in seeds:
            x, y, z = s["seed_xyz"]
            cmds.append(f"docker run --rm --network host --cpus 1 -e OMP_NUM_THREADS=1 -e HTTPS_PROXY=$HTTPS_PROXY "
                        f"-e https_proxy=$HTTPS_PROXY -e HOME=/work/vchome -e SSL_CERT_FILE=/root/.ccr/ca-bundle.crt "
                        f"-e CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt -v /root/.ccr/ca-bundle.crt:/root/.ccr/ca-bundle.crt:ro "
                        f"-v /home/user:/home/user -v /work:/work {VC_IMG} {BIN_GATED}/vc_grow_seg_from_seed "
                        f"--volume {m7} --target-dir /work/census_trace/{scroll}/g{g}/{s['id']} "
                        f"--params /work/census_trace/{scroll}/params_g{g}.json --seed {x} {y} {z}")
        t = MEASURED_45_S * (g / 45.0) ** 2
        out["per_gen"][str(g)] = dict(reach_vox=R, params_json=params, levels=levels,
                                      union_bytes=int(sum(sz[p][union[p]].sum() for p in union)),
                                      max_level_bytes=max(l["bytes_total"] for l in levels),
                                      time_per_seed_s_measured_scaled=t, hours_60_seeds_4_parallel=len(seeds) * t / 3600 / 4,
                                      commands=cmds)
    json.dump(out, open(a.out, "w"), indent=1)
    print(scroll, {g: dict(union_GB=round(d["union_bytes"] / 1e9, 2), max_level_GB=round(d["max_level_bytes"] / 1e9, 2),
                           h4=round(d["hours_60_seeds_4_parallel"], 2)) for g, d in out["per_gen"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
