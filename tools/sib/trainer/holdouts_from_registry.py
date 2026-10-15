# Provenance: Project HERCULES | owner the owner | [id removed]
"""Hold-out id lists from a stage-C pair_registry.json (pairs0814 layout), for the pair freeze (PAIR_FREEZE_SPEC.md).
Numbers only. The tool applies a rule; it never chooses one (the orchestrator declares the rule).
Rules:
  base_same         patch is SAME papyrus as the 46527 re-trace by CORR-RETRACE-RULE, or lies on segment 20260226000000
  base_within:<N>   patch minimum point-to-surface distance to 46527 < N vox ('>=256' counts as far), or base_same
  dedupe_groups     keep the lexicographically smallest patch_id of each duplicate group, hold out the rest
Usage: holdouts_from_registry.py <pair_registry.json> <rule> [<rule> ...] --out <dir>
Writes <dir>/holdout_<rule>.json (sorted ids) and prints counts."""
import argparse, json, os, sys

BASE_SID = "20260226000000"


def is_base_same(r):
    return bool(r.get("base_same_papyrus_46527")) or r["segment"].startswith(BASE_SID)


def apply(rule, rows):
    if rule == "base_same":
        return sorted(r["patch_id"] for r in rows if is_base_same(r))
    if rule.startswith("base_within:"):
        n = float(rule.split(":", 1)[1])
        return sorted(r["patch_id"] for r in rows if is_base_same(r) or
                      (isinstance(r.get("base_min_dist_vox"), (int, float)) and r["base_min_dist_vox"] < n))
    if rule == "dedupe_groups":
        groups = {}
        for r in rows:
            groups.setdefault(r["duplicate_group"], []).append(r["patch_id"])
        return sorted(p for ids in groups.values() for p in sorted(ids)[1:])
    raise ValueError(f"unknown rule {rule}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("registry")
    ap.add_argument("rules", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rows = json.load(open(a.registry))["patches"]
    os.makedirs(a.out, exist_ok=True)
    res = dict(registry=os.path.abspath(a.registry), n_patches=len(rows), rules={})
    for rule in a.rules:
        ids = apply(rule, rows)
        f = os.path.join(a.out, "holdout_" + rule.replace(":", "_") + ".json")
        json.dump(ids, open(f, "w"), indent=0)
        res["rules"][rule] = dict(n=len(ids), file=f)
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
