# Provenance: Project HERCULES | owner the owner | [id removed]
"""Write logs/sib/reg0841/chainvalid_plan.json: exact area, crop list, compute plan (no inference is run here)."""
import hashlib, json
REPO = "/home/user/dominion"; L = f"{REPO}/logs/sib/reg0841/chainvalid"
area = json.load(open(f"{L}/area.json")); mm = json.load(open(f"{L}/map_meshes.json")); cl = json.load(open(f"{L}/clearance_check.json"))
rr = json.load(open(f"{L}/rule_r_geom.json"))
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
primary, secondary = [], []
for k, v in area["segments"].items():
    lab = [c for c in v["crops"] if c["core_sup_px"] > 0]
    primary += [dict(segment=k, y=c["y"], x=c["x"], core_px=c["core_px"], core_sup_px=c["core_sup_px"]) for c in lab]
    rest = sorted([c for c in v["crops"] if c["core_sup_px"] == 0], key=lambda c: (-c["core_px"], c["y"], c["x"]))[:2]
    secondary += [dict(segment=k, y=c["y"], x=c["x"], core_px=c["core_px"], core_sup_px=0) for c in rest]
TPC = 15 * 15  # 256 px tiles, stride 128, in a 2048 px crop
S_BF16, S_FP32, S_RENDER = 3.8, 5.1, 52
def cost(n, s): return round(n * TPC * 2 * s / 3600, 2)
plan = dict(
    provenance="Project HERCULES | owner the owner | [id removed]", declaration="RULES.md DECL-CHAINVALID",
    status="PLAN ONLY: no 0841 inference has run; step 2 waits for the chain2um GATE-E2E-0139 report and the orchestrator's GO",
    map_version=dict(field_final_sha256=h(f"{REPO}/logs/sib/reg0841na/field_final.json"), record="RULES.md REG-0841-NA"),
    meshes=dict(source="organizer 9.366 um tifxyz (-on-20250821151531) mapped with field_final on the organizer 2.4 um UV grid",
                node_threshold_vox=172, residual_vs_organizer_2p4_mesh={k: v["resid_vs_organizer_2p4_mesh"] for k, v in mm["segments"].items()},
                mesh_file_sha256={k: {a: h(f"/work/cv/mesh/{k}/{a}.tif") for a in "xyz"} for k in mm["segments"]}),
    exclusion=dict(rule="every rendered/inferred sample >= 144 vox point-to-surface from every J mesh point (T shell 128 + slab margin, DECL-D3-A2, CORR-RETRACE-RULE)",
                   check="clearance_check.json (fail-closed, per node where blocks fail)", min_clearance_vox=min(v["min_clearance"] for v in cl["segments"].values()),
                   all_ge_144=cl["all_ge_144"], other_shells="C4 and K shells: none defined on 0841 in RULES.md as far as found (ASK 2)"),
    area={k: {kk: v[kk] for kk in ("renderable_px", "renderable_cm2", "sup_in_R", "ink_in_R", "blank_in_R", "sup_in_R_cm2", "renderable_sha256")} for k, v in area["segments"].items()},
    chain=dict(render="official vc_render_tifxyz (villa 41701aa, /work/bin/vc), --scale 1 --num-slices 63 --slice-step 1 --flip-normals, crop 2048 x 2048, volume 20260319124803-2.403um-0.2m-77keV-masked.zarr",
               inference="tools/sib/chain2um/infer2um.py (verbatim copy, sha256 in tools/sib/reg0841na/chain2um_copy/SOURCE.txt): ink_canonical_2um r152_3ddec_v2_l5_epoch13.ckpt (sha256 36dd0de8...), --start 0 --layers 62 --tile 256 --stride 128, Hann (official), clip 0..200; orders reverse AND forward",
               precision="same as the chain2um gate run that passes (ASK 3; default bf16 = the official CPU autocast path)",
               levelling="none: render on the organizer UV canvas so pixels align with the organizer map and labels (ASK 1)"),
    crops_primary=primary, crops_secondary=secondary,
    metrics="tools/sib/reg0841/chainvalid/cv_eval.py: AUC vs labels and r_org_E on E = renderable & supervision; r_org_all on all renderable px of evaluated cores; bar on pooled E: one order r_org_E >= 0.60 and AUC >= 0.90, other order AUC <= 0.60",
    rule_R=dict(geometry="n_render (--flip-normals) . r_out < 0 on 98 % of nodes (all 3 segments) and 100 % in both label crops: the render normal points toward the umbilicus proxy", per_segment={k: v["median_n_dot_rout"] for k, v in rr["segments"].items()},
                record="rule R on 0841 = (sign -, winning order) once the run exists"),
    compute=dict(tiles_per_crop_per_order=TPC, s_per_tile_bf16=S_BF16, s_per_tile_fp32=S_FP32, s_render_per_crop=S_RENDER,
                 primary_h_bf16=cost(len(primary), S_BF16), primary_h_fp32=cost(len(primary), S_FP32),
                 secondary_h_bf16=cost(len(secondary), S_BF16), secondary_h_fp32=cost(len(secondary), S_FP32),
                 all_crops_h_bf16=cost(sum(v["n_crops"] for v in area["segments"].values()), S_BF16),
                 note="upper bounds: all-empty tile batches are skipped by the official code; timings from 2 synthetic tiles and one 2048 px render; 4 threads; disk per crop render ~200 MB, deleted after both orders"),
    runner="tools/sib/reg0841/chainvalid/run_chainvalid.sh (refuses to start unless /work/cv/GO exists)")
json.dump(plan, open(f"{REPO}/logs/sib/reg0841/chainvalid_plan.json", "w"), indent=1)
print(json.dumps(plan["compute"]), len(primary), len(secondary), [(c["segment"], c["y"], c["x"]) for c in primary])
