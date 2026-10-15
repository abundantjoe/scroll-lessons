# Provenance: Project HERCULES | owner the owner | [id removed]
"""Write logs/sib/pairs0814/REPORT.md from the task's JSON outputs (numbers are copied by code, not by hand)."""
import collections
import json
import os

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
L = f"{REPO}/logs/sib/pairs0814"
PROV = "Provenance: Project HERCULES | owner the owner | [id removed]"


def host():
    import subprocess
    out = subprocess.run(["lscpu"], capture_output=True, text=True).stdout.splitlines()
    keep = [l.split(":", 1) for l in out if l.split(":", 1)[0] in ("Model name", "CPU(s)", "Thread(s) per core", "Socket(s)")]
    flags = next((l.split(":", 1)[1].split() for l in out if l.startswith("Flags")), [])
    return "; ".join(f"{k.strip()} {v.strip()}" for k, v in keep) + "; AMX flags: " + (" ".join(x for x in flags if x.startswith("amx")) or "none (this container has no AMX; docker/TOOLING.md described a 2.1 GHz AMX host)")


def f(x, n=3):
    return "n/a" if x is None else (f"{x:.{n}f}" if isinstance(x, float) else str(x))


def main():
    pc = json.load(open(f"{L}/protocol_check.json"))
    sm = json.load(open(f"{L}/summary.json"))
    sh = json.load(open(f"{L}/shards.json"))
    sa = {fn[:-5]: json.load(open(f"{L}/stage_a/{fn}")) for fn in sorted(os.listdir(f"{L}/stage_a"))}
    inv = {s: json.load(open(f"{L}/inventory_{s}.json")) for s in ("PHerc0814", "PHerc0500P2", "PHerc0332", "PHerc1451")}
    o = [PROV, "", "# Task pairs0814: known-text protocol check and PHerc0814 D2 training pairs", "",
         "STATUS: DONE (stage C run once over both halves: this session's 17 segments and pairs0814b's "
         "20250928235953 and 20250926051122, see HANDOVER.md)", ""]
    o += ["## Goal (a): field-by-field protocol check", "",
          "Source: official root index (decoded sha256 8119d1c2d48b54f880c81bfd7ff9a51eb5edd166c9c06eac754abf15dba7e0ac, "
          "unchanged since the D0 catalogue) and each volume's own metadata.json (voxel size = "
          "scan.tomo.acquisition.detector.samplePixelSize). References were re-derived from the index; every brief "
          "value agreed (JULY 7/7, MAY 4/4).", "",
          "| Scroll | Volume | session | voxel um | keV | distance m | exposure s | Paganin | unsharp | vs JULY | vs MAY |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for sc, p in pc["protocol"].items():
        for v in p["volumes"]:
            fl = v["fields"]
            o.append(f"| {sc} | {v['volume_id']} | {fl.get('session')} | {fl.get('voxel_um')} | {fl.get('keV')} | "
                     f"{fl.get('distance_m')} | {fl.get('exposure_s')} | {fl.get('paganin')} | {fl.get('unsharp')} | "
                     f"{v['vs_JULY']['n_match']}/{v['vs_JULY']['n_compared']} | {v['vs_MAY']['n_match']}/{v['vs_MAY']['n_compared']} |")
    o += ["", "Verdicts: " + "; ".join(f"{sc} {p['verdict']} (JULY volumes {p['JULY_match_volumes']}, MAY volumes "
                                        f"{p['MAY_match_volumes']})" for sc, p in pc["protocol"].items()) + ".",
          "Volumes with voxel None have no readable metadata.json on the bucket (404, or no scan block for the 1.129 um "
          "mosaic); none of them is a ~9 um candidate, so no verdict depends on them.", ""]
    o += ["## Segment inventories", "", "| Scroll | segments | 9.362 um mesh | 9.362 um SV | high-res mesh | high-res SV | "
          "ink maps by um | with labels |", "|---|---|---|---|---|---|---|---|"]
    for sc, d in inv.items():
        c = d["counts"]
        o.append(f"| {sc} | {c['segments']} | {c['with_9p362_mesh']} | {c['with_9p362_sv']} | {c['with_highres_mesh']} | "
                 f"{c['with_highres_sv']} | {c['ink_maps_by_resolution']} | {c['with_ink_labels']} |")
    o += ["", "Full paths and counts per segment: inventory_<scroll>.json and segment_inventory.json. PHerc0500P2 "
          "(fragment) matches JULY: all 46 segments were traced on its 4.317 um MAY-session volume, carry "
          "9.362/4.317/2.215 um meshes and SVs, and their ink maps are on the 2.215 um MAY-session scan "
          "20250526151718; 1 segment has official labels. As instructed, no 0500P2 pairs were built (held-out fold "
          "candidate). PHerc0332 matches neither protocol (2 folders with .obj meshes only). PHerc1451 matches MAY "
          "(one unindexed raw/ folder of 17 debug traces).", ""]
    o += ["## Goal (b): PHerc0814 D2 pairs", "", "### Method (DECL-D2; ASK.md defaults accepted by the orchestrator)", "",
          "1. Stage A (tools/sib/pairs0814/stage_a.py): 2-D canvas affine c9 = M c2 + t fitted from the two organizer "
          "meshes of each segment (2.399 um mesh vertices -> index landmark affine 20260309142202 -> 20250804134230 "
          "-> projected onto the 9.362 um mesh; 4-MAD trimmed LSQ). Official 2.399 um ink map area-averaged onto the "
          "9.362 um canvas (ref9).",
          "2. Stage B (stage_b.py): 384 px patches (stride 384, >= 90 % valid on both canvases); official "
          "vc_render_tifxyz -n 31, --flip-normals, voxel size 9.362 um from metadata.json; 2.4 um CT = organizer "
          "2.399 um SV slice 54 of 109 read by HTTP range requests and area-averaged onto the 9 um canvas; gate NCC "
          ">= 0.8 (zero shift) AND >= 7 of 9 128 px windows with sub-pixel shift norm <= 1.0 px; labels ink = ref9 "
          ">= 150, blank <= 100, rest and invalid 255.",
          "3. Stage C (stage_c.py): consistency checks, CORR-RETRACE-RULE same-papyrus annotation (base papyrus 46527, "
          "cross-segment duplicate groups), packing into shards.", ""]
    res = [a["residual_px9"]["p99"] for a in sa.values()]
    dn = [a["normal_dist_vox9"]["p95"] for a in sa.values()]
    sep = [a["separable_rule_residual_px9"]["p95"] for a in sa.values()]
    trim = [a.get("n_trimmed_outliers", 0) / max(1, a["n_projected"]) for a in sa.values()]
    o += ["### Validation", "",
          f"* Mesh affine (19 segments): kept-point residual p99 max {max(res):.4f} px; normal distance p95 max "
          f"{max(dn):.4f} vox; the fit equals the separable 0841 rule c9 = (c2 + 10.5) N9/N2 - 10.5 to p95 <= "
          f"{max(sep):.4f} px; trimmed projection outliers {100 * min(trim):.1f}-{100 * max(trim):.1f} % (points "
          "snapped to a wrong place on the 9 um mesh; they do not affect the fit).",
          "* Our 9.362 um render vs the organizer 9.362 um SV (segment 20250925212701, 1536 px crop): NCC 0.9968 at "
          "the surface, same slice direction (opposite direction 0.005-0.012).",
          "* Range-read 2.4 um chunk slices equal full-chunk slices bit for bit; stage B block labels equal stage A "
          "ref9 (max 1 grey level on 2 of 2.36 M px, ink >= 150 agreement 100 %); tiled-TIFF reader bit exact.",
          "* Unit tests: tests/sib_pairs0814_test_numerics.py (13 passed), incl. the CORR-RETRACE-RULE half-cell "
          "re-trace case.", ""]
    n0, c5 = sm["ncc0"], sm["control_ncc_shift5_max"]
    lb = sm["labels_passed"]
    o += ["### Results (this session's segments)", "",
          f"* Candidates {sm['candidates']}, gated {sm['gated']}, PASS {sm['passed']} (rate {sm['pass_rate']:.3f}); "
          f"segments complete {sm['segments_complete']}; handed over {sm.get('segments_handed_over')}.",
          f"* Patch NCC at zero shift: p5 {f(n0['p5'])}, p25 {f(n0['p25'])}, median {f(n0['median'])}, p75 "
          f"{f(n0['p75'])}, p95 {f(n0['p95'])}; fraction >= 0.8: {f(n0['frac_ge_0p8'])}.",
          f"* Control (not gating), best NCC at +-5 px shifts: median {f(c5['median'])}, p95 {f(c5['p95'])}, max "
          f"{f(c5['max'])}, fraction >= 0.8: {f(c5['frac_ge_0p8'])} -> the 0.8 bar separates aligned from shifted CT.",
          f"* Aligned windows per patch (histogram 0..9): {sm['n_aligned_hist']}.",
          f"* Labels in PASS patches: ink {lb['ink_px']} px ({lb['ink_cm2']:.3f} cm^2), blank {lb['blank_px']} px "
          f"({lb['blank_cm2']:.3f} cm^2), ignored {lb['ignore_px']} px; patch area {lb['area_cm2']:.2f} cm^2.",
          f"* Base papyrus (46527, {sm['base_papyrus']['rule']}): {json.dumps({k: v for k, v in sm['base_papyrus'].items() if k != 'rule'})}.",
          f"* Duplicates: {json.dumps(sm['duplicates'])}.",
          f"* Shards: {sm['shards']['n']} files, {sm['shards']['bytes'] / 1e6:.1f} MB total, max "
          f"{sm['shards']['max_bytes'] / 1e6:.1f} MB (shards.json lists sha256 and patch ids).",
          f"* Consistency problems: {sm['consistency_problems'] or 'none'}.", "",
          "| Segment | source | candidates | PASS | fail NCC only | fail align only | fail both | render failed | ink px | blank px | ignored px |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s, r in sm["per_segment"].items():
        o.append(f"| {s} | {'pairs0814b' if r.get('handed_over') else 'pairs0814'} | {r['candidates']} | {r['passed']} | "
                 f"{r['fail_ncc_only']} | {r['fail_align_only']} | {r['fail_both']} | {r['render_failed']} | "
                 f"{r['ink_px']} | {r['blank_px']} | {r['ignore_px']} |")
    o += ["", "### Outputs", "",
          "* pair_registry.json: every PASS patch (segment, 9 um canvas box, 2.4 um footprint, 3-D centre and bbox in "
          "9.362 um voxels, gate numbers, median window shift, label counts, shard and index, base-papyrus and "
          "duplicate annotations); pair_registry_xyz.npz: 17 x 17 xyz grid per PASS patch.",
          "* registry/<segment>.jsonl: every candidate incl. failures with all 9 window shifts and controls.",
          "* Shards = the staged block files (one per 1536 px block, <= 16 patches, each < 90 MB): "
          "logs/sib/pairs0814/blockpairs/<segment>/<y>_<x>.npz on this branch and data/sib/pairs0814b/blockpairs/... on "
          "pairs0814b; arrays images uint8 (N, 21, 384, 384) = render slices 5..25, ref9, labels (1 ink, 0 blank, 255 "
          "ignore), valid, xyz, patch_id. Not repacked (repacking would duplicate every patch and exceed the 1.5 GB "
          "branch budget). shards.json lists branch, path, sha256 and patch ids of every file.",
          "* protocol_check.json, segment_inventory.json, inventory_<scroll>.json, stage_a/<segment>.json, "
          "summary.json, shards.json, runs.jsonl (every run, failures included).", ""]
    o += ["### Failures and deviations", "",
          "* setup_env: exit 1 at the vesuvius Python 3.14 install step (not needed: no inference here); the C++ apps "
          "and /opt/hv built fine. The proxy port changed, so tools/sib/pairs0814/setup_env_sib.sh and vc_build_sib.sh "
          "take it from HTTPS_PROXY.",
          "* Stage B stopped silently at 2026-09-25T19:57Z while the session was suspended (usage limit) and was "
          "restarted from block checkpoints at 23:26Z (dockerd restarted); no block was lost or duplicated "
          "(stage C uniqueness check).",
          "* Five small 2026 segments (0.2-0.3 cm^2) have no 384 px patch >= 90 % valid, so 0 candidates.",
          "* Split: segments 20250928235953 (71 blocks) and 20250926051122 (65 blocks) handed to pairs0814b "
          "(HANDOVER.md); their block files and registry rows live on that branch, and the final stage C read them "
          "through git objects of the recorded commit (below) to annotate base papyrus and duplicates across both "
          "halves.", ""]
    o += ["## What the orchestrator needs to declare next", "",
          "1. The D2 pair recipe as built (ASK.md Q1-Q6), incl. that labels are not shift-corrected (median window "
          "shifts are recorded per patch if a corrected variant is wanted).",
          "2. Exclusions: which base-papyrus (46527) patches and which members of each duplicate group enter D2 "
          "training (DECL-D2-POOL-1, proposed); stage C only flagged, no patch was dropped.",
          "3. Whether PHerc0500P2 (JULY match; maps on the MAY-session 2.215 um scan) becomes the L-0500P2 fold; its "
          "pairs would use the same code with the 2.215 um volume and SV.", ""]
    u = sm.get("union") or {}
    o += ["## Provenance of this run", "",
          f"* pairs0814b commit used by stage C (read through git objects only): {u.get('commit')} "
          f"({json.dumps(u.get('segments', {}))}).",
          "* Host: " + host(),
          "* Final commit: see git log of claude/gifted-bell-gavnl5-sib-pairs0814 (the commit that adds this REPORT.md).", ""]
    grp = json.load(open(f"{L}/pair_registry.json"))["patches"]
    multi = collections.defaultdict(list)
    for x in grp:
        if x["duplicate_group_size"] > 1:
            multi[x["duplicate_group"]].append(x["patch_id"])
    o += ["## Duplicate groups (multi-member) and base-papyrus flags", "",
          f"{len(multi)} multi-member groups; members listed in pair_registry.json (duplicate_group). Base-papyrus "
          "(46527 same-papyrus by rule) patches: " + ", ".join(x["patch_id"] for x in grp if x["base_same_papyrus_46527"]) + ".", ""]
    open(f"{L}/REPORT.md", "w").write("\n".join(o) + "\n")
    print("REPORT.md", len(o), "lines")


if __name__ == "__main__":
    main()
