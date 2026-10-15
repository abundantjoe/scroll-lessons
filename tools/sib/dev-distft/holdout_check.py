# Provenance: Project HERCULES | owner the owner | [id removed]
"""Hold-out list check (numbers only): which training-pair patches a DEV hold-out list removes, fail-closed.
Hold-out segments = DEV window segments + every segment listed same-papyrus with one (the registry's
holdout_segments for 0814; for 0139, window segment_ids + their cert_samepap_other_traces keys).
Reads git objects only. Usage: holdout_check.py <dev_registry git ref:path> <out.json>"""
import collections, hashlib, json, subprocess, sys

def show(spec):
    return subprocess.run(["git", "show", spec], capture_output=True, check=True).stdout

reg_spec, outp = sys.argv[1], sys.argv[2]
raw = show(reg_spec); reg = json.loads(raw)
res = dict(provenance="Provenance: Project HERCULES | owner the owner | [id removed]",
           dev_registry=reg_spec, dev_registry_sha256=hashlib.sha256(raw).hexdigest(),
           status="PROVISIONAL: registry not frozen, no DEV METRIC-HASH in RULES.md", scrolls={})
for s, v in reg["scrolls"].items():
    h = v.get("holdout_segments") or {}
    segs = set(h.get("dev_segments", [])) | set(h.get("samepap_with_dev", {}))
    for w in v.get("windows", []):
        if w.get("role") == "text":
            segs.add(w["segment_id"]); segs |= set(w.get("cert_samepap_other_traces") or {})
    res["scrolls"][s] = dict(holdout_segments=sorted(segs), n=len(segs),
                             source="holdout_segments + text windows" if h else "text windows + their same-papyrus traces")
# pairs0814 / pairs0814b gated staged patches
rows = []
for b in ("pairs0814", "pairs0814b"):
    ref = f"origin/claude/gifted-bell-gavnl5-sib-{b}"
    files = [f for f in show(f"{ref}:logs/sib/{b}/registry").decode().split() if f.endswith(".jsonl")]
    for f in files:
        rows += [dict(json.loads(l), _branch=b) for l in show(f"{ref}:logs/sib/{b}/registry/{f}").decode().splitlines() if l.strip()]
held = set(res["scrolls"].get("PHerc0814", {}).get("holdout_segments", []))
kept = collections.Counter(); drop = collections.Counter()
for r in rows:
    if r.get("passed") and r.get("staged"):
        (drop if r["segment"] in held else kept)[r["segment"]] += 1
res["pairs0814_gated_patches"] = dict(total=sum(kept.values()) + sum(drop.values()), kept=sum(kept.values()),
                                      dropped=sum(drop.values()), dropped_by_segment=dict(drop),
                                      kept_by_segment=dict(kept))
res["pairs0139"] = "no tile registry on git (branch holds logs/tools only); counts pending"
json.dump(res, open(outp, "w"), indent=1, sort_keys=True)
print(json.dumps({k: res[k] for k in ("status", "pairs0814_gated_patches")})[:1500])
print({s: v["n"] for s, v in res["scrolls"].items()})
