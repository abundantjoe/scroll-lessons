# Provenance: Project HERCULES | owner the owner | [id removed]
"""Print the FLAT-1 per-mesh metric table (markdown) from flat1_results*.json."""
import json, sys
R = json.load(open(sys.argv[1]))["results"]
cols = ("vc_flatten", "slim", "arap", "grid_baseline", "vc_flatten_lscm_only")
print("| mesh | method | quads within 5 % | within 1 % | raw 5 % | area x | |log area| (w) | area within 5 % (tri %) | angle err mean / p99 (deg) | sigma1/sigma2 p99 | flipped | undefined uv | s |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in R:
    tag = r["segment"].split("-")[1].split("_")[0]
    for m in cols:
        x = r["methods"][m]["metrics"]
        print(f"| {tag} | {m} | {x['pct_quads_within_5pct']:.2f} | {x['pct_quads_within_1pct']:.2f} | {x['pct_quads_within_5pct_raw']:.2f} | "
              f"{x['area_scale_factor']:.4f} | {x['area_ratio']['weighted_mean_abs_log']:.4f} | {x['area_ratio']['pct_tri_within_5pct']:.2f} | "
              f"{x['angle_abs_err_deg']['mean']:.3f} / {x['angle_abs_err_deg']['p99']:.3f} | {x['conformal_sigma_ratio']['p99']:.4f} | "
              f"{x['flipped_triangles']} | {x['n_triangles_uv_undefined']} | {r['methods'][m]['info']['seconds']:.1f} |")
print()
print("| mesh | quads (h x w) | area cm^2 | aspect | iso-z tilt deg | sum angle defect rad | mean abs defect deg | fallback R-only -> margin -> trimmed (% within 5 %) | trim rounds |")
print("|---|---|---|---|---|---|---|---|---|")
for r in R:
    tag = r["segment"].split("-")[1].split("_")[0]
    g, q, f = r["geometry"], r["rect"], r["fallback"]
    print(f"| {tag} | {q['h_quads']} x {q['w_quads']} | {q['area_cm2']:.3f} | {q['aspect']:.3f} | {g['iso_z_tilt_deg']:.2f} | "
          f"{g['sum_angle_defect_rad']:.4f} | {g['mean_abs_angle_defect_deg']:.3f} | {f['R_only_slim_pct']:.2f} -> {f['before_pct']:.2f} -> {f['after_pct']:.2f} | {len(f['rounds'])-1} |")
