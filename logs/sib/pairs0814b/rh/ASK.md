Provenance: Project HERCULES | owner the owner | [id removed]

# pairs0814b P4-O harness: questions (work continues on the defaults)

Q1 (2026-09-27 01:35Z) The o1 builder manifest is interim but not flagged partial.
ckpt-screen-b a1190c5 pushed logs/sib/ckpt-screen-b/p4o/PHerc.1667-iteration-5/manifest.json. It has no
"partial": true, but its commit is titled "interim iteration-5 manifest (3 tiles)". It holds 3 tiles, r0 c10,
r0 c14 and r1 c10, all in the title zone. There is no c0-c8 known-text tile, so the DECL-P4-14 item 3 gate is
impossible. With null no1 = ceil(3/8) = 1 drawn from o1's own 3 tiles, the N0 would be a rotated copy of one of the
3 census tiles in the same session, which is a weakened null.
DEFAULT: no o1 batch is built from this manifest; the batch name o1 is kept for the builder's data. o1 starts when
a manifest has >= 18 tiles, or when its commit is no longer labelled interim. From that manifest on, a manifest that
grows later is read as o1b (the rh-e2 l2a/l2b pattern: remainder only, own N0).
Alternative: read these 3 now as o1a (1 session). That costs one reader, but the null is degraded as described.

Q1 RESOLVED (2026-09-27 02:45Z) by DECL-P4-14-A2 item 4 and DECL-P4-14-A3 item 2. Iteration 0 is dropped and
batch o1 will not exist. Iteration 5 (ckpt-screen-b) is read in stages o2s1, o2s2, ...; iteration 4 (ckpt-screen-c)
in stages o3s1, .... A stage is read once its new tiles hold >= 3 gate tiles (c5-c8) and >= 4 title-zone tiles
(c9-c19). The 3-tile interim manifest (0 gate, 3 title) does not meet the rule.
