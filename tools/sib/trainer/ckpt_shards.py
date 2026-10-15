# Provenance: Project HERCULES | owner the owner | [id removed]
"""Container-reclaim survival for the D2 trainer: serialise a resumable training state, split it into shards
< 90 MB, and keep ONLY the latest copy on a dedicated git ref as a single parentless (orphan) commit that is
force-pushed (history never grows; the previous commit becomes unreachable).

Commit tree:  MANIFEST.json  +  shard_000.bin, shard_001.bin, ...
MANIFEST.json = {schema, step, config_sha256, total_bytes, total_sha256, shards: [{file, bytes, sha256}], utc}
Restore = fetch the ref (depth 1) into a private bare repo, read the blobs, verify every sha256, concatenate, load.

All git work happens in a private bare repo (default /work/d2ckpt/git.bare), never in the working checkout, so the
main repo's objects and history are untouched. Pushing uses the same remote URL as the checkout's origin.
Refused: shard size >= 95 MB (GitHub hard limit is 100 MB)."""
from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
import subprocess

SCHEMA = "hercules-d2-resume-shards/1"
MAX_SHARD = 90 * 1000 * 1000
HARD_CAP = 95 * 1000 * 1000


def _utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(bare: str, *args, input_bytes: bytes | None = None, env_extra: dict | None = None) -> bytes:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(["git", "--git-dir", bare, *args], input=input_bytes, capture_output=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:3])} failed rc={r.returncode}: {r.stderr.decode(errors='replace')[-800:]}")
    return r.stdout


def ensure_bare(bare: str) -> str:
    if not os.path.exists(os.path.join(bare, "HEAD")):
        os.makedirs(bare, exist_ok=True)
        subprocess.run(["git", "init", "-q", "--bare", bare], check=True)
    return bare


def split_bytes(blob: bytes, max_shard: int = MAX_SHARD) -> list[bytes]:
    if max_shard >= HARD_CAP:
        raise ValueError(f"shard size {max_shard} must be < {HARD_CAP}")
    return [blob[i:i + max_shard] for i in range(0, len(blob), max_shard)] or [b""]


def state_to_bytes(state) -> bytes:
    import torch
    buf = io.BytesIO()
    torch.save(state, buf)
    return buf.getvalue()


def bytes_to_state(b: bytes):
    import torch
    return torch.load(io.BytesIO(b), map_location="cpu", weights_only=False)


def build_commit(bare: str, blob: bytes, *, step: int, config_sha256: str, max_shard: int = MAX_SHARD,
                 extra: dict | None = None) -> tuple[str, dict]:
    """Write shards + manifest as one parentless commit in the bare repo; return (commit sha, manifest)."""
    ensure_bare(bare)
    shards = split_bytes(blob, max_shard)
    entries, man_shards = [], []
    for i, sb in enumerate(shards):
        name = f"shard_{i:03d}.bin"
        oid = _git(bare, "hash-object", "-w", "--stdin", input_bytes=sb).decode().strip()
        entries.append(f"100644 blob {oid}\t{name}")
        man_shards.append(dict(file=name, bytes=len(sb), sha256=hashlib.sha256(sb).hexdigest()))
    manifest = dict(schema=SCHEMA, step=int(step), config_sha256=config_sha256, total_bytes=len(blob),
                    total_sha256=hashlib.sha256(blob).hexdigest(), shards=man_shards, utc=_utc(), **(extra or {}))
    mb = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()
    moid = _git(bare, "hash-object", "-w", "--stdin", input_bytes=mb).decode().strip()
    entries.append(f"100644 blob {moid}\tMANIFEST.json")
    tree = _git(bare, "mktree", input_bytes=("\n".join(sorted(entries, key=lambda e: e.split("\t")[1])) + "\n")
                .encode()).decode().strip()
    ident = {"GIT_AUTHOR_NAME": "hercules-d2-trainer", "GIT_AUTHOR_EMAIL": "[email removed]",
             "GIT_COMMITTER_NAME": "hercules-d2-trainer", "GIT_COMMITTER_EMAIL": "[email removed]"}
    msg = (f"D2 trainer resume state step {step} (config {config_sha256[:16]}); latest only, force-pushed orphan\n\n"
           "Provenance: Project HERCULES | owner the owner | [id removed]\n")
    commit = _git(bare, "commit-tree", tree, "-m", msg, env_extra=ident).decode().strip()
    return commit, manifest


def push_commit(bare: str, commit: str, remote_url: str, ref: str) -> None:
    """Force-push the orphan commit to ref, then verify the remote tip equals it."""
    if not ref.startswith("refs/"):
        raise ValueError("ref must be a full ref name (refs/...)")
    _git(bare, "push", "--force", "--no-verify", remote_url, f"{commit}:{ref}")
    tip = _git(bare, "ls-remote", remote_url, ref).decode().split()
    if not tip or tip[0] != commit:
        raise RuntimeError(f"remote tip {tip[:1]} != pushed {commit}")


def prune_local(bare: str, keep_commit: str | None = None) -> None:
    """Drop every local object except keep_commit's (older states never accumulate on disk)."""
    refs = _git(bare, "for-each-ref", "--format=%(refname)").decode().split()
    for r in refs:
        _git(bare, "update-ref", "-d", r)
    if keep_commit:
        _git(bare, "update-ref", "refs/local/keep", keep_commit)
    _git(bare, "reflog", "expire", "--expire=now", "--all")
    _git(bare, "gc", "-q", "--prune=now")


def save_and_push(bare: str, state, *, step: int, config_sha256: str, remote_url: str | None, ref: str | None,
                  max_shard: int = MAX_SHARD, extra: dict | None = None) -> dict:
    blob = state if isinstance(state, (bytes, bytearray)) else state_to_bytes(state)
    commit, manifest = build_commit(bare, blob, step=step, config_sha256=config_sha256, max_shard=max_shard,
                                    extra=extra)
    pushed = False
    if remote_url and ref:
        push_commit(bare, commit, remote_url, ref)
        pushed = True
    prune_local(bare, keep_commit=commit)
    return dict(commit=commit, pushed=pushed, ref=ref, n_shards=len(manifest["shards"]),
                total_bytes=manifest["total_bytes"], total_sha256=manifest["total_sha256"],
                max_shard_bytes=max(s["bytes"] for s in manifest["shards"]))


def read_commit(bare: str, commit: str) -> tuple[bytes, dict]:
    man = json.loads(_git(bare, "cat-file", "blob", f"{commit}:MANIFEST.json"))
    if man.get("schema") != SCHEMA:
        raise ValueError(f"manifest schema {man.get('schema')!r}")
    parts = []
    for s in man["shards"]:
        b = _git(bare, "cat-file", "blob", f"{commit}:{s['file']}")
        if len(b) != s["bytes"] or hashlib.sha256(b).hexdigest() != s["sha256"]:
            raise ValueError(f"shard {s['file']} fails its sha256/size check")
        parts.append(b)
    blob = b"".join(parts)
    if hashlib.sha256(blob).hexdigest() != man["total_sha256"] or len(blob) != man["total_bytes"]:
        raise ValueError("reassembled state fails the total sha256/size check")
    return blob, man


def fetch_latest(bare: str, remote_url: str, ref: str) -> tuple[bytes, dict] | None:
    """Fetch the ref (depth 1) and return (state bytes, manifest), or None if the ref does not exist."""
    ensure_bare(bare)
    tip = _git(bare, "ls-remote", remote_url, ref).decode().split()
    if not tip:
        return None
    _git(bare, "fetch", "-q", "--depth", "1", "--no-tags", remote_url, f"+{ref}:refs/local/fetched")
    commit = _git(bare, "rev-parse", "refs/local/fetched").decode().strip()
    if commit != tip[0]:
        raise RuntimeError("fetched commit differs from the remote tip")
    parents = _git(bare, "rev-list", "--parents", "-n", "1", commit).decode().split()
    if len(parents) != 1:
        raise RuntimeError("resume ref is not a single parentless commit")
    return read_commit(bare, commit)


def origin_url(repo_dir: str) -> str:
    return subprocess.run(["git", "-C", repo_dir, "remote", "get-url", "origin"], capture_output=True, text=True,
                          check=True).stdout.strip()


def main(argv=None):
    """CLI: fetch the latest shards of a ref and write the reassembled bytes (resume state or final weights)."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("fetch",))
    ap.add_argument("--remote-url", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--bare", default="/work/d2ckpt/fetch.bare")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    got = fetch_latest(a.bare, a.remote_url, a.ref)
    if got is None:
        print(json.dumps(dict(ref=a.ref, found=False)))
        return 1
    blob, man = got
    with open(a.out + ".tmp", "wb") as fh:
        fh.write(blob)
    os.replace(a.out + ".tmp", a.out)
    print(json.dumps(dict(ref=a.ref, found=True, out=a.out, kind=man.get("kind", "resume"), step=man["step"],
                          total_sha256=man["total_sha256"], n_shards=len(man["shards"]))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
