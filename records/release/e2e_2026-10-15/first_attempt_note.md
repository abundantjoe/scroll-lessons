# The interrupted first attempt (2026-10-15)

- 10:12:13 UTC: `scripts/reproduce_control.sh /home/user/hdata/e2e/work` started on an empty work directory (console,
  first lines). Step 1 fetched inputs, checkpoint and labels; step 2 started inference at 10:15:31 UTC.
- About 10:21 UTC (about five and a half minutes into inference) the container restarted (`uptime` at 10:23:26 UTC read "up 2 min"), which killed the inference.
- Observed at about 10:24 UTC, after the restart: the work directory's `out/` held only `infer.err` (837 B; last line
  `10:16:06 INFO Selected 11076 patches for inference`) and `infer.log` (2073 B). No TIFF existed. Both logs were
  deleted before the relaunch, so this listing is recorded here from the session, not as a file.
- Supporting inference: villa writes each map in one `tifffile.imwrite` call after all of that direction's patches
  (`write_output_tiff`, `infer.py` at 5ab585f). The relaunched run's forward pass ran from 10:25:54 to 11:11:16 UTC
  (45 min 22 s, `infer_stderr.log`), so no map could have been written about five and a half minutes in (INFERENCE).
- 10:25:30 UTC: the same script was relaunched on the same work directory (a NOTE line in the console). It skipped the
  fetch, whose outputs existed, and ran from step 2 to the end (12:00:42 UTC).
- Added later the same day: the deletion was `rm -f <work>/out/infer.err <work>/out/infer.log`, run in the same shell
  command that appended the NOTE line to the console and relaunched the script (10:25:30 UTC).
