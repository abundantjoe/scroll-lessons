# Quick start on real known text

`bash examples/quickstart.sh` runs the core QC tools of this repository on a **real 3.9989 cm² window of known
Herculaneum text**: the reader `read_chart.py` (with the libraries `rule55.py` and `contact_sheet.py`), the
truncated-map guard `map_integrity.py` and the layout-power tool `cluster_power.py`. It then checks the outputs against
recorded values. Beyond the clone and `pip install -r requirements.txt`, it needs no GPU, no network and no data download. It takes about
16 s on a 4-core CPU (measured 2026-10-15). The other reusable tools (`score_auc.py`, `rheldout.py`,
`release_stats.py`, `make_figures.py`) are not run here; see [`scripts/README.md`](../scripts/README.md).

```bash
pip install -r requirements.txt
bash examples/quickstart.sh            # writes examples/out/ (git-ignored); prints "ALL CHECKS PASSED", then the contact-sheet path; exit 0
```

## The input: the w040 known-text window

| | |
|---|---|
| Scroll / segment | PHerc0139, segment `20250831000000-w040_2025083102` (the Vesuvius Challenge known-text control; not an eligible scroll; a training-set sheet of the model, see below) |
| Window | 2136 × 2136 px at 9.362 µm/px = 3.9989 cm² (side 19.9972 mm, `packages/DRYRUN_PHerc0139_w040/package.json`), canvas rows 1500–3635, columns 2000–4135 |
| Forward / reverse maps | `scrollprize/ink_9um` `hybrid_3d2d-seed42/step-075000.pth`, plain (no TTA), both depth orders, on the team's native 28-slice surface volume (RULES.md G-A) |
| CT | slice 14 of the same public surface volume |
| Stored in | `packages/DRYRUN_PHerc0139_w040/` (`mesh.png`, `reverse_window.png`, `ct_window.png`): rows 0–2135 are the uint8 arrays, losslessly |
| Integrity | `extract_w040_window.py` refuses to write any array whose pixel sha256 differs from the record. The forward and reverse values are the `forward_window_sha256` / `reverse_window_sha256` that `package.json` recorded on 2026-09-17. The CT value equals the sha256 of the public stack's slice 14, same crop, re-computed on 2026-10-15 from a fresh download. |
| Ground truth | The w040 human ink labels mark **3.89 %** of the window's pixels as ink. Only 8.72 % of the window is supervised, so 3.89 % is a lower bound on the ink present. Per 0.5 cm² unit (labelled ink fraction φ, truncated to four decimals): (0,0) 0.0414, (0,1) 0.0103, (1,0) **0.1176**, (1,1) 0.0710. Measured 2026-10-15 from `w040_inklabels.zarr`, slice 14, ink > 128, by [`window_label_stats.py`](window_label_stats.py); output in [`records/release/quickstart_window_label_stats.txt`](../records/release/quickstart_window_label_stats.txt) (398,077 of the window's 4,562,496 px supervised, 8.724982 % truncated, which the script prints rounded to nearest as 8.724983; 177,573 px ink, 3.892014 %). |

> **w040 is a training-set sheet of `ink_9um`.** villa's training config lists it among the model's five native
> 9.362 µm training segments (VERIFIED,
> [`RULES.md:3236`](https://github.com/abundantjoe/hercules/blob/661ff64/RULES.md?plain=1#L3236) `@661ff64`). Everything
> below is therefore a best case on training data. It shows how the tools behave, not how sensitive they are on
> unseen text. On held-out known text from PHerc0841, the same model transfers at pixel level (forward AUC 0.8393,
> reverse 0.5486), but the frozen unit screen flags 1 of 60 valid units (MEASURED,
> [`RULES.md:3296`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3296) `@7925b3a`).

## What each step shows, and the recorded output

| Step | Tool | Recorded output (**A** = asserted by `check_quickstart.py`; *p* = printed, not asserted) |
|---|---|---|
| 1 | `extract_w040_window.py` | three `PASS ... pixel sha256 ... matches the record` lines. Enforced by the script itself: a mismatch is a hard error and stops the run. |
| 2 | `read_chart.py --maps-only` | **NOT ESTABLISHED** (A), 1 flagged of 4 valid 0.5 cm² units (A). Margins (forward − reverse): (0,0) +0.0592, (0,1) +0.0767, **(1,0) +0.0818 flagged**, (1,1) +0.0405 (A, with each unit's forward and reverse mean), so all four are positive on known text (A). Whole-window margin +0.0596 (A). Depth-swap tripwire silent (A). The flagged unit is the one with the most labelled ink (φ = 0.1176). |
| 3 | the same read with the depth orders swapped | the signed rule says **BLANK** (0 of 4) (A), and the **depth-swap tripwire fires** (A). A surface traced with its normal pointing the wrong way is caught; its ink is not silently lost. |
| 4 | `map_integrity.py --pair` and `read_chart.py` on a reverse map with all but its top-left quadrant zeroed | both **refuse** it. `quickstart.sh` stops unless `map_integrity.py` exits non-zero; its message is `PAIR: non-zero footprints differ by 0.7500 (> 0.02)` (*p*). `read_chart.py` writes no verdict (A). Without the guard, the same maps would report margins of +0.2402, +0.2620 and +0.3132 in the three 0.5 cm² units that extend beyond the kept quadrant (only the largest, +0.3132, is printed (*p*); +0.2402, +0.2620 and the three reverse means below come from `rule55.evaluate` on the same maps, the call `check_quickstart.py` makes, and only "largest margin > 3 × 0.0818" is asserted). Their true margins are +0.0767, +0.0818 and +0.0405. The zeroed pixels lower the reverse means of those units to 0.1166, 0.1207 and 0.0484. The simulation is the real 2026-09-19 failure: an inference that exited 0 with a reverse map non-zero on exactly 25.00 % of its pixels ([`RULES.md:1620`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L1620) `@750629f`). That map had produced an ADMITTED verdict, which was then withdrawn (RULES.md R-DEPTH). |
| 5 | `cluster_power.py --read-stats` | a 2 × 2 grid of valid units: P(≥ 1 four-connected flagged triple) at the control's own flag rate 7/71 = **0.0029** (*p*). This is a Monte Carlo estimate (20,000 trials, fixed seed; the script prints its standard error, 0.0004). On a 2 × 2 grid any three flagged units are four-connected, so the exact value is P(K ≥ 3) for K ~ Bin(4, 7/71) = 0.0035499. At the held-out rate 1/60 (R-HELDOUT) it is 1.8 × 10⁻⁵. Both exact values were computed for this page. A surface this small almost never produces a candidate, even when it is all text, so a negative from such a surface says little. |
| 6 | `check_quickstart.py` | `ALL CHECKS PASSED`, then `quickstart.sh` prints `Contact sheet: <out>/read/contact_sheet.png` |

The ten assertions of [`check_quickstart.py`](check_quickstart.py), in order:

1. the known-text verdict is NOT ESTABLISHED;
2. 1 of 4 valid 0.5 cm² units is flagged;
3. the per-unit table equals the record: forward / reverse / margin of (0,0) 0.3760 / 0.3168 / +0.0592,
   (0,1) 0.3567 / 0.2800 / +0.0767, (1,0) 0.3827 / 0.3009 / +0.0818 (flagged), (1,1) 0.3616 / 0.3212 / +0.0405;
4. every unit's margin is positive;
5. the whole-window margin is +0.0596;
6. the depth-swap tripwire is silent on the correctly oriented read;
7. with the orders swapped, the verdict is BLANK;
8. with the orders swapped, the tripwire fires;
9. `read_chart.py` refused the truncated pair and wrote no `read_stats.json`;
10. without the guard, the largest unit margin on the truncated pair is more than 3 × 0.0818 (it prints +0.3132).

The contact sheet (`examples/out/read/contact_sheet.png`, reproduced in `docs/figures/fig1_known_text_read.png`)
shows CT | forward | reverse | per-unit margin with a 1 cm bar on every panel. The maps are shown as stored. The CT
panel shows the fibre weave and no visible letters. The forward map shows stroke-like shapes over the labelled text.
The reverse map, computed on the same pixels, does not. Gate A scores the full w040 canvas at AUC 0.99659 forward
and 0.49633 reverse against the human labels (VERIFIED,
[`RULES.md:14`](https://github.com/abundantjoe/hercules/blob/71720ce/RULES.md?plain=1#L14) `@e3a0717`; re-created byte for
byte in a fresh container, [`RULES.md:3271`](https://github.com/abundantjoe/hercules/blob/eed0fac/RULES.md?plain=1#L3271)
`@eed0fac`). These are training-set numbers, a best case. On held-out PHerc0841 known text the pixel AUC is 0.8393
forward and 0.5486 reverse, and the unit screen flags 1 of 60 units (MEASURED,
[`RULES.md:3296`](https://github.com/abundantjoe/hercules/blob/7925b3a/RULES.md?plain=1#L3296) `@7925b3a`).

## Using the tools on your own segment

Any forward/reverse pair written by `vesuvius.ink_detection.inference.infer --direction both` works:

```bash
UM=9.362    # um/px of YOUR volume, read from its metadata (9.362 is the w040 control's value)
python scripts/map_integrity.py --pair pred.tif pred_reverse.tif            # refuse a truncated pair (exit 1)
python scripts/read_chart.py render.zarr pred.tif pred_reverse.tif \
    --um "$UM" --out read/ --key 'PHercXXXX|my_segment|0|ink9um_seed42+plain|both' --ledger read/LEDGER.md
python scripts/cluster_power.py --read-stats read/read_stats.json         # could this surface yield a candidate?
```

`render.zarr` is the 28-slice surface volume (OME-Zarr group, array `0`, axes z y x, uint8). Its middle slice defines
the on-sheet mask. `--um` must come from the volume's own metadata: the reader has no default on purpose. With no
render, pass a mask or CT-slice TIFF in place of `render.zarr` and add the flag `--maps-only` (it takes no value):

```bash
python scripts/read_chart.py mask_or_ct.tif pred.tif pred_reverse.tif --maps-only \
    --um "$UM" --out read/ --key 'PHercXXXX|my_segment|0|ink9um_seed42+plain|both' --ledger read/LEDGER.md
```

See `docs/METHODS.md` for every parameter.
