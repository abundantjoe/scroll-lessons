#!/usr/bin/env python3
# Provenance: Project HERCULES | owner the owner | [id removed]
"""Download official scrollprize/PHerc.1667-iteration-N weight files at the commit pinned in
data/catalogue/checkpoints.json and verify sha256 against the catalogued LFS oid.
Never downloads preview images. Appends one record per file to logs/sib/ckpt-screen-b/downloads.jsonl."""
import hashlib, json, os, subprocess, sys, time
REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
CAT = json.load(open(os.path.join(REPO, "data/catalogue/checkpoints.json")))
OUT = os.environ.get("CKB_CKPT_DIR", "/work/ckpt")
LOG = os.path.join(REPO, "logs/sib/ckpt-screen-b/downloads.jsonl")
ALLOWED = {"model.safetensors", "last.ckpt"}  # plus the card/code files via fetch_cards

def entry(it):
    for m in CAT["all_scrollprize_hf_models"]:
        if m["repo"] == f"scrollprize/PHerc.1667-iteration-{it}":
            return m
    raise KeyError(it)

def fetch(it, fname):
    assert fname in ALLOWED
    m = entry(it)
    f = next(x for x in m["files"] if x["path"] == fname)
    if m.get("gated") or m.get("private"):
        rec = {"iteration": it, "file": fname, "status": "unavailable (gated/private)"}
    else:
        url = f"https://huggingface.co/{m['repo']}/resolve/{m['commit_sha']}/{fname}"
        dst = os.path.join(OUT, f"PHerc.1667-iteration-{it}", fname)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        t0 = time.time()
        for k in range(5):
            r = subprocess.run(["curl", "-fsSL", "-o", dst, url])
            if r.returncode == 0:
                break
            time.sleep(2 ** (k + 1))
        h = hashlib.sha256()
        with open(dst, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 22), b""):
                h.update(b)
        got = h.hexdigest()
        rec = {"iteration": it, "repo": m["repo"], "commit": m["commit_sha"], "file": fname, "url": url,
               "bytes": os.path.getsize(dst), "bytes_catalogue": f["bytes"], "sha256": got,
               "sha256_catalogue": f["lfs_sha256"], "verified": got == f["lfs_sha256"],
               "seconds": round(time.time() - t0, 1), "path": dst,
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        if not rec["verified"]:
            os.remove(dst)
            rec["status"] = "sha256 MISMATCH, file deleted"
    with open(LOG, "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    print(json.dumps(rec), flush=True)
    return rec

CARD_FILES = ("README.md", "config.json", "configuration_inkdetection.py", "modeling_inkdetection.py")


def fetch_cards(it, out="/work/cards"):
    """Card + code at the pinned commit; verified by git blob oid; kept outside the repo."""
    m = entry(it)
    os.makedirs(out, exist_ok=True)
    for f in m["files"]:
        if f["path"] in CARD_FILES:
            dst = os.path.join(out, f"it{it}_{f['path']}")
            subprocess.run(["curl", "-fsSL", "-o", dst,
                            f"https://huggingface.co/{m['repo']}/resolve/{m['commit_sha']}/{f['path']}"], check=True)
            b = open(dst, "rb").read()
            ok = hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest() == f["git_oid"]
            print(json.dumps({"iteration": it, "file": f["path"], "git_oid_ok": ok,
                              "sha256": hashlib.sha256(b).hexdigest()}))
            if not ok:
                os.remove(dst)


if __name__ == "__main__":
    fname = sys.argv[1]
    if fname == "cards":
        for it in sys.argv[2:]:
            fetch_cards(int(it))
        sys.exit(0)
    for it in sys.argv[2:]:
        fetch(int(it), fname)
