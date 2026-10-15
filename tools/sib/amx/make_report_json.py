# Provenance: Project HERCULES | owner the owner | [id removed]
"""Roll up the task-amx result files into logs/sib/amx/report.json (numbers + sha256 of every source file)."""
import hashlib, json, os
L = "/home/user/dominion/logs/sib/amx"
T = "/home/user/dominion/tools/sib/amx"
J = lambda f: json.load(open(f"{L}/{f}"))
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
s, p, c, i8, i8b, g, a = J("summary.json"), J("profile_split.json"), J("cache_path.json"), J("int8_feas.json"), J("int8_feas_fxparts.json"), J("synth_chain_gate.json"), J("precision_ablation.json")
rep = dict(
    provenance="Project HERCULES | owner the owner | [id removed]", task="amx",
    environment=dict(villa="41701aa0eaa1aa765523db3f9f972b5830abf549", torch=p["env"]["torch"], onednn="3.12.0",
                     checkpoint_sha256="e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab",
                     checkpoint_hash_verified=True, amx_kernels_bf16="brg_conv_fwd:avx10_1_512_amx (oneDNN verbose)",
                     fp32_kernels="jit:avx512_core", cpu="4 vCPU Intel Xeon 2.1 GHz, AMX-BF16/INT8, 1 thread per core"),
    item3_grid=dict(pass1=s["table"], pass2_replicate=s["replicate"]["table"], replicate_median_rel_diff=s["replicate"]["median_rel_diff"]),
    item3_int8=dict(fp32_eager_median_s=i8["fp32_eager"]["median_s"], attempts={**i8["attempts"], **i8b["attempts"]}),
    item4_profile=dict(params=p["params"], piecewise_equals_full_max_abs=p["piecewise_equals_full"],
                       infer={dt: {k: dict(median_s=p["infer"][dt][k]["median_s"], share=p["infer"][dt][k].get("share_of_total_median")) for k in ("stem", "enc2d", "dec2d", "total")} for dt in ("fp32", "bf16")},
                       infer_achieved_gflops={dt: p["infer"][dt]["achieved_gflops"] for dt in ("fp32", "bf16")},
                       train={dt: {k: v["median_s"] for k, v in p["train"][dt].items() if k != "seg_share"} for dt in ("fp32", "bf16")},
                       train_share={dt: p["train"][dt]["seg_share"] for dt in ("fp32", "bf16")}, flops=p["flops"]),
    item5_cache=dict(equivalence=c["equivalence"], cache_bytes_per_tile=c["cache_bytes_per_tile_on_disk"],
                     cache_values_per_tile=c["cache_values_per_tile"], letter_context=c["letter_context"], throughput=c["throughput"]),
    precision_ablation={k: {kk: v[kk] for kk in ("u8_frac_within_2", "u8_max_abs", "u8_frac_identical", "logit_max_abs", "logit_p999_abs", "speedup_vs_fp32")} for k, v in a["variants"].items()},
    synthetic_full_chain_gate={k: g[k] for k in ("verdict", "pearson", "frac_within_2", "max_abs_diff", "checks")} | dict(orders=g["orders"], synthetic=g["synthetic"]),
    files_sha256={f: sha(f"{L}/{f}") for f in sorted(os.listdir(L)) if f.endswith((".json", ".jsonl")) and f != "report.json"} | {f"tools/sib/amx/{f}": sha(f"{T}/{f}") for f in sorted(os.listdir(T)) if f.endswith((".py", ".sh"))},
)
json.dump(rep, open(f"{L}/report.json", "w"), indent=1)
print("ok", len(rep["files_sha256"]))
