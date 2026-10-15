# Provenance: Project HERCULES | owner the owner | [id removed]
"""D3 Stage 1 record: hashes of all D3 scripts and the two pool manifests, pool sizes and label pixel counts,
smoke-test results, deviations. Writes /work/d3/work/stage1.json. Numbers only."""
import os, json, hashlib, datetime, subprocess

D3 = "/work/d3"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def du(p):
    return subprocess.run(["du", "-sb", p], capture_output=True, text=True).stdout.split()[0]


scripts = {f: sha256(f"{D3}/scripts/{f}") for f in sorted(os.listdir(f"{D3}/scripts")) if not f.endswith(".pyc")}
pools = {}
for name in ("fa", "replay"):
    pd = f"{D3}/pool_{name}"
    m = json.load(open(f"{pd}/manifest.json"))
    meta = m["meta"]
    pools[name] = dict(manifest=f"{pd}/manifest.json", manifest_sha256=sha256(f"{pd}/manifest.json"),
                       n_tiles=m["n_tiles"], label_px=m["label_px"], files_sha256=m["files_sha256"],
                       shapes=m["storage"]["shapes"],
                       **({k: meta[k] for k in ("n_primary_text", "n_ge144", "n_kept", "n_dropped_lt144", "dropped",
                                                "per_segment_kept")} if name == "fa" else
                          {k: meta[k] for k in ("candidates", "quota", "picked", "grid_stride", "seed",
                                                "tiles_overlapping_D1_canary_window_w044")}),
                       n_renders=(len(meta["renders"]) if name == "replay" else m["n_tiles"]),
                       render_failed_twice_dropped=meta.get("render_failed_twice_dropped"))
smoke_path = f"{D3}/work/smoke/smoke_results.json"
smoke = dict(results=json.load(open(smoke_path)), results_sha256=sha256(smoke_path))
rec = dict(
    provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
    stage="D3 stage 1 (DECL-D3-A1): pools, training script, smoke tests; hashed before the full run",
    generated_utc=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    viewing="no image or pixel array was opened, displayed or described; numbers only",
    not_read="/srv/scorer, /work/sealed_io, seals/, /work/jseal/seal_J.age, J-window renders/maps",
    scripts_sha256=scripts,
    pools=pools,
    inputs=dict(fa_tiles_json=dict(path=f"{D3}/work/fa_tiles.json", sha256=sha256(f"{D3}/work/fa_tiles.json")),
                fetch_log_0139=dict(path=f"{D3}/logs/fetch_0139.txt", sha256=sha256(f"{D3}/logs/fetch_0139.txt")),
                base_checkpoint=dict(path="/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth",
                                     sha256=sha256("/work/ckpt/ink_9um/hybrid_3d2d-seed42/step-075000.pth")),
                official_train_py=dict(path="/work/villa/vesuvius/src/vesuvius/ink_detection/training/train.py",
                                       sha256=sha256("/work/villa/vesuvius/src/vesuvius/ink_detection/training/train.py")),
                vc_render_tifxyz=sha256("/work/villa/volume-cartographer/build/hrc-release-gcc/bin/vc_render_tifxyz"),
                extra_python_packages="/work/d3_timing/pylib (scipy, scikit-image, lazy_loader, fft-conv-pytorch, "
                                      "SimpleITK, pandas, connected-components-3d, numba, llvmlite; --no-deps target)"),
    smoke=smoke,
    ledger=f"{D3}/work/ledger.tsv",
    ledger_render_rows=dict(ok=sum(1 for l in open(f"{D3}/work/ledger.tsv") if l.split("\t")[5:6] == ["0"]),
                            failed=sum(1 for l in open(f"{D3}/work/ledger.tsv") if l.split("\t")[5:6] not in (["0"], ["exit"]))),
    governing=["DECL-D3D4", "DECL-D3-A1", "DECL-D3-A2"],
    disk_bytes={p: int(du(p)) for p in (f"{D3}/pool_fa", f"{D3}/pool_replay", f"{D3}/work", f"{D3}/data", D3)},
    deviations=json.load(open(f"{D3}/work/deviations.json")) if os.path.exists(f"{D3}/work/deviations.json") else [],
)
json.dump(rec, open(f"{D3}/work/stage1.json", "w"), indent=1)
print(sha256(f"{D3}/work/stage1.json"))
print(json.dumps({k: v for k, v in rec.items() if k not in ("pools",)}, indent=1)[:6000])
