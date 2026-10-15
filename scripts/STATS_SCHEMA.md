# Stats JSON schema shared by read_chart.py (writer) and review_folder.py (reader)

The reader (5.10, `scripts/read_chart.py`) writes `<read dir>/read_stats.json`; `review_folder.py` (5.12) also accepts a
flat `stats.json`. Both are recognised by file name; `review_folder.normalise` maps them onto one record.

## A. read_chart.py schema (`read_stats.json`, authoritative)
| record field (review) | read_stats.json path |
|---|---|
| scroll, surface | `key` = `scroll|surface|depth offset|checkpoint+TTA|order`, first two fields |
| um | `um_per_px` (from the volume's metadata.json, never a default) |
| verdict | `verdict` (BLANK / NOT ESTABLISHED / PROMISING CANDIDATE / UNREADABLE / ...) |
| fwd_mean, rev_mean | `maps.fwd_mean`, `maps.rev_mean` (on-sheet, 0..1) |
| frac_gt_05, frac_gt_075 | `maps.fwd_frac_gt_0p5`, `maps.fwd_frac_gt_0p75` |
| flagged_05, valid_05, largest_cluster_05 | `rule55.units["0.5cm2"].n_flagged`, `.n_valid`, `.largest_cluster` |
| flagged_1 | `rule55.units["1cm2"].n_flagged` |
| sheet_png | `contact_sheet.path` |
| forward_tif, reverse_tif, render_zarr | `inputs.forward`, `inputs.reverse`, `inputs.render` (render ignored when `maps_only`) |
| eligible | optional top-level `eligible` (true/false); if absent, scroll on the section-1 list (`verify_package.ELIGIBLE`) |

Paths may be absolute or relative to the read directory (or its basename inside the read directory).

Detection: a stats file is the read_chart schema if it has `key` (or `maps` / `rule55`). An UNREADABLE read carries
`key`, `um_per_px`, `verdict` but no `maps`, `rule55` or `contact_sheet`; the missing numbers become `-` in INDEX.md.
`review_folder.py` only consumes a `read_stats.json` whose directory also holds `.read_complete` (read_chart.py's
marker, written last), so half-written reads are skipped in --loop mode. Two reads of the same scroll|surface (other
depth / checkpoint / order) get the remaining key fields appended to their sheet and overlay basenames.

## B. flat schema (`stats.json`), for any other writer
`scroll, surface, verdict, um, fwd_mean, rev_mean, frac_gt_05, frac_gt_075, flagged_05, valid_05, largest_cluster_05,
flagged_1, sheet_png, forward_tif, reverse_tif, render_zarr, eligible` -- same meanings as above; optional `key_tag`
(string) to disambiguate two reads of one segment. No marker is required for the flat schema.
