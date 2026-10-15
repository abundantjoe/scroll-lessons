# Provenance: Project HERCULES | owner the owner | [id removed]
"""d2-p128 id-level hold-out check (numbers and ids only; no image, no array is opened).
Compares D2 pair candidates (pairs registries on their branches) and the trainer's DRY-RUN allowlist with:
  (a) the DEV segments of the devloop dev_registry.json (DECL-DEVLOOP-A1 item 6: DEV segments are excluded from every
      D2 training set; the +16 vox same-papyrus extension needs geometry and is NOT checked here);
  (b) PHerc0841 (fold L-0841: no 0841 data) and the eligible scrolls (data/catalogue/eligible_products.json);
  (c) the DECL-D2 pair filter on registry rows that pass: NCC >= 0.8 and >= 7 of 9 windows aligned within 1 px.
Usage: python3 holdout_check.py OUT.json  (reads git objects of the named refs; writes OUT.json)"""
import collections, hashlib, json, re, subprocess, sys

REFS = dict(dev="origin/claude/gifted-bell-gavnl5-sib-devloop", trainer="origin/claude/gifted-bell-gavnl5-sib-trainer",
            p0814="origin/claude/gifted-bell-gavnl5-sib-pairs0814", p0139="origin/claude/gifted-bell-gavnl5-sib-pairs0139")
git = lambda *a: subprocess.check_output(["git", *a]).decode()
show = lambda ref, p: git("show", f"{ref}:{p}")
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
out = dict(provenance="Project HERCULES | owner the owner | [id removed]", refs={k: git("rev-parse", v).strip() for k, v in REFS.items()})

dev_txt = show(REFS["dev"], "logs/sib/devloop/dev_registry.json"); dev = json.loads(dev_txt)
dev_segs = {sc: sorted(v["segment_id"] for v in d.get("segments", {}).values()) for sc, d in dev["scrolls"].items()}
out["dev_registry"] = dict(sha256=sha(dev_txt), segments=dev_segs)
ts = lambda s: s.split("-")[0].split("_")[0]          # leading timestamp of a segment id
dev_ts = {sc: {ts(s) for s in v} for sc, v in dev_segs.items()}

elig_txt = open("data/catalogue/eligible_products.json").read()
out["eligible_products_sha256"] = sha(elig_txt)

# pairs0814 registry rows
files = [f for f in git("ls-tree", "-r", "--name-only", REFS["p0814"], "logs/sib/pairs0814/registry").split() if f.endswith(".jsonl")]
rows = [json.loads(l) for f in files for l in show(REFS["p0814"], f).splitlines() if l.strip()]
segs = sorted({r["segment"] for r in rows})
st = collections.Counter(r["status"] for r in rows)
def filt(r):
    w = r.get("windows") or []
    return r.get("ncc0", 0) >= 0.8 and sum(1 for x in w if x.get("aligned") and abs(x["dy"]) <= 1 and abs(x["dx"]) <= 1) >= 7
bad_filter = [r["patch_id"] for r in rows if r["status"] in ("GATED", "PASSED", "PASS", "KEPT") and not filt(r)]
p0814 = dict(registry_files=len(files), rows=len(rows), status=dict(st), segments=segs,
             segments_in_dev_0814=sorted(s for s in segs if ts(s) in dev_ts.get("PHerc0814", set())),
             rows_in_dev_segments=sum(1 for r in rows if ts(r["segment"]) in dev_ts.get("PHerc0814", set())),
             gated_rows_failing_decl_d2_filter=len(bad_filter), failing_ids_head=bad_filter[:10],
             segment_ids_mentioning_0841=[s for s in segs if "0841" in s],
             segment_ids_in_eligible_catalogue=[s for s in segs if s in elig_txt])
out["pairs0814"] = p0814

allow_txt = show(REFS["trainer"], "logs/sib/trainer/freeze_dryrun/allow_pairs0814.json"); allow = json.loads(allow_txt)
in_dev = [p for p in allow if p.split("_")[0] in dev_ts.get("PHerc0814", set())]
out["dryrun_allow_pairs0814"] = dict(sha256=sha(allow_txt), n=len(allow),
                                     per_segment=dict(collections.Counter(p.split("_")[0] for p in allow)),
                                     n_in_dev_segments=len(in_dev),
                                     per_dev_segment=dict(collections.Counter(p.split("_")[0] for p in in_dev)))
out["pairs0139_branch_files"] = git("ls-tree", "-r", "--name-only", REFS["p0139"], "logs/sib/pairs0139").split()
out["not_checked"] = ["+16 vox same-papyrus extension of DEV hold-outs (needs meshes; list to be frozen by the orchestrator)",
                      "clean-control / READ-CAL / canary hold-outs (lists not yet published)",
                      "pairs0139, pairs0139b/c, pairs0814b registries (no final registry at check time)"]
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(json.dumps({k: out[k] for k in ("refs", "dryrun_allow_pairs0814")}, indent=1))
print(json.dumps({k: v for k, v in p0814.items() if k != "segments"}, indent=1))
