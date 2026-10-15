# Draft issues for ScrollPrize/villa (not filed)

Two problems this project measured in community tools, written up for filing upstream. They have **not** been filed.
Filing is the repository owner's decision, and so is ticking each draft's "I personally encountered or reproduced
this" box.

How to use a draft:

- The numbered `##` line, without its number, is the issue title. Each draft's `## Details` line is part of its body.
- The text below the title, up to the next `---` or the end of the file, is the issue body.
- Each body follows villa's issue template (`.github/ISSUE_TEMPLATE/issue.md`, which `CONTRIBUTING.md` asks reporters
  to use).

About the links:

- Every link into a repository file is absolute and pinned to a commit, so a body can be pasted into a villa issue
  unchanged. The links resolve once this repository is public and its `main` contains commit `d097884`.
- Line links into Markdown files carry `?plain=1` so that they open at the cited line.
- Evidence is this repository's own committed files, plus villa's source where noted.

---

## 1. `ghcr.io/scrollprize/villa/volume-cartographer:edge` / `:main` is still the 2026-05-13 build; its `vc_render_tifxyz` rejects tutorial5's `--flip-normals`

**In one sentence:** On 2026-10-15, `ghcr.io/scrollprize/villa/volume-cartographer:edge` and `:main` were still the
image built on 2026-05-13 from villa `1e3f4c0`. Its `vc_render_tifxyz` rejects the `--flip-normals` flag that the
render command at https://scrollprize.org/tutorial5 uses.

**I was trying to:** render the published mesh of PHerc0139 segment `20250831000000-w040_2025083102` ("w040") with
`vc_render_tifxyz`, and reproduce the 28-slice surface volume published for it ("the published surface volume"
below). This was for [abundantjoe/hercules](https://github.com/abundantjoe/hercules), an independent project that uses
villa's VC3D tools and the `vesuvius` ink-detection package. Evidence links point into that repository, pinned to
commits.

**Using:** the image that `:edge` and `:main` resolved to on 2026-10-15. Its config gives `created`
2026-05-13T18:41:20Z and `org.opencontainers.image.revision` `1e3f4c021f4e53bea3867772ed05f51a7e586a9c`. The binary was
`/usr/local/bin/vc_render_tifxyz` in that image.

**What happened:** The binary's `--help` lists `--flip` (an image flip) and no `--flip-normals`. Passing
`--flip-normals` prints `Error: unrecognised option '--flip-normals'` and exits 1. The render command in tutorial5 ends
in that flag, and the page says "--flip-normals reproduces the depth orientation of the published renders and the
training labels". We passed the flag alone; we did not run tutorial5's full command against this image.

**What I expected or needed:** an image that https://scrollprize.org/segmentation calls up to date, in which
tutorial5's render command runs.

**Evidence / reproduction:** We read the tags through the anonymous GHCR API and then ran `docker pull`. The literal
invocations were not recorded. These are equivalent commands, each followed by the result we recorded:

```sh
docker pull ghcr.io/scrollprize/villa/volume-cartographer:edge
docker inspect -f '{{.Created}} {{index .Config.Labels "org.opencontainers.image.revision"}}' \
    ghcr.io/scrollprize/villa/volume-cartographer:edge
# recorded: created 2026-05-13T18:41:20Z, revision 1e3f4c021f4e53bea3867772ed05f51a7e586a9c
docker run --rm --entrypoint /usr/local/bin/vc_render_tifxyz \
    ghcr.io/scrollprize/villa/volume-cartographer:edge --help | grep -c -- --flip-normals
# recorded: no --flip-normals in the help text (this prints 0)
docker run --rm --entrypoint /usr/local/bin/vc_render_tifxyz \
    ghcr.io/scrollprize/villa/volume-cartographer:edge --flip-normals; echo "exit $?"
# recorded: Error: unrecognised option '--flip-normals', exit 1
```

Evidence:

- the saved help output,
  [`vc_render_tifxyz_help_edge_2026-05-13.txt`](https://github.com/abundantjoe/hercules/blob/d097884/records/release/vc_render_tifxyz_help_edge_2026-05-13.txt);
- the [image check, 2026-10-15](https://github.com/abundantjoe/hercules/blob/d097884/records/release/edge_image_check_2026-10-15.md),
  whose two readings are corrected by the section appended at its end;
- lab notebook `RULES.md` at commit 71720ce:
  - [stale image and smoke render, line 28](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L28);
  - [rebuilt renderer, line 29](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L29);
  - [forward and reverse AUC on w040, line 14](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L14).

- [ ] I personally encountered or reproduced this using the version and data stated above.

## Details

**Why it matters.** https://scrollprize.org/segmentation says "We host an up-to-date image on the github container
registry" and gives `docker pull ghcr.io/scrollprize/villa/volume-cartographer:edge`. Two measurements bear on what
happens to a user who follows that advice:

- On 2026-09-16, a 256 × 256 smoke render of the w040 mesh with this binary matched the published surface volume only
  with the slice order reversed. Even then the match was only Pearson 0.42–0.82 per slice, with an identical-pixel
  fraction of 0.40, and no in-plane or half-slice shift explained the difference.
- On w040's ink labels, the ink model (`scrollprize/ink_9um` `hybrid_3d2d-seed42/step-075000`) scores pixel ROC AUC
  0.99659 on the published surface volume, and 0.49633, about chance (0.5), with its slice order reversed
  (1,629,734 supervised pixels).

**Inference** from those two measurements: a user who drops the unrecognised flag to make the command run gets the
depth order the model was not trained on, and ink predictions at about chance (pixel ROC AUC near 0.5). Neither step
was run end to end with this binary.

**Workaround that works for us.** Build the tools from villa source inside
`ghcr.io/scrollprize/villa/volume-cartographer:builder-ubuntu-26.04`, with
[`build_vc3d.sh`](https://github.com/abundantjoe/hercules/blob/d097884/scripts/build_vc3d.sh). That script is
written for our machine. On another machine:

- drop the `-v /root/.ccr/ca-bundle.crt:/ca.crt:ro` mount, together with the `SSL_CERT_FILE`, `CURL_CA_BUNDLE` and
  `GIT_SSL_CAINFO` settings that point at it;
- set `VILLA` to your villa checkout and `HERCULES_DATA` to an output directory.

At villa `5ab585f`, on a 2048 × 2048 crop of w040 rendered with `--flip-normals`, the rebuilt renderer matched the
published surface volume at a minimum Pearson of 0.999999 (to six decimals) over the 28 slices. The match was not
bit-identical: the minimum identical-pixel fraction was 0.9956.

**Suggested fix.** There are two options:

- publish `:edge` / `:main` again from current `main`;
- or retire those tags and change https://scrollprize.org/segmentation to name what users should pull instead.

At villa `5ab585f` we found no workflow that pushes either tag. The only push to
`ghcr.io/scrollprize/villa/volume-cartographer` we found is `ci.sh publish`
([`ci.sh` lines 175–192](https://github.com/ScrollPrize/villa/blob/5ab585ffee54331a3362b9ce6b2929b20dcde2c6/volume-cartographer/scripts/ci.sh#L175-L192),
run by `.github/workflows/vc3d-publish-ghcr.yml`). It writes the `builder-<image>` and `builder-<image>-<sha>` tags.
Until the tags are published again or retired, the segmentation page could point at the `builder-ubuntu-26.04` image
plus a source build.

---

## 2. `vesuvius.ink_detection.inference.infer --direction both` can exit 0 with an incomplete reverse map (regions left at 0) under heavy load

**In one sentence:** Twice on a heavily loaded CPU-only machine, `python -m vesuvius.ink_detection.inference.infer
... --direction both` left regions of the reverse-direction map at 0 (no prediction). One run is recorded as exiting
0, and we infer that the other did too.

**I was trying to:** compare forward and reverse ink maps from the `scrollprize/ink_9um`
`hybrid_3d2d-seed42/step-075000.pth` checkpoint on surface renders. This was for
[abundantjoe/hercules](https://github.com/abundantjoe/hercules), an independent project that uses villa's `vesuvius`
ink-detection package. Evidence links point into that repository, pinned to commits.

**Using:** `vesuvius` installed editable from villa `5ab585ffee54331a3362b9ce6b2929b20dcde2c6`, with Python
3.14.0rc2, torch 2.14.0+cpu and no GPU. The checkpoint was `scrollprize/ink_9um` `hybrid_3d2d-seed42/step-075000.pth`.

- **First case.** Input: our 28-slice `vc_render_tifxyz` render of a 2048 × 2048 crop of PHerc0139 segment
  `20250831000000-w040_2025083102`. Command
  ([`rdepth.sh` at a789712, lines 17–19](https://github.com/abundantjoe/hercules/blob/a789712/scripts/rdepth.sh#L17-L19)):
  `nice -n 19 python -m vesuvius.ink_detection.inference.infer render.zarr step-075000.pth high.tif --direction both --layer-start 11 --layer-end 28 --batch-size 4 --no-compile --num-workers 2`
- **Second case.** Input: our render of a PHerc1203 surface (our id `team_20250923163331524`). Our runner's command
  builder ([`run_patch_dir.py` at 303a5ce, lines 78–82](https://github.com/abundantjoe/hercules/blob/303a5ce/scripts/run_patch_dir.py#L78-L82);
  the same call at f0ff387 for the default window) passes `--direction both --tta-mirror --batch-size 4 --no-compile
  --num-workers 3` and no layer arguments.

**What happened:** Both cases were on 2026-09-19, and both were on the reverse pass.

- **First case.** The reverse map was non-zero on exactly 25.00 % of its pixels (one quadrant). Its forward map was
  100 % non-zero, and the process exited 0.
- **Second case.** The reverse map was non-zero on 0.9404 of the input's on-sheet pixels (pixels where the input's
  middle slice is non-zero), against 1.0000 for the forward map. Our notes do not state its exit status. They do
  record that its inference-complete marker existed, and our runner writes that marker only when the inference
  returns 0 ([`run_patch_dir.py` at 303a5ce, lines 155–156](https://github.com/abundantjoe/hercules/blob/303a5ce/scripts/run_patch_dir.py#L155-L156)).
  So we infer that it also exited 0.

The machine was one CPU-only box (4 cores, 15 GB RAM). Our job scripts that went through our runner each used a
separate lock file, none of which blocked the others, so up to eight of these inferences could hold a lock at once.
The first case's script took no lock at all, so it was not one of those eight. The load average was 10–14 that night.

**What I expected or needed:** a complete map for each direction, or a non-zero exit status when a map is incomplete.

**Evidence / reproduction:** We have no deterministic reproducer.

- A re-run of the first command on the same input completed. Both maps were 100 % non-zero, with 100 % coverage of
  the on-sheet pixels.
- A later re-run of the second case also completed, with both maps 0.5976 non-zero and identical footprints.

Our notes do not establish that the machine load during these re-runs matched the failing runs. Our runner's
`--num-workers` default was lowered from 3 to 2 at about 03:12 UTC that night
([`run_patch_dir.py` at 2141cdb, line 98](https://github.com/abundantjoe/hercules/blob/2141cdb/scripts/run_patch_dir.py#L98)). The second case's re-run most
likely still used 3: its throughput record
([`records/throughput.jsonl` at 71720ce, line 141](https://github.com/abundantjoe/hercules/blob/71720ce/records/throughput.jsonl#L141)) ends at 05:21:01Z after
8140.9 s of inference and 14.9 s of reading, so its inference began no later than about 03:05 UTC (an inference from
those timings).

Evidence, from lab notebook `RULES.md` at commit 71720ce:

- [environment, line 7](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L7);
- [first case, line 1618](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1618);
- [`dmesg` observation, line 1690](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1690);
- [second case and its deleted marker, lines 1740–1749](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1740-L1749);
- [locks, load and the unproven cause, lines 1757–1770](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1757-L1770);
- [leaked-semaphore log and the worker change, lines 1810–1817](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1810-L1817);
- [villa commit, line 1969](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1969);
- [complete re-run of the first case and M = 0.39948, lines 1993–2017](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1993-L2017);
- [re-run of the second case, lines 2073–2079](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L2073-L2079).

The first case's script calls the inference directly and takes no lock
([`rdepth.sh` at a789712, lines 13–20](https://github.com/abundantjoe/hercules/blob/a789712/scripts/rdepth.sh#L13-L20)); commit
[`acc775f`](https://github.com/abundantjoe/hercules/commit/acc775f) records that it "bypassed run_patch_dir.py's cap
entirely". A summary is in
[lesson 1](https://github.com/abundantjoe/hercules/blob/d097884/docs/LESSONS.md#1-check-that-both-maps-of-a-pair-are-complete-before-scoring-them).

- [ ] I personally encountered or reproduced this using the version and data stated above.

## Details

**Effect.** Pixels with no prediction are 0 in the output. That lowers the reverse mean and inflates forward − reverse.
We used M = mean forward probability on labelled ink − mean reverse probability on labelled ink. On the first case's
incomplete map, M = 0.60594. The complete re-run of the same command on the same input gave M = 0.39948. With the
incomplete map, a comparison we had specified before running it passed instead of failing, until we caught it.

**Cause: unproven.** During the first case, `dmesg` showed four failed allocations of about 67.8 TB by a python
process, inside the window in which that reverse pass ran. That is suggestive and nothing more. The same night, a
different inference on the same box selected 1139 patches and then died with
`resource_tracker: There appear to be 18 leaked semaphore objects to clean up at shutdown`, exiting non-zero. Our
notes read that as multiprocessing workers being killed under pressure, and they attribute the first case to the same
mechanism ("Same mechanism, two different exit codes"). That is an **inference**, not shown for either incomplete
map, and the comparison in our notes names only the first case.

**Why it matters.** A pipeline that trusts the exit code will score such a map as if it were complete. For a
forward − reverse statistic, an incomplete reverse map pushes the result toward a false positive.

**Suggested fix.** Make each direction fail before its TIFF is written if any scheduled patch was not processed. One
way to do it:

1. In `infer_single_zarr`, `len(blocks)` is the count logged as `Selected %d patches for inference`
   ([`infer.py` line 1058 at villa 5ab585f](https://github.com/ScrollPrize/villa/blob/5ab585ffee54331a3362b9ce6b2929b20dcde2c6/vesuvius/src/vesuvius/ink_detection/inference/infer.py#L1058)).
2. `run_block_inference` could return how many patches the `DataLoader` yielded. That count would include both the
   patches it accumulates and the ones it drops because their raw input is all zero
   ([line 757](https://github.com/ScrollPrize/villa/blob/5ab585ffee54331a3362b9ce6b2929b20dcde2c6/vesuvius/src/vesuvius/ink_detection/inference/infer.py#L757)).
3. `infer_single_zarr` could then raise before `write_output_tiff` when that total is below `len(blocks)`.

Counting only the accumulated patches would not work. Dropping all-zero patches is intended (see the
`flush_remaining` docstring,
[lines 726–727](https://github.com/ScrollPrize/villa/blob/5ab585ffee54331a3362b9ce6b2929b20dcde2c6/vesuvius/src/vesuvius/ink_detection/inference/infer.py#L726-L727)),
so that count can be lower on a correct run.

Raising before the write also matters for `--folder`. That mode skips any direction whose TIFF already exists, so an
incomplete TIFF left on disk would be kept on the next run.

The cause is unproven, so this count may not catch every case: a patch whose input came back as all zeros would be
counted as a legitimate drop. The output check below would have flagged both of our cases.

**A downstream check** also catches the problem without knowing its cause, using two tests:

- the forward and reverse maps of one run must have non-zero fractions within 0.02 of each other;
- each map must be non-zero on ≥ 99 % of the pixels where the input's middle slice is non-zero.

[`map_integrity.py`](https://github.com/abundantjoe/hercules/blob/d097884/scripts/map_integrity.py) runs both:
`python map_integrity.py --pair out.tif out_reverse.tif --render-dir <directory containing render.zarr>`. Without
`--render-dir` it runs only the first test.
