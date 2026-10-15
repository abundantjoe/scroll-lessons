# Provenance: Project HERCULES | owner the owner | [id removed]
"""Driver for the PHerc0139 D2 pairs (task pairs0139): segments in order of label quality (labelq.py ranking:
tier A by kappa vs the official 2.399 um human labels, then tier B by ink-map crispness), excluded segments skipped
(exclusion.json). The next segment's render runs while the current one is tiled. Stops after the segment in which the
cumulative kept count reaches TARGET (3000). Resumable: a segment with registry/<short>.summary.json is done.
Writes /work/p139/out/order.json. Usage: run_all.py [TARGET]"""
import json, os, subprocess, sys, time

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
OUT = "/work/p139/out"
PY = "/work/p139/py/bin/python"
RUN = "tools/sib/pairs0139/run.sh"
ENV = dict(os.environ, PYTHONPATH="src:tools/sib/pairs0139")


def short(s):
    return s.split("-")[1].split("_")[0]


def order():
    excl = json.load(open("/work/p139/exclusion_v2.json"))   # CORR-RETRACE-RULE re-check (retrace_check.py)
    E = set(excl["E"])
    lq = {}
    for l in open("/work/p139/labelq.jsonl"):
        r = json.loads(l); lq[r["segment"]] = r
    aff = json.load(open("/work/p139/affines.json"))["segments"]
    missing = [s for s in aff if short(s) not in E and s not in lq]
    assert not missing, f"label quality missing for {missing}"
    A = sorted([s for s in lq if short(s) not in E and lq[s].get("human")], key=lambda s: -lq[s]["human"]["kappa"])
    Bt = sorted([s for s in lq if short(s) not in E and not lq[s].get("human")], key=lambda s: -lq[s]["crispness"])
    rows = [dict(rank=i + 1, segment=s, short=short(s), tier="A" if s in A else "B",
                 kappa=lq[s]["human"]["kappa"] if s in A else None, crispness=lq[s]["crispness"])
            for i, s in enumerate(A + Bt)]
    json.dump(dict(rule="tier A (official 2.399 um human labels) by kappa desc, then tier B by crispness desc; "
                        "excluded segments (exclusion.json E) skipped", excluded=sorted(E), order=rows),
              open(f"{OUT}/order.json", "w"), indent=1)
    return [r["segment"] for r in rows]


def kept_so_far():
    n = 0
    for f in os.listdir(f"{OUT}/registry"):
        if f.endswith(".summary.json"):
            n += json.load(open(f"{OUT}/registry/{f}"))["kept"]
    return n


def main():
    os.makedirs(f"{OUT}/registry", exist_ok=True)
    segs = order()
    todo = [s for s in segs if not os.path.exists(f"{OUT}/registry/{short(s)}.summary.json")]
    rproc = None
    for i, s in enumerate(todo):
        if kept_so_far() >= TARGET:
            print("target reached", kept_so_far(), flush=True)
            break
        # make sure this segment's render exists (maybe started as the previous 'next')
        if rproc is not None:
            rproc.wait(); rproc = None
        if not os.path.exists(f"/work/p139/render/{short(s)}.zarr.done.json"):
            while subprocess.run(["pgrep", "-f", f"render_only.py {s}"], capture_output=True).returncode == 0:
                time.sleep(20)          # a render of this segment started elsewhere is still running
        if not os.path.exists(f"/work/p139/render/{short(s)}.zarr.done.json"):
            subprocess.run([RUN, f"render_{short(s)}", PY, "tools/sib/pairs0139/render_only.py", s],
                           env=dict(ENV, VC_CPUS="3"))
        if i + 1 < len(todo):
            nxt = todo[i + 1]
            if not os.path.exists(f"/work/p139/render/{short(nxt)}.zarr.done.json") and \
                    subprocess.run(["pgrep", "-f", f"render_only.py {nxt}"], capture_output=True).returncode != 0:
                rproc = subprocess.Popen([RUN, f"render_{short(nxt)}", PY, "tools/sib/pairs0139/render_only.py", nxt],
                                         env=dict(ENV, VC_CPUS="2"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        rc = subprocess.run([RUN, f"pairs_{short(s)}", PY, "tools/sib/pairs0139/build_pairs.py", s], env=ENV).returncode
        print("segment", short(s), "rc", rc, "kept so far", kept_so_far(), flush=True)
    if rproc is not None:
        rproc.wait()
    print("done; kept", kept_so_far(), flush=True)


if __name__ == "__main__":
    main()
