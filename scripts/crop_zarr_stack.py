#!/usr/bin/env python
"""Crop a local zarr-v2 surface-volume stack (group with array "0", axes z y x, uint8) into a new
OME-style zarr group with array "0" that villa's infer accepts. Pure numpy + zarr; idempotent.
usage: crop_zarr_stack.py <in.zarr> <out.zarr> --x X --y Y --w W --h H [--zrange z0:z1]
"""
import argparse, json, os, sys, shutil
import numpy as np, zarr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--x", type=int, required=True); ap.add_argument("--y", type=int, required=True)
    ap.add_argument("--w", type=int, required=True); ap.add_argument("--h", type=int, required=True)
    ap.add_argument("--zrange", default=None, help="z0:z1 half-open; default all slices")
    a = ap.parse_args()
    if os.path.exists(os.path.join(a.out, ".complete")):
        print("exists, skipping", a.out); return
    g = zarr.open_group(a.inp, mode="r")
    arr = g["0"]
    z0, z1 = (0, arr.shape[0]) if a.zrange is None else map(int, a.zrange.split(":"))
    data = arr[z0:z1, a.y:a.y + a.h, a.x:a.x + a.w]
    print("crop shape", data.shape, "dtype", data.dtype, "min/max", int(data.min()), int(data.max()),
          "nonzero frac", float((data > 0).mean()))
    if os.path.exists(a.out): shutil.rmtree(a.out)
    og = zarr.open_group(a.out, mode="w", zarr_format=2)
    oa = og.create_array("0", shape=data.shape, chunks=(data.shape[0], 128, 128), dtype="uint8",
                         compressors=None, chunk_key_encoding={"name": "v2", "separator": "/"})
    oa[:] = data
    # minimal OME multiscales metadata so consumers know axes z y x
    og.attrs["multiscales"] = [{"version": "0.4", "axes": [{"name": n, "type": "space"} for n in "zyx"],
                                "datasets": [{"path": "0"}]}]
    json.dump({"source": os.path.abspath(a.inp), "x": a.x, "y": a.y, "w": a.w, "h": a.h, "z": [z0, z1]},
              open(os.path.join(a.out, "crop.json"), "w"), indent=1)
    open(os.path.join(a.out, ".complete"), "w").write("ok\n")
    print("wrote", a.out)

if __name__ == "__main__":
    main()
