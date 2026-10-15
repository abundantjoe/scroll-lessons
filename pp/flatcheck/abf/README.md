# Optional ABF++ path (official vc_flatten algorithm)

`abf_uv_dump.cpp` calls the unmodified `vc::abfFlatten` from ScrollPrize/villa
`volume-cartographer` (tested at commit 41701aa0eaa1aa765523db3f9f972b5830abf549)
with the defaults of `vc_flatten`, and writes the per-vertex UV as `u.tif`/`v.tif`.
`vc_flatten --uv-only` computes the same UVs but aborts when saving a 2-channel TIFF.

Build (inside the official deps image `ghcr.io/scrollprize/vc3d-deps/linux`,
after building `vc_flattening`/`vc_core` from villa with CMake):

    g++ -std=gnu++23 -O2 -fopenmp -I<villa>/volume-cartographer/core/include \
      -I<villa>/volume-cartographer/utils/include -isystem /usr/include/opencv4 -isystem /usr/include/eigen3 \
      abf_uv_dump.cpp -o abf_uv_dump <build>/core/libvc_flattening.so <build>/core/libvc_core.so \
      <build>/utils/libutils.so -lopencv_imgcodecs -lopencv_core -ltiff

Then set `FLATCHECK_ABF_CMD` to a command prefix that runs the binary, for
example `docker run --rm -v $PWD:$PWD -w $PWD <image> /path/abf_uv_dump`.
flatcheck calls `$FLATCHECK_ABF_CMD <in.tifxyz> <out_dir>`.
