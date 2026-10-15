# Provenance: Project HERCULES | owner the owner | [id removed]
"""Pair-freeze record for D2 (logs/sib/trainer/PAIR_FREEZE_SPEC.md). Numbers and hashes only; no image is opened.

Input: a freeze request JSON (spec section 2):
  {"d2_date": "YYYY-MM-DD" | null, "decl": "DECL-D2-A1",
   "sources": [{"name", "kind": "tilegrid3" | "tilegrid" | "blockpairs" | "stagec", "branch", "commit", "path"}],
   "holdouts": [{"reason", "file": JSON list of patch/tile ids}]}
Output (spec section 3): <out>/pair_freeze.json plus <out>/allow_<name>.json per source (the ids each arm config
consumes via make-config --allow-ids name=<file>). Every file that enters training is hashed; per-source counts are
taken from the registry rows (candidates, gated, passed/kept), then after hold-outs, then (tile grids) in/out of
complete 3 x 3 blocks. --verify additionally loads every source through d2_data (sha256 + label-rule checks) and
records the loaded patch counts and label pixel totals."""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d2_data  # noqa: E402

PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"
SCHEMA = "hercules-d2-pair-freeze/1"


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def rows_of(path):
    rows, files = [], {}
    for f in sorted(glob.glob(os.path.join(path, "registry", "*.jsonl"))):
        files[os.path.relpath(f, path)] = d2_data.sha256_file(f)
        rows += [json.loads(l) for l in open(f) if l.strip()]
    return rows, files


def tilegrid_blocks(ids_pos: dict, k: int, t: int = 128):
    """ids_pos {tile_id: (segment, y0, x0)} -> (tiles in complete grid-aligned k x k blocks, n_blocks)."""
    have = {v: i for i, v in ids_pos.items()}
    inside, nblk = set(), 0
    for (sg, y0, x0) in sorted(have):
        if y0 % (k * t) or x0 % (k * t):
            continue
        blk = [(sg, y0 + a * t, x0 + b * t) for a in range(k) for b in range(k)]
        if all(p in have for p in blk):
            nblk += 1
            inside.update(have[p] for p in blk)
    return inside, nblk


def freeze_source(src: dict, held: set, out_dir: str, verify: bool) -> dict:
    kind, path = src["kind"], src["path"]
    rows, reg_files = rows_of(path) if kind != "stagec" else ([], {})
    rec = dict(name=src["name"], kind=kind, branch=src.get("branch"), commit=src.get("commit"),
               path=os.path.abspath(path), registry_files_sha256=reg_files)
    data_files = {}
    if kind.startswith("tilegrid"):
        k = {"tilegrid": 1, "tilegrid3": 3, "tilegrid4": 4}[kind]
        kept = [r for r in rows if r.get("shard")]
        for r in kept:
            data_files["shards/" + r["shard"]] = r["shard_sha256"]
        ids = {r["tile_id"]: (r["segment"], int(r["canvas9_y0"]), int(r["canvas9_x0"])) for r in kept}
        after = {i: p for i, p in ids.items() if i not in held}
        inside, nblk = tilegrid_blocks(after, k, int(kept[0]["size"]) if kept else 128) if k > 1 else (set(after), None)
        allow = sorted(inside)
        rec["counts"] = dict(candidates=len(rows), kept=len(kept), held_out=len(ids) - len(after),
                             after_holdouts=len(after), in_block=len(inside), out_of_block=len(after) - len(inside),
                             blocks=nblk, mosaic=k, patches_px=(k * 128), segments=len({p[0] for p in after.values()}))
    elif kind == "blockpairs":
        passed = [r for r in rows if r.get("passed") and r.get("staged")]
        for r in passed:
            data_files[r["staged"]] = r["staged_sha256"]
        allow = sorted(r["patch_id"] for r in passed if r["patch_id"] not in held)
        rec["counts"] = dict(candidates=len(rows), gated=sum(1 for r in rows if r.get("status") == "GATED"),
                             passed=len(passed), held_out=len(passed) - len(allow), after_holdouts=len(allow),
                             patches_px=int(passed[0]["size"]) if passed else None,
                             segments=len({r["segment"] for r in passed if r["patch_id"] in set(allow)}),
                             label_px_registry=dict(ink=sum(r["n_ink"] for r in passed if r["patch_id"] not in held),
                                                    blank=sum(r["n_blank"] for r in passed if r["patch_id"] not in held),
                                                    ignore=sum(r["n_ignore"] for r in passed if r["patch_id"] not in held)))
    elif kind == "stagec":
        man = json.load(open(os.path.join(path, "shards.json")))
        rec["registry_files_sha256"] = {"shards.json": d2_data.sha256_file(os.path.join(path, "shards.json"))}
        ids = []
        droot = src.get("data_root")
        rec["data_root"] = os.path.abspath(droot) if droot else None
        for sh in man["shards"]:
            data_files[sh["shard"]] = sh["sha256"]
            ids += sh["patch_ids"]
        preg = os.path.join(path, "pair_registry.json")
        if os.path.exists(preg):
            rec["registry_files_sha256"]["pair_registry.json"] = d2_data.sha256_file(preg)
        allow = sorted(i for i in ids if i not in held)
        rec["counts"] = dict(passed=len(ids), held_out=len(ids) - len(allow), after_holdouts=len(allow))
    else:
        raise ValueError(f"unknown kind {kind}")
    def _resolve(f):
        for base in ([src["data_root"]] if src.get("data_root") else []) + [path]:
            if os.path.exists(os.path.join(base, f)):
                return os.path.join(base, f)
        return os.path.join(path, f)
    bad = {f: h for f, h in data_files.items() if d2_data.sha256_file(_resolve(f)) != h}
    if bad:
        raise ValueError(f"{src['name']}: {len(bad)} data files differ from their registry sha256: {sorted(bad)[:3]}")
    rec["data_files_sha256"] = dict(sorted(data_files.items()))
    rec["data_files_digest"] = hashlib.sha256(canonical(rec["data_files_sha256"])).hexdigest()
    af = os.path.join(out_dir, f"allow_{src['name']}.json")
    json.dump(allow, open(af, "w"), indent=0)
    rec["allow_ids"] = dict(file=os.path.abspath(af), sha256=d2_data.sha256_file(af), n=len(allow))
    if verify:
        s = d2_data.load_source(dict(kind=kind, path=path, name=src["name"], allow_ids=af,
                                     data_root=src.get("data_root")))
        rec["verified_load"] = dict(n_patches=len(s), size_px=s.size, ink_px=int(s.ink.sum()),
                                    supervised_px=int(s.sup.sum()), registry_sha256=s.registry_sha256,
                                    label_rule_mismatch_px=0)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    req = json.load(open(a.request))
    os.makedirs(a.out, exist_ok=True)
    holdouts, held = [], set()
    for h in req.get("holdouts", []):
        ids = json.load(open(h["file"]))
        holdouts.append(dict(reason=h["reason"], file=os.path.abspath(h["file"]), sha256=d2_data.sha256_file(h["file"]),
                             n=len(ids)))
        held.update(ids)
    rec = dict(provenance=PROV, schema=SCHEMA, decl=req.get("decl"), d2_date=req.get("d2_date"),
               created_utc=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               request_sha256=d2_data.sha256_file(a.request),
               label_rule=dict(ink_min=d2_data.INK_MIN, blank_max=d2_data.BLANK_MAX, rest="ignored",
                               rotated_in_pixels="ignored, never blank"),
               holdouts=holdouts, holdout_ids_total=len(held),
               sources=[freeze_source(s, held, a.out, a.verify) for s in req["sources"]])
    rec["totals"] = dict(allow_ids=sum(s["allow_ids"]["n"] for s in rec["sources"]))
    rec["data_registry_digest"] = hashlib.sha256(canonical([(s["name"], s["data_files_digest"],
                                                             s["allow_ids"]["sha256"]) for s in rec["sources"]])).hexdigest()
    rec["record_sha256"] = hashlib.sha256(canonical({k: v for k, v in rec.items() if k != "created_utc"})).hexdigest()
    p = os.path.join(a.out, "pair_freeze.json")
    json.dump(rec, open(p, "w"), indent=1, sort_keys=True)
    print(json.dumps(dict(out=p, record_sha256=rec["record_sha256"], totals=rec["totals"],
                          sources={s["name"]: s["counts"] for s in rec["sources"]})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
