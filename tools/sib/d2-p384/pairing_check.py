# Provenance: Project HERCULES | owner the owner | [id removed]
"""Pairing and hold-out check of the pinned trainer (8475920) against logs/sib/trainer/PAIR_FREEZE_SPEC.md
(trainer branch 08d7e42). SYNTHETIC only, no training step. (1) make-config for P384 / NULL / REV with identical
flags and one synthetic tilegrid-free pairs source: the configs must differ only in arm / null / rev. (2) the
tilegrid allowlist order (hold-outs before the 3 x 3 block completeness test) and the adapters the spec names are
checked in the source text. Writes logs/sib/d2-p384/pairing_check.json."""
import hashlib, inspect, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TD = os.path.join(HERE, "trainer")
sys.path.insert(0, TD)
import d2_data  # noqa: E402
PY, W = "/opt/hv-ink/bin/python", "/work/d2/pairing"
os.makedirs(W, exist_ok=True)
reg = "/work/d2/smoke/syn560/registry.json"
allow = os.path.join(W, "allow.json")
json.dump([f"synthetic-{i:06d}" for i in range(40) if i % 7], open(allow, "w"))
cfgs = {}
for arm in ("P384", "NULL", "REV"):
    p = os.path.join(W, f"{arm}.json")
    subprocess.run([PY, os.path.join(TD, "d2_train.py"), "make-config", "--arm", arm, "--seed", "1", "--batch", "32",
                    "--micro-batch", "4", "--steps", "12000", "--forward", "full", "--threads", "4", "--subtile",
                    "--source", f"syn=pairs:{reg}", "--allow-ids", f"syn={allow}", "--hash-sources", "--out", p],
                   check=True, capture_output=True)
    cfgs[arm] = json.load(open(p))
def flat(d, pre=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flat(v, pre + k + "."))
        else:
            out[pre + k] = v
    return out
f = {a: flat(c) for a, c in cfgs.items()}
diffs = {a: sorted(k for k in set(f["P384"]) | set(f[a]) if f["P384"].get(k) != f[a].get(k)) for a in ("NULL", "REV")}
lt = inspect.getsource(d2_data.load_tilegrid)
ls = inspect.getsource(d2_data.load_source)
srcs = [s for s in cfgs["P384"]["sources"]]
res = dict(
    provenance="Provenance: Project HERCULES | owner the owner | [id removed]", data="SYNTHETIC",
    trainer_d2_train_sha256=hashlib.sha256(open(os.path.join(TD, "d2_train.py"), "rb").read()).hexdigest(),
    config_fields_differing_from_P384=diffs,
    paired=all(set(v) <= {"arm", "null", "rev"} for v in diffs.values()),
    allow_ids_pinned_in_config=dict(path=srcs[0].get("allow_ids") is not None, sha256=srcs[0].get("allow_ids_sha256")),
    allow_ids_applied_by_pairs_kind="allow_ids" in inspect.getsource(d2_data.load_pairs_registry)
    if hasattr(d2_data, "load_pairs_registry") else None,
    tilegrid_holdouts_before_block_test=lt.index("kept = [r for r in kept if r[\"tile_id\"] in keep]") < lt.index("if any(c is None"),
    adapters_in_pinned=[k for k in ("tilegrid3", "blockpairs", "stagec", "pairs") if f'"{k}"' in ls],
    spec_kinds_missing_in_pinned=[k for k in ("tilegrid3", "blockpairs", "stagec") if f'"{k}"' not in ls],
    stagec_data_root_supported="data_root" in inspect.getsource(d2_data),
)
json.dump(res, open(os.path.join(HERE, "..", "..", "..", "logs", "sib", "d2-p384", "pairing_check.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
