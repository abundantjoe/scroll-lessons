# Provenance: Project HERCULES | owner the owner | [id removed]
"""Task pairs0814 stage C: verify, annotate and pack the PHerc0814 D2 pairs built by stage B. Numbers only.

1. Consistency: every registry row is unique; every PASS patch is staged exactly once in its block file, whose
   sha256 matches the registry; staged labels recount to the registry label counts; no FAIL patch is staged.
2. 3-D annotation of every PASS patch (points = the 9.362 um mesh at every 4th patch pixel, 96 x 96), under
   CORR-RETRACE-RULE (RULES.md on the work branch, 2026-09-25T19:01:33Z), fail-closed: a patch is SAME papyrus as a
   segment if EITHER (a) nearest-densified-vertex distances (5 x 5 densified, 4 vox) OR (b) point-to-triangulated-
   surface distances give >= 1000 patch points within 2 vox and count[0,1) >= 2 x count[2,3). A point MATCHES a
   segment if either distance is < 2 vox.
   * base-training papyrus: SAME vs segment 20260226000000-46527_2um_try2 (the organizer re-trace of 46527, the
     only 0814 segment in the base model's training set), the matched fraction, and the clearance = minimum
     point-to-surface distance (fail-closed lower bound dv - 2.83 vox where the surface distance was not computed;
     capped at 256 vox);
   * cross-segment duplicates: a matched point is assigned to the other segment's 384 px patch cell containing its
     nearest dense vertex; two PASS patches are linked when the patch is SAME as that segment and >= 25 % of its
     points land in the other patch; linked components = duplicate groups (same papyrus traced by more than one
     organizer segment).
3. Storage: the staged block npz files (one per 1536 px block, <= 16 patches, each < 90 MB, sha256-matched to the
   registry) are the shards; shards.json lists branch, path, sha256 and patch ids (no repacking: it would duplicate
   every patch and exceed the 1.5 GB branch budget).
4. Outputs (logs/sib/pairs0814/): pair_registry.json (every PASS patch: segment, canvas box, 2.4 um footprint,
   3-D centre / bbox, gate numbers, label counts, shard + index, base-papyrus and duplicate annotations),
   pair_registry_xyz.npz (xyz 17 x 17 grids of all PASS patches), shards.json, summary.json.
Usage: stage_c.py
"""
import collections
import subprocess
import hashlib
import json
import os
import sys
import time

import numpy as np
from scipy.spatial import cKDTree

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "src"))
from hercules.geometry.tifxyz import densify, read_tifxyz, sample_grid, valid_mask  # noqa: E402

LOGD = f"{REPO}/logs/sib/pairs0814"
WORK = "/work/sib"
BASE_SID = "20260226000000"
P, K, STEP = 384, 5, 4
PX_CM = 9.362e-4
UNION_SIDS = ("20250928235953", "20250926051122")  # handed to pairs0814b (HANDOVER.md)
PROV = "Project HERCULES | owner the owner | [id removed]"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


HALF_DIAG = 2.0 * np.sqrt(2.0)  # half diagonal of a 4 vox dense cell


def closest_on_triangles(p, a, b, c):
    """Distance from points p (n, 3) to triangles (a, b, c) (n, 3) each (Ericson, Real-Time Collision Detection 5.1.5)."""
    ab, ac, ap = b - a, c - a, p - a
    d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1)
    bp = p - b; d3 = (ab * bp).sum(1); d4 = (ac * bp).sum(1)
    cp = p - c; d5 = (ab * cp).sum(1); d6 = (ac * cp).sum(1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    q = np.empty_like(p)
    done = np.zeros(len(p), bool)

    def put(m, val):
        m = m & ~done
        q[m] = val[m]
        done[:] = done | m
    put((d1 <= 0) & (d2 <= 0), a)
    put((d3 >= 0) & (d4 <= d3), b)
    with np.errstate(divide="ignore", invalid="ignore"):
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + (d1 / (d1 - d3))[:, None] * ab)
        put((d6 >= 0) & (d5 <= d6), c)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + (d2 / (d2 - d6))[:, None] * ac)
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + ((d4 - d3) / ((d4 - d3) + (d5 - d6)))[:, None] * (c - b))
        den = 1.0 / (va + vb + vc)
        put(np.ones(len(p), bool), a + (vb * den)[:, None] * ab + (vc * den)[:, None] * ac)
    return np.linalg.norm(p - q, axis=1)


def surface_distance(q, dense, tree, rr, cc, todo, k=4, chunk=200000):
    """Point-to-triangulated-surface distance (inf where not computed) over the valid quads (2 triangles each)
    adjacent to the k nearest dense vertices of each point."""
    H, W = dense.shape[:2]
    v = valid_mask(dense)
    qv = v[:-1, :-1] & v[1:, :-1] & v[:-1, 1:] & v[1:, 1:]
    out = np.full(len(q), np.inf)
    idx = np.nonzero(todo)[0]
    D = dense.astype(np.float64)
    for s0 in range(0, len(idx), chunk):
        ii = idx[s0:s0 + chunk]
        _, kk = tree.query(q[ii], k=k, workers=3)
        best = np.full(len(ii), np.inf)
        for col in range(k):
            vr, vc_ = rr[kk[:, col]], cc[kk[:, col]]
            for dr in (-1, 0):
                for dc in (-1, 0):
                    j = vr + dr; i = vc_ + dc
                    ok = (j >= 0) & (i >= 0) & (j < H - 1) & (i < W - 1)
                    ok[ok] = qv[j[ok], i[ok]]
                    if not ok.any():
                        continue
                    jj, ii2 = j[ok], i[ok]
                    p00, p01, p10, p11 = D[jj, ii2], D[jj, ii2 + 1], D[jj + 1, ii2], D[jj + 1, ii2 + 1]
                    pq = q[ii][ok]
                    dmin = np.minimum(closest_on_triangles(pq, p00, p01, p11), closest_on_triangles(pq, p00, p11, p10))
                    best[ok] = np.minimum(best[ok], dmin)
        out[ii] = best
    return out


def main():
    segs = sorted(json.load(open(f"{LOGD}/segment_inventory.json"))["inventory"]["PHerc0814"]["segments"])
    rows = []
    for s in segs:
        sid = s.split("-", 1)[0]
        f = f"{LOGD}/registry/{sid}.jsonl"
        if os.path.exists(f):
            rows += [json.loads(l) for l in open(f)]
    for r in rows:
        r["_root"] = WORK
        r["source"] = "pairs0814"
    union = None
    if "--union" in sys.argv:
        # sibling pairs0814b's segments, read only through git objects of a recorded commit (nothing is written there)
        ref = sys.argv[sys.argv.index("--union") + 1]
        commit = subprocess.run(["git", "-C", REPO, "rev-parse", ref], capture_output=True, text=True, check=True).stdout.strip()
        uroot = f"{WORK}/union"
        union = dict(ref=ref, commit=commit, segments={})
        for sid in UNION_SIDS:
            base = f"{commit}:logs/sib/pairs0814b/registry"
            done = subprocess.run(["git", "-C", REPO, "show", f"{base}/{sid}.SEGMENT_DONE.json"], capture_output=True, text=True)
            if done.returncode != 0:
                raise SystemExit(f"pairs0814b segment {sid} has no SEGMENT_DONE at {commit}: stage C must wait")
            txt = subprocess.run(["git", "-C", REPO, "show", f"{base}/{sid}.jsonl"], capture_output=True, text=True, check=True).stdout
            urows = [json.loads(l) for l in txt.splitlines() if l.strip()]
            os.makedirs(f"{uroot}/blockpairs/{sid}", exist_ok=True)
            arch = subprocess.run(["git", "-C", REPO, "archive", commit, f"data/sib/pairs0814b/blockpairs/{sid}"], capture_output=True, check=True).stdout
            import io, tarfile
            with tarfile.open(fileobj=io.BytesIO(arch)) as tf:
                for m in tf.getmembers():
                    if m.isfile():
                        with open(f"{uroot}/blockpairs/{sid}/{os.path.basename(m.name)}", "wb") as fh:
                            fh.write(tf.extractfile(m).read())
            for r in urows:
                r["_root"] = uroot
                r["source"] = f"pairs0814b@{commit}"
            rows += urows
            union["segments"][sid] = dict(rows=len(urows), passed=sum(bool(r.get("passed")) for r in urows),
                                          segment_done=json.loads(done.stdout))
    ids = [r["patch_id"] for r in rows]
    dup_ids = [k for k, v in collections.Counter(ids).items() if v > 1]
    assert not dup_ids, f"duplicate registry rows {dup_ids[:5]}"
    def marker(s):
        f = f"{WORK}/blocks/{s.split('-', 1)[0]}/SEGMENT_DONE.json"
        return json.load(open(f)) if os.path.exists(f) else None
    handed = [s for s in segs if (marker(s) or {}).get("handed_over")]
    done_segs = [s for s in segs if marker(s) is not None and s not in handed]
    if union:
        done_segs += [s for s in handed if s.split("-", 1)[0] in union["segments"]]
    passed = [r for r in rows if r.get("passed")]
    # ---- 1. consistency of staged data
    staged = {}
    problems = []
    for r in passed:
        staged.setdefault(r["staged"], []).append(r)
    for rel, rs in staged.items():
        path = f"{rs[0]['_root']}/{rel}"
        if sha256(path) != rs[0]["staged_sha256"]:
            problems.append(f"sha mismatch {rel}")
            continue
        z = np.load(path)
        pid = list(z["patch_id"])
        if sorted(pid) != sorted(r["patch_id"] for r in rs):
            problems.append(f"patch ids differ {rel}")
        for r in rs:
            i = pid.index(r["patch_id"])
            lab = z["labels"][i]
            if int((lab == 1).sum()) != r["n_ink"] or int((lab == 0).sum()) != r["n_blank"]:
                problems.append(f"label count {r['patch_id']}")
            if z["images"][i].shape != (21, P, P) or z["images"][i].dtype != np.uint8:
                problems.append(f"image shape {r['patch_id']}")
    staged_fail = [r["patch_id"] for r in rows if r.get("staged") and not r.get("passed")]
    problems += [f"staged but failed {p}" for p in staged_fail]
    # ---- 2. 3-D annotation (CORR-RETRACE-RULE: fail-closed vertex OR point-to-surface form)
    meshes = {}
    for s in segs:
        sid = s.split("-", 1)[0]
        if os.path.exists(f"{WORK}/seg/{sid}/mesh9/x.tif"):
            meshes[sid] = read_tifxyz(f"{WORK}/seg/{sid}/mesh9")
    qpts, qown = [], []
    off = np.arange(0, P, STEP) + STEP // 2 + 0.5  # pixel centres (P + 0.5) of every 4th pixel
    for i, r in enumerate(passed):
        m = meshes[r["patch_id"].split("_")[0]]
        g = sample_grid(m.points, ((r["y0"] + off) / 20.0)[:, None], ((r["x0"] + off) / 20.0)[None, :]).reshape(-1, 3)
        ok = g[:, 0] != -1
        qpts.append(g[ok]); qown.append(np.full(ok.sum(), i))
    qpts = np.concatenate(qpts) if qpts else np.zeros((0, 3)); qown = np.concatenate(qown) if qown else np.zeros(0, int)
    npts = np.bincount(qown, minlength=len(passed)).astype(float)
    NP = len(passed)
    base_same = np.zeros(NP, bool); base_frac = np.zeros(NP); base_min = np.full(NP, np.inf)
    seg_frac = collections.defaultdict(dict)
    seg_same = collections.defaultdict(dict)
    link = collections.Counter()
    cell_of = {r["patch_id"]: j for j, r in enumerate(passed)}
    own_sid = np.array([passed[j]["patch_id"].split("_")[0] for j in qown]) if len(qown) else np.zeros(0, str)
    for sidB, mB in meshes.items():
        dense = densify(mB.points, K)
        v = valid_mask(dense)
        rr, cc = np.nonzero(v)
        pts = dense[rr, cc].astype(np.float64)
        lo, hi = pts.min(0) - 260, pts.max(0) + 260
        sel = np.nonzero(np.all((qpts >= lo) & (qpts <= hi), 1) & (own_sid != sidB))[0]
        if sel.size == 0:
            continue
        tree = cKDTree(pts)
        dv, kv = tree.query(qpts[sel], k=1, distance_upper_bound=256.0, workers=3)
        ds = surface_distance(qpts[sel], dense, tree, rr, cc, np.isfinite(dv) & (dv <= 6.0))
        if sidB == BASE_SID:
            # clearance: exact surface distance where computed, else the fail-closed lower bound dv - 2.83
            clr = np.where(np.isfinite(ds), ds, dv - HALF_DIAG)
            np.minimum.at(base_min, qown[sel], clr)
        own = qown[sel]
        for form, dd in (("a", dv), ("b", ds)):
            c0 = np.bincount(own[dd < 1.0], minlength=NP)
            c1 = np.bincount(own[(dd >= 1.0) & (dd < 2.0)], minlength=NP)
            c2 = np.bincount(own[(dd >= 2.0) & (dd < 3.0)], minlength=NP)
            same = ((c0 + c1) >= 1000) & (c0 >= 2 * c2)
            for j in np.nonzero(same)[0]:
                seg_same[j][sidB] = seg_same[j].get(sidB, "") + form
        matched = (dv < 2.0) | (ds < 2.0)
        cnt = np.bincount(own[matched], minlength=NP)
        for j in np.nonzero(cnt)[0]:
            seg_frac[j][sidB] = float(cnt[j] / npts[j])
        if sidB == BASE_SID:
            base_frac = cnt / np.maximum(npts, 1)
            base_same = np.array([BASE_SID in seg_same[j] for j in range(NP)])
        # matched point -> canvas pixel of its nearest dense vertex -> 384 px patch cell of segment B
        km = kv[matched]
        py = rr[km] / K * 20.0 - 0.5; px = cc[km] / K * 20.0 - 0.5
        cy = (np.floor(py / P) * P).astype(int); cx = (np.floor(px / P) * P).astype(int)
        for a_, yy, xx in zip(own[matched], cy, cx):
            b_ = cell_of.get(f"{sidB}_{yy}_{xx}")
            if b_ is not None and sidB in seg_same[int(a_)]:
                link[(int(a_), int(b_))] += 1
    for j, r in enumerate(passed):
        if r["patch_id"].split("_")[0] == BASE_SID:
            base_same[j], base_frac[j], base_min[j] = True, 1.0, 0.0
    parent = list(range(len(passed)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    edges = []
    for (a, b), c in link.items():
        if c / npts[a] >= 0.25:
            edges.append((a, b, c / npts[a]))
            parent[find(a)] = find(b)
    groups = collections.defaultdict(list)
    for j in range(len(passed)):
        groups[find(j)].append(j)
    gid = {}
    for n, (root, mem) in enumerate(sorted(groups.items(), key=lambda kv: min(kv[1]))):
        for j in mem:
            gid[j] = n
    # ---- 3. storage: by default the sha-verified staged block npz files ARE the shards (each < 90 MB, already
    # pushed: logs/sib/pairs0814/blockpairs on this branch, data/sib/pairs0814b/blockpairs on pairs0814b). Repacking
    # (--pack) would store every patch twice and exceed the 1.5 GB branch budget.
    order = sorted(range(len(passed)), key=lambda j: (passed[j]["patch_id"].split("_")[0], passed[j]["staged"],
                                                      passed[j]["y0"], passed[j]["x0"]))
    cache = {}

    def item(j):
        rel = passed[j]["staged"]
        if rel not in cache:
            cache.clear()
            cache[rel] = np.load(f"{passed[j]['_root']}/{rel}")
        z = cache[rel]
        i = list(z["patch_id"]).index(passed[j]["patch_id"])
        return {k: z[k][i] for k in ("images", "ref9", "labels", "valid", "xyz")}, i
    shards = []
    loc = {}
    by_file = collections.defaultdict(list)
    for j in order:
        r = passed[j]
        if r["source"] == "pairs0814":
            path = f"logs/sib/pairs0814/{r['staged']}"; branch = "claude/gifted-bell-gavnl5-sib-pairs0814"
        else:
            path = f"data/sib/pairs0814b/{r['staged']}"; branch = f"claude/gifted-bell-gavnl5-sib-pairs0814b@{union['commit']}"
        by_file[(branch, path)].append(j)
    for (branch, path), js in by_file.items():
        full = f"{passed[js[0]]['_root']}/{passed[js[0]]['staged']}"
        shards.append(dict(shard=path, branch=branch, n=len(js), bytes=os.path.getsize(full), sha256=sha256(full),
                           patch_ids=[passed[j]["patch_id"] for j in js]))
        for j in js:
            loc[j] = (path, item(j)[1])
    # ---- 4. outputs
    reg = []
    xyz_all = np.zeros((len(passed), 17, 17, 3), np.float32)
    for j, r in enumerate(passed):
        xyz_all[j] = item(j)[0]["xyz"]
        reg.append(dict(
            patch_id=r["patch_id"], segment=r["segment"], source=r["source"], y0=r["y0"], x0=r["x0"], size=P,
            footprint24_xywh=r["footprint24_xywh"], centre_xyz_vox9=r["centre_xyz_vox9"], bbox_xyz_vox9=r["bbox_xyz_vox9"],
            ncc0=r["ncc0"], ncc0_slab53_55=r["ncc0_slab53_55"], n_aligned=r["n_aligned"],
            window_shift_median_dy_dx=[float(np.median([w["dy"] for w in r["windows"] if w["dy"] is not None])),
                                       float(np.median([w["dx"] for w in r["windows"] if w["dx"] is not None]))],
            control_ncc_shift5_max=max(r["control_ncc_shift5"].values()) if r.get("control_ncc_shift5") else None,
            n_ink=r["n_ink"], n_blank=r["n_blank"], n_ignore=r["n_ignore"], valid_frac=r["valid_frac"],
            shard=loc[j][0], shard_branch=[x["branch"] for x in shards if x["shard"] == loc[j][0]][0], shard_index=loc[j][1],
            base_same_papyrus_46527=bool(base_same[j]),
            base_papyrus_frac_46527=float(base_frac[j]),
            base_min_dist_vox=(float(base_min[j]) if np.isfinite(base_min[j]) else ">=256"),
            same_papyrus_frac_by_segment={k: round(v, 4) for k, v in sorted(seg_frac[j].items())},
            same_papyrus_rule_by_segment={k: v for k, v in sorted(seg_same[j].items())},
            duplicate_group=gid[j], duplicate_group_size=len(groups[find(j)])))
    np.savez_compressed(f"{LOGD}/pair_registry_xyz.npz", xyz=xyz_all, patch_id=np.array([r["patch_id"] for r in passed]))
    q = lambda a, p: float(np.percentile(a, p)) if len(a) else None
    gated = [r for r in rows if r.get("status") == "GATED"]
    n0 = np.array([r["ncc0"] for r in gated if r["ncc0"] is not None and np.isfinite(r["ncc0"])])
    ctl = np.array([max(r["control_ncc_shift5"].values()) for r in gated if r.get("control_ncc_shift5")])
    per_seg = {}
    for s in segs:
        sid = s.split("-", 1)[0]
        rs = [r for r in rows if r["patch_id"].startswith(sid + "_")]
        g = [r for r in rs if r.get("status") == "GATED"]
        per_seg[s] = dict(candidates=len(rs), gated=len(g), render_failed=len(rs) - len(g),
                          passed=sum(bool(r.get("passed")) for r in rs),
                          fail_ncc_only=sum(1 for r in g if not r["passed"] and r["n_aligned"] >= 7),
                          fail_align_only=sum(1 for r in g if not r["passed"] and r["ncc0"] >= 0.8),
                          fail_both=sum(1 for r in g if not r["passed"] and r["ncc0"] < 0.8 and r["n_aligned"] < 7),
                          ink_px=sum(r["n_ink"] for r in rs if r.get("passed")),
                          blank_px=sum(r["n_blank"] for r in rs if r.get("passed")),
                          ignore_px=sum(r["n_ignore"] for r in rs if r.get("passed")),
                          segment_complete=s in done_segs, handed_over=s in handed)
    base_any = [x for x in reg if x["base_same_papyrus_46527"] or x["base_papyrus_frac_46527"] > 0]
    uniq = len({x["duplicate_group"] for x in reg})
    uniq_nobase = len({x["duplicate_group"] for x in reg if x["base_papyrus_frac_46527"] == 0})
    grp_base = {x["duplicate_group"] for x in base_any}
    clean = [x for x in reg if x["duplicate_group"] not in grp_base]
    summ = dict(
        provenance=PROV, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), consistency_problems=problems,
        segments_complete=f"{len(done_segs)}/{len(segs)}", segments_handed_over=handed, union=union, candidates=len(rows), gated=len(gated), passed=len(passed),
        pass_rate=len(passed) / max(1, len(gated)), per_segment=per_seg,
        ncc0=dict(n=len(n0), p5=q(n0, 5), p25=q(n0, 25), median=q(n0, 50), p75=q(n0, 75), p95=q(n0, 95),
                  frac_ge_0p8=float((n0 >= 0.8).mean()) if len(n0) else None),
        control_ncc_shift5_max=dict(median=q(ctl, 50), p95=q(ctl, 95), max=float(ctl.max()) if len(ctl) else None,
                                    frac_ge_0p8=float((ctl >= 0.8).mean()) if len(ctl) else None),
        n_aligned_hist={str(k): sum(1 for r in gated if r["n_aligned"] == k) for k in range(10)},
        labels_passed=dict(ink_px=sum(x["n_ink"] for x in reg), blank_px=sum(x["n_blank"] for x in reg),
                           ignore_px=sum(x["n_ignore"] for x in reg),
                           ink_cm2=sum(x["n_ink"] for x in reg) * PX_CM ** 2,
                           blank_cm2=sum(x["n_blank"] for x in reg) * PX_CM ** 2,
                           area_cm2=len(reg) * (P * PX_CM) ** 2),
        base_papyrus=dict(rule="CORR-RETRACE-RULE fail-closed (vertex OR point-to-surface bins, >= 1000 points within 2 vox, c0 >= 2 c2) vs 20260226000000-46527_2um_try2",
                          passed_same_papyrus_46527_by_rule=sum(1 for x in reg if x["base_same_papyrus_46527"]),
                          passed_on_46527_itself=sum(1 for x in reg if x["segment"].startswith(BASE_SID)),
                          passed_with_any_base_point=len(base_any),
                          passed_within_128vox_of_46527=sum(1 for x in reg if isinstance(x["base_min_dist_vox"], float) and x["base_min_dist_vox"] < 128),
                          passed_within_64vox_of_46527=sum(1 for x in reg if isinstance(x["base_min_dist_vox"], float) and x["base_min_dist_vox"] < 64)),
        duplicates=dict(groups=uniq, groups_without_base_points=uniq_nobase, passed_patches_in_multi_groups=sum(
            1 for x in reg if x["duplicate_group_size"] > 1), edges=len(edges),
            clean_patches_not_in_any_group_touching_46527=len(clean),
            clean_groups=len({x["duplicate_group"] for x in clean})),
        shards=dict(n=len(shards), bytes=sum(s["bytes"] for s in shards), max_bytes=max((s["bytes"] for s in shards), default=0)),
    )
    json.dump(dict(provenance=PROV, utc=summ["utc"], patches=reg), open(f"{LOGD}/pair_registry.json", "w"), indent=1)
    json.dump(dict(provenance=PROV, shards=shards), open(f"{LOGD}/shards.json", "w"), indent=1)
    json.dump(summ, open(f"{LOGD}/summary.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "per_segment"}, indent=1))


if __name__ == "__main__":
    main()
