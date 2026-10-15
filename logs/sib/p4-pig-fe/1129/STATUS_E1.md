Provenance: Project HERCULES | owner the owner | [id removed]

# STATUS E1 (sub-sibling p4-pig-fe-e1)

STATUS: done. Both steps exited with rc=0. No code or parameter changes (base 654a7b7).

| step | command | result |
|---|---|---|
| maps | `python tools/sib/p4-pig-fe/strip.py maps E1 /tmp/fe1` | chunks 289883, absent_404 9977, secs 1211.6, T 8872, scale 1, blk 8, tiles 60, B_lo 82, B_hi 230 |
| score | `python tools/sib/p4-pig-fe/strip.py score E1 /tmp/fe1 logs/sib/p4-pig-fe/1129/scores_E1_raw.json --sigma0 1.0` | wall 244 s (real 4m4.2s), n_positions 70058674, tiles 60, eligible 60, scored 60 |

- maps_E1.npz: 2163055314 bytes, kept in /tmp scratch and not committed. Zip CRC check passed (5 members).
- The container restarted after maps finished (the file was written at 18:52Z and the final meta line was logged). Score ran afterwards on the same npz. Nothing was re-fetched.
- sigma0 = 1.0, so z = raw r. The parent divides by the control sigma0.
- No image, tile or CT pixel was viewed. Numbers only.
