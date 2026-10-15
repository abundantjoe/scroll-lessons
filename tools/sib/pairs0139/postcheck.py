# Provenance: Project HERCULES | owner the owner | [id removed]
"""Re-validate segments built before the CORR-RETRACE-RULE re-check (exclusion_v2.json, nearE2/): a kept tile is
dropped if its segment is now excluded or any of its pixels is a v2 Rule-S pixel. Affected shards are rewritten
(tiles removed, sha256 re-recorded); every dropped tile stays in the registry with kept = false and
dropped_by = "CORR-RETRACE-RULE". Numbers only. Usage: postcheck.py SHORT..."""
import hashlib, json, os, sys
import numpy as np

OUT = "/work/p139/out"


def main():
    ex = json.load(open("/work/p139/exclusion_v2.json"))
    rep = {}
    for sh in sys.argv[1:]:
        reg = f"{OUT}/registry/{sh}.jsonl"
        rows = [json.loads(l) for l in open(reg)]
        seg = rows[0]["segment"]
        excluded = sh in ex["E"]
        mp = f"/work/p139/nearE2/{seg}.npz"
        mask = None
        if os.path.exists(mp):
            z = np.load(mp); s = tuple(z["shape"])
            mask = np.unpackbits(z["packed"])[:s[0] * s[1]].reshape(s).astype(bool)
        drop = set()
        for r in rows:
            if not r["kept"]:
                continue
            y, x, T = r["canvas9_y0"], r["canvas9_x0"], r["size"]
            if excluded or (mask is not None and mask[y:y + T, x:x + T].any()):
                drop.add(r["tile_id"])
        if drop:
            for name in sorted({r["shard"] for r in rows if r["kept"] and r["tile_id"] in drop}):
                p = f"{OUT}/shards/{name}"
                z = dict(np.load(p))
                keep = np.array([str(t) not in drop for t in z["tile_id"]])
                if keep.any():
                    np.savez_compressed(p, **{k: v[keep] for k, v in z.items()})
                    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
                else:
                    os.remove(p); h = None
                idx = 0
                for r in rows:
                    if r.get("shard") == name and r["kept"]:
                        if r["tile_id"] in drop:
                            r["kept"] = False; r["dropped_by"] = "CORR-RETRACE-RULE"
                            r.pop("shard_index", None); r["shard"] = None; r["shard_sha256"] = None
                        else:
                            r["shard_index"] = idx; r["shard_sha256"] = h; idx += 1
            with open(reg, "w") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            sp = f"{OUT}/registry/{sh}.summary.json"
            sm = json.load(open(sp)); sm["kept_before_postcheck"] = sm["kept"]; sm["kept"] -= len(drop)
            sm["dropped_by_corr_retrace"] = len(drop); json.dump(sm, open(sp, "w"), indent=1)
        rep[sh] = dict(segment_excluded_v2=excluded, dropped=len(drop),
                       kept_after=sum(r["kept"] for r in rows))
    print(json.dumps(rep, indent=1))
    json.dump(rep, open(f"{OUT}/postcheck.json", "w"), indent=1)


if __name__ == "__main__":
    main()
