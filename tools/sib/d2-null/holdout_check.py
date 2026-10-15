# Provenance: Project HERCULES | owner the owner | [id removed]
"""d2-null hold-out check against logs/sib/trainer/PAIR_FREEZE_SPEC.md (trainer branch 08d7e42), SYNTHETIC only.
Numbers and hashes only; no image is written as an image or opened.

1. Writes a synthetic stage-C tree (the spec's preferred pairs0814u layout: shards.json + pair_registry.json +
   staged block npz files under a data_root) with N 384 px patches, and a hold-out list (some pool ids plus one id
   that is not in the pool).
2. Runs the unchanged trainer-head pair_freeze.py --verify on it (subprocess), producing pair_freeze.json and the
   allowlist.
3. make-config (unchanged trainer-head d2_train.py) for NULL and P384, seed 1, with --allow-ids / --data-root /
   --hash-sources, as the spec's step 4 says.
4. Builds both Trainers and checks: the loaded pool equals the allowlist; no held-out id is loaded; the NULL
   derangement acts on the allowed patches only (0 fixed points, labels = fresh allowed labels permuted, no label
   array equal to a held-out patch's); every drawn patch over --batches batch draws is allowed; P384 and NULL draw
   identical images and (patch, z, rotation) sequences with different labels (pair_check.py, one process per arm);
   an edited allowlist is refused.
Usage: holdout_check.py --work DIR --out OUT.json [--n 24] [--batches 12]"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TH = os.path.join(HERE, "trainer_head")
sys.path.insert(0, TH)
PY = sys.executable


def h(b):
    return hashlib.sha256(b).hexdigest()


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"FAILED {cmd}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r.stdout


def write_stagec(tree, n, seed):
    import numpy as np
    import d2_data
    rng = np.random.default_rng(seed)
    rel_dir = "logs/sib/pairs0814/blockpairs"
    os.makedirs(os.path.join(tree, rel_dir), exist_ok=True)
    entries, preg, ids_all = [], [], []
    per = 8
    for s0 in range(0, n, per):
        m = min(per, n - s0)
        seg = f"SYNSEG{s0 // per}"
        ids = [f"{seg}_{0}_{384 * i}" for i in range(m)]
        base = d2_data._smooth_noise(rng, (m, 384, 384), 3.0)
        img = np.clip(120 + 30 * base[:, None] + 8 * rng.standard_normal((m, 21, 384, 384)), 0, 255).astype(np.uint8)
        ref9 = np.clip(128 + 90 * d2_data._smooth_noise(rng, (m, 384, 384), 6.0), 0, 255).astype(np.uint8)
        valid = np.ones((m, 384, 384), bool)
        valid[:, :, :24] = False
        ink, sup = d2_data.labels_from_target(ref9, valid.astype(np.uint8))
        rel = f"{rel_dir}/{seg}.npz"
        np.savez_compressed(os.path.join(tree, rel), images=img, ref9=ref9,
                            labels=np.where(sup == 1, ink, 255).astype(np.uint8), valid=valid,
                            xyz=rng.random((m, 17, 17, 3)).astype(np.float32), patch_id=np.array(ids))
        entries.append(dict(shard=rel, branch="SYNTHETIC", n=m, bytes=os.path.getsize(os.path.join(tree, rel)),
                            sha256=d2_data.sha256_file(os.path.join(tree, rel)), patch_ids=ids))
        preg += [dict(patch_id=i, segment=seg, y0=0, x0=384 * k, size=384) for k, i in enumerate(ids)]
        ids_all += ids
    root = os.path.join(tree, "logs/sib/pairs0814")
    json.dump(dict(shards=entries, synthetic=True), open(os.path.join(root, "shards.json"), "w"), indent=1)
    json.dump(dict(patches=preg, synthetic=True), open(os.path.join(root, "pair_registry.json"), "w"), indent=1)
    return root, ids_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--batches", type=int, default=12)
    a = ap.parse_args()
    import numpy as np
    W = os.path.abspath(a.work)
    os.makedirs(W, exist_ok=True)
    tree = os.path.join(W, "tree")
    root, ids_all = write_stagec(tree, a.n, 20260926)
    rng = np.random.default_rng(7)
    held_pool = sorted(rng.choice(ids_all, 5, replace=False).tolist())
    held = held_pool + ["NOT_IN_POOL_0_0"]
    json.dump(held, open(os.path.join(W, "holdout.json"), "w"))
    req = dict(decl="DECL-D2-A1 (SYNTHETIC hold-out check)", d2_date=None,
               sources=[dict(name="pairs0814u", kind="stagec", branch="SYNTHETIC", commit="SYNTHETIC", path=root,
                             data_root=tree)],
               holdouts=[dict(reason="SYNTHETIC hold-out list", file=os.path.join(W, "holdout.json"))])
    json.dump(req, open(os.path.join(W, "req.json"), "w"), indent=1)
    fz = os.path.join(W, "freeze")
    run([PY, os.path.join(TH, "pair_freeze.py"), "--request", os.path.join(W, "req.json"), "--out", fz, "--verify"])
    rec = json.load(open(os.path.join(fz, "pair_freeze.json")))
    allow_f = os.path.join(fz, "allow_pairs0814u.json")
    allow = json.load(open(allow_f))
    cfgs = {}
    for arm in ("NULL", "P384"):
        out = run([PY, os.path.join(TH, "d2_train.py"), "make-config", "--arm", arm, "--seed", "1", "--subtile",
                   "--batch", "32", "--micro-batch", "4", "--steps", "12000", "--forward", "full", "--precision", "fp32",
                   "--threads", "4", "--z-jitter", "2", "--z-centre-offset", "0", "--lr", "2e-5",
                   "--weight-decay", "3e-5", "--log-every", "50", "--ckpt-every", "250",
                   "--source", f"pairs0814u=stagec:{root}", "--allow-ids", f"pairs0814u={allow_f}",
                   "--data-root", f"pairs0814u={tree}", "--hash-sources", "--decl", "DECL-D2",
                   "--out", os.path.join(W, f"cfg_{arm}.json")])
        cfgs[arm] = json.loads(out.strip().splitlines()[-1])
    os.environ["OMP_NUM_THREADS"] = os.environ["MKL_NUM_THREADS"] = "4"
    import d2_train
    import d2_data
    # one Trainer per process: Trainers seed and share the process-global python / numpy / torch RNGs, so the
    # P384-vs-NULL pairing is measured by pair_check.py in separate processes (batch draws only)
    tn = d2_train.Trainer(d2_train.validate_config(json.load(open(os.path.join(W, "cfg_NULL.json")))),
                          os.path.join(W, "tr_NULL"))
    sN = tn.sources[0]
    sP = d2_data.load_source(json.load(open(os.path.join(W, "cfg_P384.json")))["sources"][0])
    fresh_all = d2_data.load_source(dict(kind="stagec", path=root, name="all", data_root=tree))
    fa = {pid: i for i, pid in enumerate(fresh_all.patch_id)}
    allowed_idx = [fa[p] for p in sN.patch_id]
    held_idx = [fa[p] for p in held_pool]
    n = len(sN)
    drng = np.random.default_rng(1)
    while True:
        perm = drng.permutation(n)
        if not np.any(perm == np.arange(n)):
            break
    f_ink, f_sup = fresh_all.ink[allowed_idx], fresh_all.sup[allowed_idx]
    lab_equal_held = sum(1 for i in range(n) for j in held_idx
                         if np.array_equal(sN.ink[i], fresh_all.ink[j]) and np.array_equal(sN.sup[i], fresh_all.sup[j]))
    draws_ok, drawn = True, set()
    for b in range(a.batches):
        _, srcN = tn.make_batch()
        for k, j, _, _ in srcN:
            pid = sN.patch_id[j // tn.nsub[k]]
            drawn.add(pid)
            draws_ok &= (pid in allow) and (pid not in held)
    pc = {}
    for arm in ("NULL", "P384"):
        run([PY, os.path.join(HERE, "pair_check.py"), "--config", os.path.join(W, f"cfg_{arm}.json"),
             "--out", os.path.join(W, f"pair_{arm}.json"), "--steps", str(a.batches), "--train-steps", "0",
             "--trainer-dir", TH])
        pc[arm] = json.load(open(os.path.join(W, f"pair_{arm}.json")))["steps"]
    img_eq = [x["image_sha256"] == y["image_sha256"] for x, y in zip(pc["NULL"], pc["P384"])]
    dig_eq = [x["sample_digest"] == y["sample_digest"] for x, y in zip(pc["NULL"], pc["P384"])]
    lab_diff = [x["ink_sha256"] != y["ink_sha256"] for x, y in zip(pc["NULL"], pc["P384"])]
    dig_inproc = tn.sample_digest == pc["NULL"][-1]["sample_digest"]
    # tamper: an edited allowlist with the config's pinned sha256 must be refused
    cfg = json.load(open(os.path.join(W, "cfg_NULL.json")))
    bad = os.path.join(W, "allow_edited.json")
    json.dump(allow + [held_pool[0]], open(bad, "w"))
    spec = dict(cfg["sources"][0], allow_ids=bad)
    try:
        d2_data.load_source(spec)
        tamper = "ACCEPTED (defect)"
    except ValueError as e:
        tamper = "refused: " + str(e)[:160]
    res = dict(
        provenance=d2_train.PROV, data="SYNTHETIC stage-C tree (no real data, no image opened)",
        trainer_head_commit="08d7e42da1bc2a01c55b8ca0659f00c2b2c33935",
        code_sha256={f: d2_data.sha256_file(os.path.join(TH, f)) for f in ("d2_train.py", "d2_data.py", "pair_freeze.py")},
        freeze=dict(record_sha256=rec["record_sha256"], data_registry_digest=rec["data_registry_digest"],
                    counts=rec["sources"][0]["counts"], allow_ids=rec["sources"][0]["allow_ids"],
                    verified_load=rec["sources"][0].get("verified_load"), holdout_ids_total=rec["holdout_ids_total"]),
        configs=cfgs,
        config_allow_sha256_equals_freeze=all(json.load(open(os.path.join(W, f"cfg_{arm}.json")))["sources"][0]
                                              ["allow_ids_sha256"] == rec["sources"][0]["allow_ids"]["sha256"]
                                              for arm in cfgs),
        pool=dict(n_pool_total=len(ids_all), n_holdout_listed=len(held), n_holdout_in_pool=len(held_pool),
                  n_loaded_NULL=n, n_loaded_P384=len(sP), loaded_equals_allowlist=sorted(sN.patch_id) == sorted(allow),
                  held_out_loaded=sorted(set(sN.patch_id) & set(held))),
        derangement=dict(n=n, perm_sha256=h(perm.astype(np.int64).tobytes()),
                         matches_trainer=h(perm.astype(np.int64).tobytes()) == tn.meta["derangement"]["perm_sha256"],
                         fixed_points=int(np.sum(perm == np.arange(n))),
                         labels_equal_fresh_allowed_permuted=bool(np.array_equal(sN.ink, f_ink[perm]) and
                                                                  np.array_equal(sN.sup, f_sup[perm])),
                         label_arrays_equal_to_a_held_out_patch=lab_equal_held,
                         P384_labels_unpermuted=bool(np.array_equal(sP.ink, f_ink) and np.array_equal(sP.sup, f_sup))),
        draws=dict(batches=a.batches, samples=a.batches * 32, all_drawn_allowed_and_not_held=bool(draws_ok),
                   distinct_patches_drawn=len(drawn)),
        pairing=dict(method="pair_check.py per arm in separate processes, batch draws only", batches=a.batches,
                     images_equal_every_batch=all(img_eq), digest_equal_every_batch=all(dig_eq),
                     labels_differ_every_batch=all(lab_diff), null_in_process_digest_equals_subprocess=dig_inproc),
        tamper_edited_allowlist=tamper)
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
