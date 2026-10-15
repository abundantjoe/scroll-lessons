#!/usr/bin/env python
"""rsym.py -- RULES R-SYM: is the reverse map a copy of the forward map?

Statistic: Pearson r(forward, reverse) over the pixels of the rule 5.5 VALID 0.5 cm2 units, which are
>= 90 % on-sheet by construction and whose boxes are already recorded in every read_stats.json.
The same definition is applied to the Gate B control and to every corpus read, with no exception.

Bars are in RULES.md R-SYM and are not repeated as tunables here: control anchor r <= 0.30 (else the
statistic is unusable and nothing follows), DEPTH-SYMMETRIC at r >= 0.70, nomination at r < 0.30.
This script measures and prints. It alters no map, no verdict and no bar.
"""
import argparse, glob, json, os, sys
import numpy as np
import tifffile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rule55
DATA = os.environ.get("HERCULES_DATA", "/home/user/hercules_data")  # data root; override with $HERCULES_DATA

CONTROL_ANCHOR = 0.30
SYM_AT = 0.70
NOMINATE_BELOW = 0.30


def pearson(a, b):
    a = a.astype(np.float64); b = b.astype(np.float64)
    a = a - a.mean(); b = b - b.mean()
    da, db = np.sqrt((a * a).sum()), np.sqrt((b * b).sum())
    if da == 0 or db == 0:
        return float("nan")
    return float((a * b).sum() / (da * db))


def unit_pixels(fwd, rev, units, side, origin):
    """Concatenated forward/reverse pixel vectors over every valid unit box."""
    oy, ox = origin
    fs, rs = [], []
    for u in units:
        y0, x0 = oy + u["row"] * side, ox + u["col"] * side
        fs.append(fwd[y0:y0 + side, x0:x0 + side].ravel())
        rs.append(rev[y0:y0 + side, x0:x0 + side].ravel())
    if not fs:
        return None, None
    return np.concatenate(fs), np.concatenate(rs)


def read_one(stats_path):
    d = json.load(open(stats_path))
    r55 = d.get("rule55") or {}
    tab = (r55.get("units") or r55).get("0.5cm2")
    if not tab:
        return None, "no 0.5 cm2 table"
    units = [u for u in tab.get("valid_units", [])]
    if not units:
        return None, "no valid unit"
    fwd_p = d["inputs"]["forward"]; rev_p = d["inputs"]["reverse"]
    if not (os.path.exists(fwd_p) and os.path.exists(rev_p)):
        return None, "maps pruned"
    fwd = tifffile.imread(fwd_p); rev = tifffile.imread(rev_p)
    if fwd.shape != rev.shape:
        return None, "shape mismatch"
    side = int(tab["side_px"]); origin = tuple(tab.get("origin", (0, 0)))
    f, r = unit_pixels(fwd, rev, units, side, origin)
    if f is None:
        return None, "no unit pixels"
    return dict(key=d.get("key", stats_path), verdict=d.get("verdict"), n_units=len(units),
                onsheet_cm2=d.get("onsheet_cm2"), fwd_mean=d.get("maps", {}).get("fwd_mean"),
                rev_mean=d.get("maps", {}).get("rev_mean"), r=pearson(f, r),
                n_px=int(f.size), path=stats_path), None


def control(gate_dir, um):
    """Gate B: our own render of the w040 known-text mesh crop, plain seed42, both orders, identical treatment."""
    import zarr
    fwd = tifffile.imread(os.path.join(gate_dir, "render_plain.tif"))
    rev = tifffile.imread(os.path.join(gate_dir, "render_plain_reverse.tif"))
    g = zarr.open_group(os.path.join(gate_dir, "render.zarr"), mode="r")
    a = g["0"]
    ct = np.asarray(a[a.shape[0] // 2])
    onsheet = ct > 0
    side = rule55.unit_side(um)
    origin, _ = rule55.best_origin(onsheet, side)
    res, _ = rule55.evaluate(fwd, rev, onsheet, um, unit_origin=origin)
    tab = (res.get("units") or res)["0.5cm2"]
    units = tab.get("valid_units", [])
    f, r = unit_pixels(fwd, rev, units, int(tab["side_px"]), tuple(tab.get("origin", (0, 0))))
    whole = pearson(fwd[onsheet], rev[onsheet])
    return dict(n_units=len(units), r_units=(pearson(f, r) if f is not None else float("nan")),
                r_whole_onsheet=whole, onsheet_px=int(onsheet.sum()),
                n_px=(int(f.size) if f is not None else 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patches", default=DATA + "/patches")
    ap.add_argument("--gateb", default=DATA + "/gates/gateB")
    ap.add_argument("--um", type=float, default=9.362)
    ap.add_argument("--out", default=DATA + "/gates/rsym/rsym.json")
    a = ap.parse_args()

    ctl = control(a.gateb, a.um)
    print("== CONTROL (Gate B, w040 known text, our own render) ==")
    print("  valid units %d over %d px: r(fwd,rev) = %.4f   [anchor: must be <= %.2f]"
          % (ctl["n_units"], ctl["n_px"], ctl["r_units"], CONTROL_ANCHOR))
    print("  whole on-sheet (%d px): r = %.4f" % (ctl["onsheet_px"], ctl["r_whole_onsheet"]))
    usable = ctl["r_units"] <= CONTROL_ANCHOR
    print("  anchor %s" % ("HOLDS - R-SYM is usable" if usable else "FAILS - R-SYM is an UNUSABLE INDICATOR"))

    rows, excluded = [], {}
    for sp in sorted(glob.glob(os.path.join(a.patches, "*", "*", "read_*", "read_stats.json"))):
        row, why = read_one(sp)
        if row is None:
            excluded[why] = excluded.get(why, 0) + 1
        else:
            rows.append(row)
    rows.sort(key=lambda x: x["r"])
    print("\n== CORPUS: %d reads measured, %d excluded (%s) =="
          % (len(rows), sum(excluded.values()), ", ".join("%s %d" % kv for kv in sorted(excluded.items()))))
    print("%-62s %5s %8s %8s %7s  %s" % ("read", "units", "fwd", "rev", "r", "verdict"))
    for x in rows:
        print("%-62s %5d %8.4f %8.4f %7.4f  %s"
              % (x["key"].split("|")[1][:62], x["n_units"], x["fwd_mean"] or float("nan"),
                 x["rev_mean"] or float("nan"), x["r"], x["verdict"]))
    if rows:
        rr = np.array([x["r"] for x in rows])
        sym = int((rr >= SYM_AT).sum())
        nom = [x for x in rows if x["r"] < NOMINATE_BELOW]
        print("\n  median r %.4f   min %.4f   max %.4f" % (float(np.median(rr)), rr.min(), rr.max()))
        print("  DEPTH-SYMMETRIC (r >= %.2f): %d of %d = %.1f %%" % (SYM_AT, sym, len(rows), 100.0 * sym / len(rows)))
        print("  nominated (r < %.2f): %d%s" % (NOMINATE_BELOW, len(nom),
              ("  -> " + ", ".join(x["key"] for x in nom)) if nom else ""))
        if not usable:
            print("\n  CONTROL ANCHOR FAILED: the corpus numbers above are reported for the record and gate NOTHING.")
        elif len(nom) == 0 and sym >= 0.90 * len(rows):
            print("\n  OUTCOME DS-ALL.")
        else:
            print("\n  OUTCOME DS-SPLIT." if nom else "\n  OUTCOME: neither DS-ALL nor DS-SPLIT as declared.")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(dict(control=ctl, control_anchor=CONTROL_ANCHOR, usable=bool(usable), sym_at=SYM_AT,
                   nominate_below=NOMINATE_BELOW, reads=rows, excluded=excluded), open(a.out, "w"), indent=1)
    print("\nwrote %s" % a.out)


if __name__ == "__main__":
    main()
