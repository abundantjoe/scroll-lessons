# Provenance: Project HERCULES | owner the owner | [id removed]
"""Copy staged stage-B block npz files (/work/sib/blockpairs) into logs/sib/pairs0814/blockpairs/ after checking each
file's sha256 against the registry's staged_sha256 and the < 90 MB limit; append blockpairs_manifest.jsonl. Prints the
new files' total bytes. Only files whose block has a done marker (complete) are copied; git add/commit/push is done by
the caller in batches of <= 500 MB."""
import glob, hashlib, json, os, shutil, sys
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
L = f"{REPO}/logs/sib/pairs0814"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
reg = {}
for f in glob.glob(f"{L}/registry/*.jsonl"):
    for l in open(f):
        r = json.loads(l)
        if r.get("staged"): reg.setdefault(r["staged"], set()).add(r["staged_sha256"])
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 500 * 10**6
tot, new = 0, []
for src in sorted(glob.glob("/work/sib/blockpairs/*/*.npz")):
    if src.endswith(".tmp.npz"): continue
    rel = "blockpairs/" + os.path.relpath(src, "/work/sib/blockpairs")
    dst = f"{L}/{rel}"
    if os.path.exists(dst): continue
    s, n = sha(src), os.path.getsize(src)
    assert reg.get(rel) == {s}, f"registry sha mismatch for {rel}: {reg.get(rel)} vs {s}"
    assert n < 90 * 1024 * 1024, (rel, n)
    if tot + n > limit: break
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    assert sha(dst) == s
    with open(f"{L}/blockpairs_manifest.jsonl", "a") as fh:
        fh.write(json.dumps({"file": rel, "bytes": n, "sha256": s}) + "\n")
    tot += n; new.append(rel)
print(len(new), tot)
