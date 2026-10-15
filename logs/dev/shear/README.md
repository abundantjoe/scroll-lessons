# Shear-line detector, development record (DECL-UNR-1 item 3)

Provenance: Project HERCULES | [id removed]. Tool: `tools/unr/shear_lines.py`. Data: PHerc0268 OME level 0 (8.64 um),
y-slab 5820..5835, z 7936..8704, x 1280..2304 (768 x 1024 per section, fetched with `core_native.L0.slab`, 48 chunks,
5 s); held-out null slab at y 7900..7915, same window (91 % in mask). No letters, no readings are claimed.

## Result against the bar

The bar of the brief (every injected shear line flagged within +-2 sections of the injection, 100 % of >= 20 placements,
at a declared false-positive rate on un-injected sections) is NOT met. The numbers are in `strict/control.json`
(declared rate 0.5 segments per section) and `permissive/control.json` (declared rate 10 per section); see the table
below. The reasons are measured, not guessed, and are recorded here because they bear on item 3 as declared.

Two operating points, both declared before any injected section was read (threshold T_d = 99th percentile of the
null window coherence drops = 0.0784; run length n_min set by the declared rate on the null slab; 17 angles at 5 deg;
352-row windows at stride 16; 65 placements = 20 lines x {half 22 vox, one declared 44 vox, one local pitch 39-45 vox}
+ 5 two-spacing 88 vox; injected sections 4..11 of 16; a hit = a segment within 12 vox and 7.5 deg of the injected line).

| operating point | declared FP/section | n_min | null FP/section (calib. slab y5820) | held-out null FP/section (y7900) | half: within +-2 / any section (of 20) | one declared (of 20) | one local pitch (of 20) | two spacings (of 5) | all classes within +-2 |
|---|---|---|---|---|---|---|---|---|---|
| strict | 0.5 | 22 windows | 0.25 | 0.62 | 0 / 3 | 0 / 4 | 0 / 8 | 1 / 2 | 1 of 65 (1.5 %) |
| permissive | 10 | 11 windows | 9.6 | 10.3 | 2 / 10 | 4 / 15 | 5 / 13 | 1 / 4 | 12 of 65 (18.5 %) |

"within +-2" = flagged in every injected section and in no section farther than 2 from the injection (the brief's
criterion); "any section" = flagged in at least one injected section. Mean fraction of injected sections flagged at the
permissive point: half 0.32, one declared 0.44, one local 0.47, two 0.62 (the cut's coherence drop grows with the slip,
and an integer slip is NOT harder for this signal than a fractional one: the detector sees the cut, not the phase).
Detection is a property of the line's location, not of the slip class: at the permissive point lines at x0 = 940 (right
edge) were never flagged in any class, x0 = 380 at 35 deg and x0 = 520 at 0 deg were flagged in every injected section
for every class, and the fibrous centre (x0 = 660) was intermittent. False positives on the placement stacks match the
null (strict 0.50 / permissive 8.5 per un-injected section); 13 permissive placements spilled by one section (section 12).
Slip: no segment reached status MEASURED at the strict point (0 of 65 placements); the permissive run skipped the slip
stage (--no_slip) after the strict run and a direct test showed it non-performing (own-match peaks 0.1-0.4, no agreed
reference). Slip sign and magnitude are therefore not delivered.
Runtime: strict 32 min, permissive 26 min, 3 processes each, 16 sections x 17 angles x 65 placements.

## What was measured on the real section (why a phase test fails here)

All numbers from the un-injected section y = 5828 unless stated; scripts in the session scratchpad, reproduced by the
functions of the tool.

1. The region is not a periodic horizontal stack. At 8.64 um it is a wavy, braided packet: sheet-scale slopes change by
   more than 0.5 over 8-16 voxels laterally, fibre bundles cross at tens of degrees, and clear sheet/gap laminae exist
   only in the lower-left quarter (x < 400). Peak statistics on vertical profiles (prominence >= 3 MAD): pitch median
   47 vox (p10 19, p90 98), sheet width median 14.5 vox; the declared "one spacing" of 44 vox is the census median.

2. Lateral decorrelation of the texture. Normalised cross-correlation of a band on one side of a line against the band
   on the other side (continuity, best small shift), as a function of the gap D between band centres:
   single columns, Gaussian 1 along z: D = 12: 0.32, D = 24: 0.25, D = 36: 0.20;
   8-12-column bands with fibre-scale oriented averaging (tensor sigma 2/8): own-peak median 0.31, and the matching
   shift of a candidate line agrees with its neighbour 4 vox away at 56 %, 12 vox away at 24 %, 24 vox away at 17 %;
   sheet-scale oriented averaging (tensor sigma 4/12, 32-vox average along the sheets): own-peak median 0.52, agreement
   4 vox: 79 %, 12 vox: 56 %, 24 vox: 45 %. Among nodes whose own peak is >= 0.45 (10 % of coherent nodes) the
   agreement is 98 % at 4 vox and 90 % at 12 vox; those nodes sit in the clear-lamina quarter, where the stack is
   locally periodic and the matching peak is often an integer alias of the continuity offset.
   Consequence: a two-sided band match cannot read the lamina phase across a line at this resolution in this region;
   neither a tensor-predicted continuation (errors of tens of voxels in the slope x gap product), nor a neighbour-based
   reference, nor a +-2 or +-4 section aperture, nor z-blur or elastic sub-window pooling changed this (each was tested;
   the agreement figures moved by < 5 points).

3. Integer slips. A slip of exactly one local pitch of a periodic stack maps the lattice onto itself: no phase test can
   see it; only the cut itself (fibre continuity) and the aperiodic part of the stack can. In the clear-lamina quarter
   the stack is periodic enough that the band match prefers an alias; in the fibrous centre the texture is aperiodic but
   decorrelates laterally before a match is reliable. This is a property of the data, not of a parameter choice.

4. What every injected cut does produce is a line of lower structure-tensor coherence (fibre scale, sigma 2/8): the
   window drop on the injected line exceeds the null 99th percentile in 13 % (half spacing), 20-22 % (one spacing) and
   38 % (two spacings) of its windows, 46-60 % above the 95th percentile. Chained along the line (352-row windows,
   stride 16) with the threshold at the null 95th percentile and the run length set by the null, single-section
   detections were 2-4 of 5 vertical test lines for every slip class, the two misses being the faint fibrous centre
   (x = 660) and the right edge (x = 940). The un-injected section itself carries long lines of the same kind at the
   same places in every section (x ~ 56, 228-290, 344, 865; fold hinges, the lower-left seam, buckling-zone edges): with
   17 candidate angles the null run length needed for 0.5 false segments per section (28 windows) exceeds the longest
   injected run (27), which is why the strict operating point detects nothing. The on-line intensity dip does not
   separate them (|dip| < 0.02 on both), i.e. these are not dark gaps but genuine coherence boundaries.

5. The slip measurement on detected segments (one-sided sheet-scale textures over the whole segment, reference from
   parallel lines 12-24 vox away) returned own-match peaks of 0.1-0.4 and no agreed reference on either the null lines
   or the injected lines: status UNKNOWN throughout. The sign and magnitude of the slip are therefore not delivered by
   this tool in this region.

## What the tool delivers as it stands

Per section: candidate discontinuity segments (endpoints, angle, coherence drop mean/max, number of windows, on-line
intensity dip, slip status and, where the band match is strong and agreed, slip in voxels with sign), linked along y
with persistence. It is a detector of coherence-cut lines, calibrated on the null, with the slip measurement attached
as a separately reported, currently non-performing stage. It is not a validated shear-line detector.

## What would be needed (not done here, for the orchestrator's decision)

- A positive control on the W1 phantom (DECL-UNR-1 item 8) rather than on this fibrous window: the phantom's stack is
  what a phase test assumes, and the detector's integer-slip performance there is the fair measurement of the method.
- A different observable for real data: tracked ridge identities (X1's own lamina ids) counted between two long-lived
  reference laminae on both sides of a candidate line (an integer slip changes the count by one); this uses the
  sheet-scale continuity over millimetres instead of texture over tens of voxels, and is the quantity DECL-UNR-1 item 3
  calls the ridge phase.
- A window chosen by the X0 survey where the stack is separable and coherent (the lower-left quarter here) and lines
  placed inside it, with the local pitch regularity recorded per placement so that integer-slip visibility is stated per
  line rather than averaged.

## Deviations from the brief

- Environment: only the Python venv part of `docker/env/setup_env.sh` was built (`uv venv /opt/hv` + the package list);
  the Docker daemon, VC3D build and ink environment were not needed by this job and were skipped.
- Threads: all runs used <= 3 processes/threads.
- The detector's primary signal is the coherence drop, with the texture-match slip as a secondary measurement; item 3's
  wording ("lamina ridge phase discontinuous ... together with a local coherence drop") was pursued first and failed
  for the measured reasons above; six variants of the phase test were built and discarded before the design was fixed.
- Two operating points were run instead of one, both declared before any injected section was read.
