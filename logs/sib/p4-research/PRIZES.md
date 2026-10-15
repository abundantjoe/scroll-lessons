# Open Vesuvius Challenge prizes, ranked for fastest money (sibling p4-research)

Provenance: Project HERCULES | owner the owner | [id removed]
Serves: orchestrator task of 2026-09-26 21:42Z. Owner, 21:36Z, verbatim: "use only the ones that'll secure the fastest money - get all the lowest hanging fruit available to us so we can get the rest".
Status: v2 (complete), 2026-09-26 ~22:10Z.
Integrity:
- No image, tile or CT data was opened.
- The EXPECTED-TEXT section of DOSSIER.md was not read for this file.
- Only official organizer pages were used for rules.

## 0. Bottom line
1. **Fastest money: monthly Progress Prizes.**
   - The next deadline is **2026-09-30, 11:59pm Pacific**, four days away.
   - The July 2026 round paid $1,000 each for small, well-scoped tools, for example "a tool that detects intersections in tifxyz patches" and "a tool to check metadata in our open data catalog". The best submission of the month received $20,000.
   - Several of our validated tools are that kind of contribution (section 3).
   - Awards were announced about 6 days after the month closed (July round, post of 2026-08-06). Winners must supply payment information within 30 days.
   - **Hard gate: the owner's decision.** A winner "must … make it open source under a permissive license, publicly on GitHub, to accept the prize". Our repo abundantjoe/dominion appears private (unauthenticated github.com returned 404 at 21:47Z) and carries an MIT LICENSE.
   - Publishing is an outward-facing action. It needs the owner's explicit approval and a scrub for secrets, keys and sealed material.
2. **The milestone prizes (First Letters $50k per scroll; Paris 4 Title $50k; Grand Prize $1M)** are the "rest".
   - On our record their near-term probability is low: D1 FAIL, D3 NOT PASSED, no GPU, and the P4 title odds are "well under 3%".
   - Their review is slow ("We will acknowledge having received your submission within a week", then technical and papyrological review).
   - They are not the fastest money. Keep them as the long lane.

## 1. Catalogue of every open prize
All quotes are from https://scrollprize.org/prizes, fetched 2026-09-26T21:42:51Z (raw HTML sha256 9688cbb7cea853bc...). The page states "Open prize pool $2,140,000".

### 1.1 2027 Grand Prize: $1,000,000 total
- **Award:** "$800,000 to the first team or individual to fully unroll and make readable a scroll from the set below". Also "second place ($100,000), third place ($50,000), and fourth place ($50,000)".
- **Eligible scrolls (13):** PHerc0125, 0191, 0211, 0257, 0268, 0358, 0800, 0813, 0826, 1203, 1218, 1447, 1545.
- **Key requirements (quoted):**
  - "100% of the papyrus recto surface unrolled";
  - "Verify that at least 70% of each counted column's preserved characters are legible";
  - "Pipeline should be seamlessly integrated in the VC3D software";
  - "The unrolling pipeline should be fully automated; up to 8 documented hours of human annotation / input are tolerated";
  - "Any dataset created or used to train ML models must be published publicly, under a CC-BY-NC 4.0 license";
  - "Data derived from higher resolution scans of the submitted scroll volume cannot be used";
  - "To qualify, you must have registered on the Vesuvius Challenge Discord at the time of the submission".
- **Deadline:** June 25th, 2027 (11:59pm Pacific).
- **Review:** "We will acknowledge having received your submission within a week. Depending on the difficulty of verifying your methodology, it might take longer". Then papyrological scoring per column.
- **Payout time:** months. Out of reach for this project (no GPU; 0 legible letters on unseen text).

### 1.2 First Letters Prizes: $50,000 per scroll, up to 10 scrolls
- **Award:** "$50,000 to the first team that uncovers 10 letters within a single 4 cm² area of that scroll — and open sources their code, data, model weights and results (after winning the prize)". The maximum is 10 scrolls.
- **Eligible volumes (22):** PHerc0125, 0175A, 0175B, 0191, 0211, 0257, 0268, 0306B, 0343, 0358, 0483A, 0483B, 0490A, 0490B, 0800, 0813, 0826, 0846A, 0846B, 1203, 1218, 1545. PHerc1447 is no longer on this list; 0841 is not on it either.
- **Key requirements (quoted):**
  - "an image of the virtually unwrapped segment, showing at least 10 visible and legible letters within a single 4 cm² area";
  - "should not contain manual annotations … This includes annotations that were then used as training data and memorized by a machine learning ink model";
  - "Annotate the rows of text";
  - "False-positive mitigation"; "Held-out validation".
- **Deadline:** June 25th, 2027. The review bar is "deliberately high — we'd rather be slow than wrong".
- **Note (quoted):** "Sometimes ink is visible directly in the flattened render, with no model at all (usually it shows up as bright areas). If that's already enough legible letters, that by itself qualifies for the prize."
- **Changed since our recon:** the amount is now $50,000 (the 2025 posts said $60,000).

### 1.3 PHerc. Paris 4's Title Prize: $50,000
- Full rules are in DOSSIER.md section 3.1 (unchanged; re-fetched now).
- Key text: "The expected title region has shown no detectable ink so far — possibly a different ink, and the top rows are physically missing".
- **Deadline:** June 25th, 2027. Submissions "remain open until the prize is won".

### 1.4 Progress Prizes (monthly)
- **Award (quoted):** "Best Submission of the Month: $20,000, guaranteed every month, to the single best submission". Also "progress prizes will be awarded at a range of levels based on the significance of the contribution, typically $20,000, $10,000, $5,000, $2,500, $1,000, $500 or $250".
- **Criteria (quoted):** "We favor submissions that:
  - Are released or open-sourced early …;
  - Actually get used …;
  - Improve results quantitatively and/or qualitatively on real data …;
  - Resolve outstanding bugs in tools that people are using …;
  - Reveal insightful, actionable information … detecting failure-cases of existing methods on real scroll data …;
  - Are well documented."
- **Core requirements (quoted):**
  - "Address a specific challenge using Vesuvius Challenge scroll data";
  - "Provide clear implementation path and a demonstration of its use";
  - "Demonstrate significant advantages over existing solutions";
  - "Include comprehensive documentation";
  - "Accept standard community formats (e.g. OME-Zarr or Zarr arrays, tifxyz quadmeshes, triangular meshes)";
  - "Designed for modular integration".
- **Also eligible (quoted):** "Any contribution that makes any of the Open Problems easier to address"; "Improvements to VC3D". The wishlist is the villa issues labelled "help wanted" (https://github.com/ScrollPrize/villa/issues, fetched ~21:48Z). Open issues there:
  - #191 "Surface and Fiber Predictions in Compressed or Highly Curved areas";
  - #192 "Accurate 3d ink labels";
  - #193 "Methods for generating surface, fiber, or ink labels".
  All three are labelled "Good candidate for a Progress Prize".
- **Cadence (quoted):** "Submissions are evaluated monthly, and multiple submissions/awards per month are permitted. The next deadline is 11:59pm Pacific, September 30th, 2026!" Submission is via the Submission Form (Google Form).
- **Evidence of what wins** ("$335k awarded in July", Substack 2026-08-06, sha256 44312380511ed081...):
  - "The team reviewed 58 submissions … $33,500 has been awarded to 13 teams and individual contributors".
  - $20,000 to ScrollFiesta (a meshing pipeline integrated with VC3D);
  - $2,500 to an unwrapping pipeline;
  - $1,000 each for small items: a metadata checker ("a tool to check metadata in our open data catalog"), a tifxyz metadata fixer, "a tool that detects intersections in tifxyz patches", zarr-reading PRs, spiral-fitter fixes, "an update to the ink tutorial that includes proper validation data".
  - About 13 of 58 submissions won, a base rate of about 22% per submission.
- **Time to payout:** the July round closed 07-31 and was announced 08-06, about 6 days later. Terms: "Prize winner must provide payment information to Scroll Prize, Inc. within 30 days of prize announcement to receive prize". The actual transfer time is not published (UNCERTAIN).

### 1.5 General terms (quoted from the same page)
- "Prizes are awarded at the sole discretion of Scroll Prize, Inc. …"
- "You agree to make your method open source if you win a prize. It does not have to be open source at the time of submission, but you have to make it open source under a permissive license to accept the prize."
- "Submissions for milestone prizes will close once the winner is announced and their methods are open sourced."
- For milestone prizes: "you must not make your discovery public until the prize is officially announced".
- Content licence: the site says "Content licensed CC BY-NC 4.0 unless otherwise specified".

### 1.6 Other items, not open or not applicable
- The Kaggle "Vesuvius Challenge – Surface Detection" competition ($200,000, November 2025) is closed. Source: https://scrollprize.org/2026_open_problems, fetched ~21:45Z, sha256 d75dfe6c74fb8032...
- "Refer a successful hire — earn a $5,000 prize" (Substack 2025-05-01) is not listed on the current prizes page. Status UNCERTAIN, and not relevant.

## 2. Ranking by expected value per hour, for this project
EV = P(award) x amount / hours. All probabilities are our judgement (UNCERTAIN), anchored on the July base rate (13 of 58, about 22%; small tools $1,000) and on our own verdict record (STATE.md).

| Rank | Prize / submission | Our P(award) | Amount if won | Hours to submit | EV/h | Time to money |
|---|---|---|---|---|---|---|
| 1 | Progress: **flatcheck**, a flattening-quality checker for tifxyz plus a documented ABF++ failure mode (flat1) | 0.45-0.6 | $1,000-5,000 | 8-12 | ~$60-300 | Sept 30 round: announcement ~Oct 6, then payment |
| 2 | Progress: **tifxyz-dist**, exact point-to-surface distance and a train/prediction overlap check (p4-excl surfdist) | 0.35-0.5 | $1,000-2,500 | 6-8 | ~$50-200 | same |
| 3 | Progress: **handcheck**, a handedness/orientation checker for tifxyz renders (handed) | 0.35-0.5 | $1,000-2,500 | 6-8 | ~$50-150 | same |
| 4 | Progress: published inter-scan affines plus the regrescan tool (PHerc1203 PASS; honest FAILs) | 0.25-0.4 | $500-1,000 | 4-6 | ~$30-100 | same, or October |
| 5 | Progress: **subcheck**, a reproducible-submission verifier (factory) | 0.25-0.4 | $1,000-2,500 | 10-14 | ~$20-100 | October round |
| 6 | Progress: tracer bridge/fold gate for VC3D (upstream PR) | 0.2-0.35 | $1,000-5,000 | 15-25 (its T3 FAILs; needs the docker build) | ~$20-80 | October or later |
| 7 | Progress: blind-read false-positive harness plus injection-recovery detection limits (harness, p4-highz) | 0.2-0.35 | $1,000-5,000 | 20-30 (de-projection: hard-coded key, RULES hashes) | ~$15-60 | October or later |
| 8 | First Letters ($50k per scroll) | ≤ 0.02 by 2027-06 on current evidence | $50,000 | hundreds, and it needs a GPU | ≤ ~$5 | months |
| 9 | Paris 4 Title ($50k) | ~0.01-0.03 | $50,000 | 50-150 | ~$5-20 | months |
| 10 | Grand Prize | ~0 | $0.8M | n/a | ~0 | n/a |

The best-of-month $20,000 is possible only for a contribution the community adopts widely. In July it went to a meshing pipeline integrated with VC3D. None of ours is in that class now (P ≤ 0.05).

Why the progress prizes rank first:
- The review is monthly and guaranteed.
- The bar is "significance", not a legibility threshold.
- Our tools already exist and are tested.
- Several tools map directly onto what every milestone submission must prove: no training/prediction overlap, a low-distortion flattening, and false-positive mitigation. That is an "Open Problems" and community-use argument.
- Hours are packaging (README, CLI, demo on public data), not research.

## 3. What we would submit
The asset evidence comes from the sibling-branch inventory of 2026-09-26 ~22:05Z. Test counts marked "re-run" were re-executed on a git-archive export. Each submission is **a new, minimal public repo** under the owner's account, not abundantjoe/dominion. Each needs a README, a CLI, a demo on public data, and before/after numbers.

### 3.1 flatcheck (rank 1; for the Sept 30 deadline)
- **Source:** sib-flat1, `tools/sib/flat1/{flatpkg.py, flatlib.py}`, with `tests/sib_flat1_test_{flatten,pkg}.py` (re-run: 18 pass, 2 skip).
- **What it offers:**
  - The isometry metric per tifxyz: % of quads within ±5 %, fold-overs, and area and angle distortion.
  - A collapse detector.
  - SLIM and ARAP re-flattening as alternatives.
- **The actionable finding** (the "detecting failure-cases of existing methods on real scroll data" criterion):
  - On 10 hard curved windows, the official ABF++/vc_flatten passes the bar 0/10, against SLIM 3/10 and ARAP 4/10. SLIM is ≥ vc_flatten in 33/33 comparisons.
  - ABF++ collapse cases have 22-34 % of quads within ±5 % and up to 12 flips.
  - Every milestone prize requires "a low-distortion isometric 2D parametrization", so the checker is directly useful to every entrant.
- **Gaps:**
  - strip the project paths and provenance/governance references;
  - drop the RULES hash coupling;
  - package the libigl dependency;
  - write one demo notebook on a public segment.
  - The ABF path needs the VC3D docker image, so document it as optional.
- **Effort:** 8-12 h.
- **Risks:** the organizers may already track distortion internally. Mitigate by showing concrete failing public segments, with their IDs, and SLIM fixes. **Do not include Paris 4 title-strip numbers** (p4_flat.json covers the P4 strips: search intelligence).

### 3.2 tifxyz-dist (rank 2; for the Sept 30 deadline)
- **Source:** sib-p4-excl, `tools/sib/p4-excl/{surfdist.py, test_surfdist.py, dense_tile.py}` (re-run: 21/21 pass; on-surface max error 1.6e-11 vox).
- **What it offers:**
  - The exact point-to-triangle distance from any points or mesh to a tifxyz. It uses a KD-tree with a proven covering bound, so it needs no densification. Its outputs are certified lower and upper bounds.
  - Use cases: the "no overlap between training and prediction regions" check that all three milestone prizes demand; the minimum clearance between a candidate region and the training segments; and mesh-to-mesh spacing and intersection.
- **Advantage over July's intersection tool:** exact distances with bounds, and a train/prediction clearance certificate rather than only self-intersection.
- **Gaps:** the CLI, the README and a public demo, for example clearance of official segments against the public ink-label segments. The contamination unit grouping (sib-contam) is **not** included: its real-data gate still fails (`all_caught: false`).
- **Effort:** 6-8 h.
- **Risks:** it overlaps with July's tifxyz-intersection award. Show the differences explicitly.
- **The demo must not use Paris 4 w010-027/w028-037 flags.** They reveal where our title search looks.

### 3.3 handcheck (rank 3; for the Sept 30 deadline)
- **Source:** sib-handed, `tools/sib/handed/pkg/src/hercules/geometry/handed_rule.py` and the tests (re-run: 55 pass, 1 skip; 69 synthetic tests on the branch).
- **What it offers:**
  - From mesh chirality × frame parity, it predicts whether a render reads mirrored.
  - Planted glyphs read correctly 32/32, and the wrong-sign control comes out mirrored 32/32.
  - On official meshes, every one on 0139, 0009B, 0841 and 0800 is predicted unmirrored, and **9 of 15 PHerc1447 meshes are flagged**. That is directly "actionable information" for the organizers.
- **Gaps:** decouple it from the hercules package; add a CLI over a folder of tifxyz; write the README.
- **Effort:** 6-8 h.
- **Risks:** the 1447 flags must be double-checked before any claim. Report them as flags, not errors.

### 3.4 Inter-scan affines (rank 4)
- **Source:** sib-regrescan (`regrescan.py`, `final_affine.json`; re-run collected 11 passing tests against 29 reported, so resolve the discrepancy first), plus the reg0841 negative result.
- **Offer:**
  - a 4×4 affine for PHerc1203, 9.36 ↔ 2.40 µm (held-out r 0.879, RMS 0.73 vox);
  - the PHerc0846A attempt, honestly marked FAIL on r;
  - the finding that no single affine fits PHerc0841.
- **Effort:** 4-6 h.
- **Risk: the Grand Prize rule** "Data derived from higher resolution scans of the submitted scroll volume cannot be used". Label the affines clearly so that no entrant misuses them. The value is lower than 3.1-3.3.

### 3.5 Later rounds (October onward)
- subcheck (factory verifier, 49/49 tests re-run);
- the tracer bridge/fold gate (a VC3D PR; T3 must pass first);
- the blind-read false-positive harness plus P4-F injection-recovery limits (needs de-projection: the hard-coded age key, RULES hashes, /srv paths);
- the depth-calibration false-PASS trap (p4-depth: its PASS rule passes 25/100 noise sheets) as a documented pitfall.

### 3.6 Owner actions needed (none can be done by siblings)
1. Approve making specific tool code public in new repos, under MIT (already the repo licence).
2. Submit via the Submission Form (https://docs.google.com/forms/…, linked on the prizes page) by **Sept 30, 11:59pm Pacific**. Join the Discord and post each tool, because adoption counts.
3. After any award, provide payment information within 30 days.

## 4. Risks and rules
- **Publishing the code** (a public GitHub repo, permissive licence) is required only to *accept* a progress prize. The Submission Form can be sent before publishing.
  - Publishing is outward-facing and irreversible (it can be cached and indexed). **It needs the owner's explicit approval.**
  - Before any publish: a secret scan and a scrub.
    - No /srv/scorer keys, sealed answers, age keys or tokens.
    - No blind-read outputs that could reveal P4 lead locations.
    - No EXPECTED-TEXT.
  - Publish **a new minimal repo of the tool only**, not abundantjoe/dominion.
- **Disclosure of milestone work:** "you must not make your discovery public until the prize is officially announced". Our Paris 4 layout analysis (DOSSIER section 4, windows A and B) is search intelligence, not a discovery.
  - Publishing it would help competitors and gains little as a progress prize. **Keep it private** until the title search closes.
  - The same applies to any P4 census or lead numbers.
- **Organizer data:** the site content and data are "CC BY-NC 4.0 unless otherwise specified". Tools that *read* public data are fine. Demo outputs derived from the data should be shared under CC BY-NC 4.0 with attribution.
- **Discord:** registration is required "at the time of the submission" for the Grand Prize. It is not stated for progress prizes. The owner should hold a Discord account anyway, because the community-use signal counts ("Actually get used").
- **Duplication risk:** July already rewarded "a tool that detects intersections in tifxyz patches" and metadata checkers. Our submission must show a clear advantage, for example exact point-to-triangle distances with a covering bound (21 of 21 synthetic tests, a certified threshold) and the train/prediction-overlap certificate that the milestone rules require.
- **Timing:** the Sept 30 deadline leaves about 4 days. Packaging one or two tools is feasible. A late entry rolls into the October round (deadline presumably Oct 31; UNCERTAIN until posted).

Integrity: no issues (v2).
