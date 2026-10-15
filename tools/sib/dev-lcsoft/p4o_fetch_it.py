#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Fetch official scrollprize/PHerc.1667-iteration-N files at the commit pinned in data/catalogue/checkpoints.json
(config.json, configuration_inkdetection.py, modeling_inkdetection.py -> /work/cards/it<N>_<name>, verified by git
blob oid; model.safetensors -> /work/ckpt/PHerc.1667-iteration-N/, verified by LFS sha256). Never downloads previews
or README figures. One JSON line per file appended to logs/sib/dev-lcsoft/p4o/downloads.jsonl."""
import hashlib, json, os, subprocess, sys, time
REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
CAT = json.load(open(os.path.join(REPO, "data/catalogue/checkpoints.json")))
LOG = os.path.join(REPO, "logs/sib/dev-lcsoft/p4o/downloads.jsonl")
it = int(sys.argv[1])
m = next(x for x in CAT["all_scrollprize_hf_models"] if x["repo"] == f"scrollprize/PHerc.1667-iteration-{it}")
assert not m.get("gated") and not m.get("private")
os.makedirs(os.path.dirname(LOG), exist_ok=True)
for f in m["files"]:
    name = f["path"]
    if name not in ("config.json", "configuration_inkdetection.py", "modeling_inkdetection.py", "model.safetensors"):
        continue
    dst = (f"/work/cards/it{it}_{name}" if name != "model.safetensors"
           else f"/work/ckpt/PHerc.1667-iteration-{it}/model.safetensors")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    url = f"https://huggingface.co/{m['repo']}/resolve/{m['commit_sha']}/{name}"
    t0 = time.time()
    for k in range(5):
        if subprocess.run(["curl", "-fsSL", "-o", dst, url]).returncode == 0:
            break
        time.sleep(2 ** (k + 1))
    b = open(dst, "rb").read()
    sha = hashlib.sha256(b).hexdigest()
    oid = hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
    ok = (sha == f["lfs_sha256"]) if f.get("lfs_sha256") else (oid == f["git_oid"])
    rec = dict(utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), repo=m["repo"], commit=m["commit_sha"], file=name,
               url=url, bytes=len(b), sha256=sha, git_oid=oid, verified=ok, seconds=round(time.time() - t0, 1))
    open(LOG, "a").write(json.dumps(rec) + "\n")
    print(json.dumps(rec))
    if not ok:
        os.remove(dst)
        sys.exit(f"verification failed: {name}")
