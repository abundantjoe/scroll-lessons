# Provenance: Project HERCULES | owner the owner | [id removed]
"""Plan v2 (stricter ASK defaults): levelled chain, crops clamped to the canvas with explicit cores. No inference."""
import hashlib, json
REPO = "/home/user/dominion"; L = f"{REPO}/logs/sib/reg0841/chainvalid"
SEG = {"w00": "20260220213127-w00", "214732": "20260220214732-auto_grown_20260220144552896", "022814": "20260221022814-auto_grown_20260220174252405"}
area = json.load(open(f"{L}/area_lev.json")); cl = json.load(open(f"{L}/clearance_check_lev.json")); rr = json.load(open(f"{L}/rule_r_geom_lev.json"))
lv = json.load(open(f"{L}/level_check.json")); mm = json.load(open(f"{L}/map_meshes.json"))
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def crop(k, c, H, W):
    ry, rx = max(c["y"], 0), max(c["x"], 0); ye, xe = min(c["y"] + 2048, H), min(c["x"] + 2048, W)
    core = [max(c["y"] + 128, 0), min(c["y"] + 1920, H), max(c["x"] + 128, 0), min(c["x"] + 1920, W)]
    # at the canvas border the core extends to the edge (no neighbouring crop covers it)
    if c["y"] + 128 <= 128: core[0] = 0
    if c["x"] + 128 <= 128: core[2] = 0
    if c["y"] + 2048 >= H: core[1] = H
    if c["x"] + 2048 >= W: core[3] = W
    return dict(segment=k, segment_id=SEG[k], ry=ry, rx=rx, rh=ye - ry, rw=xe - rx, core=core, core_px=c["core_px"], core_E_px=c["core_E_px"])


prim, sec = [], []
for k, v in area["segments"].items():
    H, W = v["canvas"]
    prim += [crop(k, c, H, W) for c in v["crops"] if c["core_E_px"] > 0]
    sec += [crop(k, c, H, W) for c in sorted([c for c in v["crops"] if c["core_E_px"] == 0], key=lambda c: (-c["core_px"], c["y"], c["x"]))[:2]]
TPC = 15 * 15; S_BF16, S_FP32 = 3.8, 5.1
cost = lambda cs, s: round(sum((c["rh"] // 128 - 1) * (c["rw"] // 128 - 1) for c in cs) * 2 * s / 3600, 2)
plan = dict(
    provenance="Project HERCULES | owner the owner | [id removed]", version=2, declaration="RULES.md DECL-CHAINVALID (+ -A1 pending)",
    status="PLAN ONLY. No ink map of PHerc0841 exists or will be made until the orchestrator appends the declaration and gives GO; the runner refuses without /work/cv/GO",
    stricter_defaults=dict(levelling="LEVELLED (as specified): level_mesh step 20 vox on the mapped meshes; predictions scored on the organizer canvas through the exact levelled<->organizer correspondence (level_check.json)",
                           shells="T shell only exists on 0841 (C4 = 0139/0814 clean controls, K = fold K; neither has 0841 windows); every rendered sample >= 144 vox point-to-surface from J, fail-closed",
                           precision="only a precision with which the chain2um GATE-E2E-0139 passes; if it passes in neither, no 0841 run",
                           area="bar decided on the pooled primary E (labelled px) only; secondary crops report r_org_all only",
                           reference_model="organizer map model 20260417190342 may have seen 0841 labels: result recorded as a chain check only, never as evidence of the reader",
                           go="no run without explicit GO after the declaration is appended and the chain2um gate report exists"),
    map_version=dict(field_final_sha256=h(f"{REPO}/logs/sib/reg0841na/field_final.json"), record="RULES.md REG-0841-NA"),
    meshes=dict(mapped="/work/cv/mesh (node threshold 172 vox)", levelled="/work/cv/mesh_lev",
                levelled_file_sha256={k: {a: h(f"/work/cv/mesh_lev/{k}/{a}.tif") for a in "xyz"} for k in SEG},
                level_transform={k: lv[k]["T"] for k in SEG},
                level_check={k: {x: lv[k][x] for x in ("dist_median", "dist_p99", "dist_max", "roundtrip_px_max", "edge_within_10pct")} for k in SEG},
                residual_vs_organizer_2p4_mesh={k: v["resid_vs_organizer_2p4_mesh"] for k, v in mm["segments"].items()}),
    exclusion=dict(min_clearance_vox_levelled=min(v["min_clearance"] for v in cl["segments"].values()), all_ge_144=cl["all_ge_144"],
                   method="clearance_check_lev.json: kept-node blocks (re-checked per node where a block box fails) grown by 13.2 vox (slab 8 + pixel 5.2), jsurf point-to-surface"),
    area={k: {x: v[x] for x in ("canvas", "renderable_px", "E_org_px", "E_mapped_renderable", "E_ink")} for k, v in area["segments"].items()},
    chain=dict(render="vc_render_tifxyz (villa 41701aa) --segmentation /work/cv/mesh_lev/<seg> --scale 1 --group-idx 0 --num-slices 63 --slice-step 1 --voxel-size 2.403 --voxel-unit micrometer --flip-normals --crop-x rx --crop-y ry --crop-width rw --crop-height rh",
               inference="chain2um infer2um.py verbatim (tools/sib/reg0841na/chain2um_copy, sha256 in SOURCE.txt): --start 0 --layers 62 --tile 256 --stride 128 --batch 1 --threads 4, directions reverse AND forward, checkpoint ink_canonical_2um r152_3ddec_v2_l5_epoch13.ckpt sha256 36dd0de8...",
               scoring="cv_eval_lev.py (tests/sib_reg0841_cv_eval_lev_test.py)"),
    crops_primary=prim, crops_secondary=sec,
    rule_R=dict(n_render_dot_r_out_median={k: v["median_n_dot_rout"] for k, v in rr["segments"].items()}, frac_positive={k: v["frac_positive"] for k, v in rr["segments"].items()},
                label_crops=rr["segments"]["214732"]["label_crops"], note="render normal points toward the umbilicus proxy (mask centroid); rule R = (sign -, winning order) once run"),
    compute=dict(s_per_tile_bf16=S_BF16, s_per_tile_fp32=S_FP32, primary_h_bf16=cost(prim, S_BF16), primary_h_fp32=cost(prim, S_FP32),
                 secondary_h_bf16=cost(sec, S_BF16), secondary_h_fp32=cost(sec, S_FP32), render_s_per_2048_crop=52,
                 note="both orders; upper bounds (empty batches skipped); timings from 2 synthetic tiles and one CT render"),
    runner="tools/sib/reg0841/chainvalid/run_chainvalid_lev.sh primary|secondary PRECISION (refuses without /work/cv/GO)")
json.dump(plan, open(f"{L}/chainvalid_plan_levelled_alt.json", "w"), indent=1)
print(json.dumps(plan["compute"]), [(c["segment"], c["ry"], c["rx"], c["rh"], c["rw"], c["core"], c["core_E_px"]) for c in prim])
