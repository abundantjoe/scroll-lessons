# Provenance: Project HERCULES | [id removed]
"""Tile one GP piece prediction with the unchanged FL-2 piece tiler (fl2_pieces.tile), then relabel that call's rows:
model GP_timesformer, model_sha256, variant, attribution. Usage: gp_tile.py SEG SEGDIR PLAN PIECE PRED DIR OUTDIR MANIFEST VOLID MEASURE VARIANT"""
import sys, json, importlib.util
spec = importlib.util.spec_from_file_location("fl2p", "tools/sib/pairs0139c/fl2_pieces.py"); P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
a = sys.argv[1:]; variant = a[10]; man = a[7]
GPSHA = "490a98f9491e1180274ed3a0c0a9c611d73a0109c0e0c0fbba1097562a972488"
P.tile(*a[:10])
m = json.load(open(man)); pid = int(a[3])
for t in m["tiles"]:
    if t["piece"]["id"] == pid and t["direction"] == a[5]:
        t.update(model="GP_timesformer", model_sha256=GPSHA, variant=variant)
m.update(decl="DECL-FL-4 gate (held-out PHerc0139, pieces per DECL-FL-2-E3)",
         model="GP_timesformer: 2023 Grand Prize TimeSformer by Youssef Nader for the Grand Prize team (MIT), organizer copy HF scrollprize/timesformer_GP_scroll1 @61b81d31, run via villa 41701aa ink-detection/optimized_inference",
         chain=f"C2-NT render pieces (vc_render_tifxyz -n 31 --flip-normals --crop-*); GP layers 2..27 of 31; variant {variant}; window 64 stride 32 fp32 (autocast off); Hann blend; sigmoid -> 0-255")
json.dump(m, open(man, "w"), indent=1)
