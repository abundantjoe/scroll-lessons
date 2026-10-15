# Provenance: Project HERCULES | owner the owner | [id removed]
"""Record the synthetic glyph correlation scores (numbers only) as JSON."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests"))
import sib_handed_synthetic as t  # noqa: E402

out = {"method": "TM_CCOEFF_NORMED max of the flattened mean(-2..+2) render vs glyph template and its mirrors; "
                 "rule = convention parity from metadata, up from z flag, r_out from CT-mask centroid", "cases": []}
for ch in "RK":
    g = t.S.font_glyph(ch)
    sc = t.S.spiral_glyph_volume(t.SHAPE, t.spiral(), g, k_glyph=t.K_G, phi_g=t.PHI_G, z_c=t.Z_C, pix=t.PIX)
    for kind in t.KINDS:
        for pf in ["none", "u", "v", "uv"]:
            src = t.source_grid(sc)
            if "u" in pf:
                src = src[:, ::-1].copy()
            if "v" in pf:
                src = src[::-1].copy()
            vol, pts, props = t.S.transform_scene(sc.vol, src, kind)
            for override in (None, "wrong"):
                fi = t.H.frame_info(t.S.ZATTRS_ZYX, props)
                sign = None if override is None else -t.H.predicted_convention(fi)
                img, o, _ = t.rule_render(vol, pts, props, override_sign=sign)
                s = t.mirror_scores(img, g)
                out["cases"].append(dict(glyph=ch, frame=kind, props=props, param_flip=pf,
                                         sign_used=o.chirality_after, rule=(override is None),
                                         flip_u=o.flip_u, flip_v=o.flip_v, scores={k: round(v, 4) for k, v in s.items()},
                                         unmirrored=bool(s["id"] > s["lr"] + 0.2)))
rule = [c for c in out["cases"] if c["rule"]]
wrong = [c for c in out["cases"] if not c["rule"]]
out["summary"] = dict(n_rule=len(rule), rule_unmirrored=sum(c["unmirrored"] for c in rule),
                      rule_min_id=min(c["scores"]["id"] for c in rule),
                      rule_min_margin_lr=min(c["scores"]["id"] - c["scores"]["lr"] for c in rule),
                      n_wrong_sign=len(wrong), wrong_sign_mirrored=sum(c["scores"]["lr"] > c["scores"]["id"] + 0.2 for c in wrong))
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
print(json.dumps(out["summary"]))
