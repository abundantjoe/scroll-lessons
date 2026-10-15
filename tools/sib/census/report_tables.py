# Provenance: Project HERCULES | owner the owner | [id removed]
"""Print the markdown tables of REPORT.md from logs/sib/census/census.json."""
import json

import numpy as np

c = json.load(open("logs/sib/census/census.json"))
V = c["volumes"]
G = 1e9


def gb(b):
    return f"{b / G:.2f}"


print("### Products (m7 prediction, normal grids, lasagna, umbilicus)\n")
print("| Vol | volume id | vox um | shape z,y,x | m7 GB (6 levels) | NG total GB | NG xy / xz / yz GB | NG previews GB | lasagna | umbilicus |")
print("|---|---|---|---|---|---|---|---|---|---|")
for k, v in V.items():
    pl = v["ngrid_planes"]
    prev = sum(d["bytes"] for n, d in v["ngrid_preview_dirs"].items() if n.endswith("_img"))
    las = "yes" if any(l["same_volume"] for l in v["lasagna"]) else "no"
    um = "official (%d pts)" % v["umbilicus"][0]["n_points"] if v["umbilicus"] else "none"
    print(f"| {k} | {v['volume_id']} | {v['voxel_um']:.3f} | {','.join(map(str, v['shape_zyx']))} | {gb(v['m7_bytes_total'])} | "
          f"{gb(v['ngrid_bytes_total'])} | {gb(pl['xy']['bytes'])} / {gb(pl['xz']['bytes'])} / {gb(pl['yz']['bytes'])} | {gb(prev)} | {las} | {um} |")

print("\n### Normal-grid xy bytes per 500-slice z band\n")
print("| Vol | bands | median MB | min MB | max MB | mean xz file MB | mean yz file MB |")
print("|---|---|---|---|---|---|---|")
for k, v in V.items():
    b = np.array([x["xy_bytes"] for x in v["xy_bytes_per_500_band"]], float)
    full = b[:-1] if len(b) > 1 else b
    pl = v["ngrid_planes"]
    print(f"| {k} | {len(b)} | {np.median(full) / 1e6:.0f} | {full.min() / 1e6:.0f} | {full.max() / 1e6:.0f} | "
          f"{pl['xz']['mean_file_bytes'] / 1e6:.3f} | {pl['yz']['mean_file_bytes'] / 1e6:.3f} |")

print("\n### Axis direction and CT-mask shape (level 4)\n")
print("| Vol | acquisition z | root catalogue top-to-bottom | scroll z extent (vox) | axis ratio med / p10 | solidity med / p10 | r_eq med (vox) | centre source | centroid flag |")
print("|---|---|---|---|---|---|---|---|---|")
for k, v in V.items():
    m, ax = v["mask"], v["axis"]
    cs = "umbilicus" if v["umbilicus"] else "mask centroid"
    flag = "n/a (umbilicus)" if v["umbilicus"] else ("UNRELIABLE" if (m["axis_ratio_median"] < 0.65 or m["solidity_p10"] < 0.85) else "caution")
    print(f"| {k} | {ax['acquisition_z']} ({ax['z_start_mm']} -> {ax['z_end_mm']} mm) | {ax['root_catalogue_z_direction_is_top_to_bottom']} | "
          f"{m['scroll_z_extent_vox'][0]:.0f}-{m['scroll_z_extent_vox'][1]:.0f} | {m['axis_ratio_median']:.2f} / {m['axis_ratio_p10']:.2f} | "
          f"{m['solidity_median']:.2f} / {m['solidity_p10']:.2f} | {m['r_eq_median_vox']:.0f} | {cs} | {flag} |")

print("\n### Seeds\n")
print("| Vol | placed / 60 | all checks pass | snap vox p50 / p90 / max | nudged | f at seed (min-max) | pairs in reach 45 / 75 gen | v2 SAME / DIFF / UNDET (45) | v2 SAME / DIFF / UNDET (75) | upper bound share 45 / 75 |")
print("|---|---|---|---|---|---|---|---|---|---|")
for k, v in V.items():
    s = v.get("seeds")
    if not s:
        print(f"| {k} | not run | | | | | | | | |")
        continue
    d45, d75 = s["duplicates"]["45"], s["duplicates"]["75"]
    ub = lambda d: d["pairs_in_reach"] / d["all_pairs"]
    print(f"| {k} | {s['placed']} | {s['all_checks_pass']} | {s['snap_vox_p50']:.1f} / {s['snap_vox_p90']:.1f} / {s['snap_vox_max']:.1f} | "
          f"{s['nudged_fraction']} | {s['f_seed_range'][0]:.2f}-{s['f_seed_range'][1]:.2f} | {d45['pairs_in_reach']} / {d75['pairs_in_reach']} | "
          f"{d45['same']} / {d45['different']} / {d45['undetermined']} | {d75['same']} / {d75['different']} / {d75['undetermined']} | "
          f"{ub(d45):.3f} / {ub(d75):.3f} |")

print("\n### Sync plan and time per seed\n")
print("| Vol | per-seed upper GB (median, 45 / 75 gen) | per-seed typical GB (median, 45 / 75) | union 60 seeds GB (45 / 75) | full xy+xz+yz GB | s/seed 45 / 75 (archive-scaled, 1 thread) | 60 seeds h at 4 parallel (45 / 75) |")
print("|---|---|---|---|---|---|---|")
for k, v in V.items():
    y = v.get("sync")
    if not y:
        continue
    a, b = y["45"], y["75"]
    print(f"| {k} | {a['per_seed_upper_bytes']['median'] / G:.2f} / {b['per_seed_upper_bytes']['median'] / G:.2f} | "
          f"{a['per_seed_typical_bytes']['median'] / G:.2f} / {b['per_seed_typical_bytes']['median'] / G:.2f} | "
          f"{a['union_60_seeds_bytes'] / G:.2f} / {b['union_60_seeds_bytes'] / G:.2f} | {a['full_planes_bytes'] / G:.2f} | "
          f"{a['time_per_seed_s_archive_scaled']:.0f} / {b['time_per_seed_s_archive_scaled']:.0f} | "
          f"{a['time_60_seeds_4parallel_h']:.2f} / {b['time_60_seeds_4parallel_h']:.2f} |")

print("\n### Ranking\n")
print("| Final rank | Vol | score | shape | crushing | centre | data | seeding | raw rank | rescan |")
print("|---|---|---|---|---|---|---|---|---|---|")
for r in c["ranking"]:
    print(f"| {r['rank_final']} | {r['vol']} | {r['score']:.3f} | {r['shape']:.2f} | {r['crushing']:.2f} | {r['centre']:.2f} | "
          f"{r['data']:.2f} | {r['seeding']:.2f} | {r['rank_raw']} | {'yes' if r['rescan'] else 'no'} |")
