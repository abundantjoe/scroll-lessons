# Provenance: Project HERCULES | owner the owner | [id removed]
"""Stream-and-upload disk offload to the private GitHub repo (owner-directed; RULES.md DECL-OFFLOAD-1).

Outputs are produced in a bounded local working folder, pushed as one commit per batch to the data branch
claude/gifted-bell-gavnl5-data, verified on the remote, and only then may the local copy be removed. Each batch
commit's tree holds only that batch (under <label>/) plus BATCH.json; batches are chained by parent links, so the
branch tip stays small and any batch can be fetched alone by its commit sha. The local git work uses a throwaway
repo with a blob-free shallow fetch of the tip (no history, no old blobs), so local disk use is the batch itself.
The manifest of every batch (label, commit, files, sha256, bytes) is appended to logs/offload/manifest.jsonl on the
work branch.

Refused: anything under /srv/scorer or /work/sealed_io, seal keys (*.agekey, *key*.json under scorer paths),
unencrypted seals, files > 95 MB, batches > 1.5 GB, extensions outside ALLOWED, symlinks.

Usage:
  python tools/offload/git_offload.py push <src_dir> <label> [--delete-after]
  python tools/offload/git_offload.py fetch <label> <dest_dir>
  python tools/offload/git_offload.py list
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRANCH = "claude/gifted-bell-gavnl5-data"
MANIFEST = os.path.join(REPO, "logs", "offload", "manifest.jsonl")
TMP_ROOT = "/work/offload_tmp"
ALLOWED = {".png", ".npz", ".npy", ".json", ".jsonl", ".tsv", ".txt", ".md", ".csv", ".tif", ".tiff", ".log", ".age"}
FORBIDDEN_PREFIXES = ("/srv/scorer", "/work/sealed_io", "/srv/")
MAX_FILE = 95 * 1024 * 1024
MAX_BATCH = int(1.5 * 1024 ** 3)
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"


def _git(args, cwd, env=None, capture=True):
    r = subprocess.run(["git"] + args, cwd=cwd, env=env, capture_output=capture, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()[:500]}")
    return r.stdout.strip() if capture else ""


def _sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _check_files(src):
    src = os.path.realpath(src)
    if any(src.startswith(p) for p in FORBIDDEN_PREFIXES):
        raise ValueError(f"refused: {src} is under a forbidden prefix")
    files, total = [], 0
    for root, dirs, names in os.walk(src):
        for n in names:
            p = os.path.join(root, n)
            rel = os.path.relpath(p, src)
            if os.path.islink(p):
                raise ValueError(f"refused symlink {rel}")
            ext = os.path.splitext(n)[1].lower()
            if ext not in ALLOWED:
                raise ValueError(f"refused extension {ext!r}: {rel}")
            low = n.lower()
            if low.endswith(".agekey") or "seal.agekey" in low:
                raise ValueError(f"refused key file {rel}")
            s = os.path.getsize(p)
            if s > MAX_FILE:
                raise ValueError(f"refused {rel}: {s} bytes > {MAX_FILE}")
            total += s
            files.append((rel, p, s))
    if total > MAX_BATCH:
        raise ValueError(f"refused batch: {total} bytes > {MAX_BATCH}")
    if not files:
        raise ValueError("empty batch")
    return sorted(files), total


def _origin():
    return _git(["remote", "get-url", "origin"], REPO)


def _remote_tip():
    out = _git(["ls-remote", "origin", f"refs/heads/{BRANCH}"], REPO)
    return out.split()[0] if out else None


def push(src, label, delete_after=False):
    if not label or "/" in label or label.startswith("."):
        raise ValueError("label must be a single path component")
    files, total = _check_files(src)
    entries = [{"path": f"{label}/{rel}", "bytes": s, "sha256": _sha256(p)} for rel, p, s in files]
    os.makedirs(TMP_ROOT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="wc_", dir=TMP_ROOT)
    try:
        _git(["init", "-q"], tmp)
        _git(["remote", "add", "origin", _origin()], tmp)
        _git(["config", "user.name", _git(["config", "user.name"], REPO) or "hercules"], tmp)
        _git(["config", "user.email", _git(["config", "user.email"], REPO) or "hercules@localhost"], tmp)
        parent = _remote_tip()
        if parent:
            _git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", f"refs/heads/{BRANCH}"], tmp)
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, ".git", "offload_index"))
        for (rel, p, s), e in zip(files, entries):
            blob = _git(["hash-object", "-w", p], tmp)
            _git(["update-index", "--add", "--cacheinfo", f"100644,{blob},{e['path']}"], tmp, env=env)
        meta = {"provenance": PROV, "label": label, "created_utc": _utc(), "source_dir": os.path.realpath(src),
                "n_files": len(entries), "bytes": total, "files": entries}
        mp = os.path.join(tmp, "BATCH.json")
        with open(mp, "w") as fh:
            json.dump(meta, fh, indent=1)
        mblob = _git(["hash-object", "-w", mp], tmp)
        _git(["update-index", "--add", "--cacheinfo", f"100644,{mblob},BATCH.json"], tmp, env=env)
        tree = _git(["write-tree"], tmp, env=env)
        msg = f"offload batch {label} ({len(entries)} files, {total} bytes)\n\n{PROV}\n"
        args = ["commit-tree", tree, "-m", msg] + (["-p", parent] if parent else [])
        commit = _git(args, tmp)
        for attempt in range(5):
            try:
                _git(["push", "-q", "origin", f"{commit}:refs/heads/{BRANCH}"], tmp)
                break
            except RuntimeError:
                if attempt == 4:
                    raise
                time.sleep(2 ** (attempt + 1))
        if _remote_tip() != commit:
            raise RuntimeError("remote tip does not equal the pushed commit; local copy kept")
        rec = {"utc": _utc(), "label": label, "branch": BRANCH, "commit": commit, "parent": parent, "tree": tree,
               "n_files": len(entries), "bytes": total, "files": entries}
        os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
        with open(MANIFEST, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if delete_after:
        # verified on the remote above; remove only the files that were pushed, then empty dirs
        for rel, p, s in files:
            os.remove(p)
        for root, dirs, names in os.walk(src, topdown=False):
            if not os.listdir(root):
                os.rmdir(root)
    return rec


def fetch(label, dest):
    recs = [json.loads(l) for l in open(MANIFEST)] if os.path.exists(MANIFEST) else []
    rec = [r for r in recs if r["label"] == label]
    if not rec:
        raise KeyError(f"no batch {label!r} in manifest")
    rec = rec[-1]
    os.makedirs(TMP_ROOT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="rd_", dir=TMP_ROOT)
    try:
        _git(["init", "-q"], tmp)
        _git(["remote", "add", "origin", _origin()], tmp)
        _git(["fetch", "-q", "--depth", "1", "origin", rec["commit"]], tmp)
        os.makedirs(dest, exist_ok=True)
        for e in rec["files"]:
            out = os.path.join(dest, os.path.relpath(e["path"], label))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "wb") as fh:
                fh.write(subprocess.run(["git", "cat-file", "blob", f"{rec['commit']}:{e['path']}"], cwd=tmp,
                                        capture_output=True, check=True).stdout)
            if _sha256(out) != e["sha256"]:
                raise RuntimeError(f"sha256 mismatch for {e['path']}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return rec


def main(argv):
    if len(argv) >= 3 and argv[0] == "push":
        r = push(argv[1], argv[2], delete_after="--delete-after" in argv)
        print(json.dumps({k: r[k] for k in ("label", "commit", "n_files", "bytes")}))
    elif len(argv) == 3 and argv[0] == "fetch":
        r = fetch(argv[1], argv[2])
        print(json.dumps({"label": r["label"], "commit": r["commit"], "n_files": r["n_files"], "dest": argv[2]}))
    elif argv[:1] == ["list"]:
        if os.path.exists(MANIFEST):
            for l in open(MANIFEST):
                r = json.loads(l)
                print(r["utc"], r["label"], r["commit"][:12], r["n_files"], r["bytes"])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
