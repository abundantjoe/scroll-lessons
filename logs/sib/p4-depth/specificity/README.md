Provenance: Project HERCULES | owner the owner | [id removed]

# p4-depth specificity harness (for the DECL-P4-18 L4 pre-gate; reuse unchanged)

These are byte-identical copies of tools/sib/p4-depth/{test_depth.py, depth.py, l2.py} at the commit that adds this directory.

**Generator:** `test_depth.synth_hist(layer_um, seed, n_px=40000, layer_um_thick=15.0, psf_sigma_slices=1.0, gaps=True, cover=0.05)`
- It returns per-slice uint8 histograms of shape (109, 256), at 2.4 um/slice, with the mesh at slice 54.
- Papyrus body: +-50 um, mean 110. Gaps: mean 40 (or body everywhere if gaps=False).
- Noise: SD 30, plus speckle at 5e-4.
- layer_um=None gives a no-layer sheet. Otherwise it adds a 15 um ink layer (mean 215, area cover 5 %) convolved with a Gaussian point-spread function of psf_sigma_slices.

**Harness:** `python3 test_depth.py [out.json]`
- It applies `depth.peak_verdict(depth.f_from_hist(hist, 203), depth.offsets_um())` to each case.
- Asserted cases (exit 0 only if all hold):
  - (a) layer + PSF gives d* within 5 um;
  - (b0) a noise-free uniform sheet gives STOP;
  - (c) counting identities hold.
- Reported cases:
  - (a_sharp) layer without PSF;
  - (b1) 100 iid-noise uniform sheets: 25/100 PASS;
  - (b2) 10 no-ink sheet+gap profiles: 10/10 PASS.
- To test another rule on the same sheets, keep synth_hist and the seeds (b1: 1..100, gaps=False, n_px=20000; b2: 1..10, defaults) unchanged, and swap only the verdict function.
- Re-run here: same b1/b2/asserted results as ../unit_tests.json.

sha256:
```
fa5e69c467760bcdf1895b9b85e99f40e4bb9b9980a99c6a5d9062c38db2f82c  test_depth.py
4f904f43fc1ec9389dd81aeb41e43d116a1ae1328db2b73cdc0dc6cef91acd55  depth.py
c6dad892e4fc1b3595ca57f329020f5646d5a57d6d7534b08f2b61eaa37806a1  l2.py
```
