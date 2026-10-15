# Provenance: Project HERCULES | owner the owner | [id removed]
"""Project chain2um CPU cost per cm^2 from measured pass summaries (numbers only).
Tiles per cm^2 per order at stride s px and pixel p um (interior asymptote): (1e4 / (p * s))^2.
Usage: project2um.py out.json name=summary.json [...]"""
import json, sys

PX_UM, STRIDE, CORES = 2.399, 128, 4
TPC = (1e4 / (PX_UM * STRIDE)) ** 2
RENDER_S, RENDER_CM2, RENDER_CPUS = 98.0, 0.28005084315648, 3  # runs.jsonl render_w043_n63 (docker --cpus 3)

out = dict(pixel_um=PX_UM, stride_px=STRIDE, tile_px=256, layers=62, tiles_per_cm2_per_order=TPC,
           host='Intel Xeon model 85 @2.80GHz, 4 vCPU, avx512_vnni, NO amx, NO avx512_bf16 (host_cpu.txt)',
           render=dict(wall_s_per_cm2=RENDER_S / RENDER_CM2, wall_h_per_cm2=RENDER_S / RENDER_CM2 / 3600,
                       note='vc_render_tifxyz -n 63 streaming S3, docker --cpus 3; includes S3 fetch'),
           passes={})
for spec in sys.argv[2:]:
    name, p = spec.split('=', 1)
    s = json.load(open(p))
    spt = s['s_per_tile_wall']
    one = TPC * spt / 3600
    out['passes'][name] = dict(tiles=s['tiles'], s_per_tile_wall=spt, s_per_tile_forward=s['s_per_tile_forward'],
                               wall_h_per_cm2_one_order=one, core_h_per_cm2_one_order=one * CORES,
                               wall_h_per_cm2_both_orders=2 * one, core_h_per_cm2_both_orders=2 * one * CORES)
# Reference only (NOT measured in this task): docker/TOOLING.md section 5, AMX host, 3 threads, random weights.
out['reference_amx_host_tooling_md'] = {k: dict(s_per_tile=v, wall_h_per_cm2_one_order=TPC * v / 3600,
                                                core_h_per_cm2_one_order=TPC * v / 3600 * 3)
                                        for k, v in (('bf16_3thr', 5.25), ('fp32_3thr', 8.0))}
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(json.dumps(out, indent=1))
