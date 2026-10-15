"""hzw1: offset-0 regression of off_E2 records against p4-highz stage_b_E2.jsonl (exact equality expected).
Provenance: Project HERCULES | owner the owner | [id removed]
Usage: python regress0.py <p4-highz worktree> <scratch>
"""
import sys
HZ, SCR = sys.argv[1], sys.argv[2]
import json
sb={(d["r"],d["c"]):d for d in map(json.loads,open(HZ + "/logs/sib/p4-highz/stage_b_E2.jsonl"))}
k=next(iter(sb.values())); print(sorted(k)[:20])
n=m=0
for d in map(json.loads,open(SCR + "/off_E2_-60_-45_-30_-15_0_15_30_45_60.jsonl")):
    s=sb.get((d["r"],d["c"]))
    if s is None: print("missing",d["r"],d["c"]); continue
    o=d["offsets"]["0"]; n+=1
    eq=(o["n_hi"]==s.get("n_hi"), o["stroke"]==s.get("stroke"), o["acf"]==s.get("acf"), o["acf_rot90"]==s.get("acf_rot90"))
    m+=all(eq); print(d["r"],d["c"],o["n_hi"],s.get("n_hi"),eq)
print("exact",m,"/",n)
