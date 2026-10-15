Provenance: Project HERCULES | owner the owner | [id removed]

# PROPOSAL: DECL-SG11-REFCAL-1 (for the orchestrator to declare, amend or reject)

**Purpose:** measure how often the SG 11 layout test passes on **genuine known text** read by the REF readers. This is the calibration adopted in the B8 answer (2026-09-25T19:41Z) and proposed for B9 and the pitch-CV bar (PROPOSAL-SG-LINESPACING-1, P4 and P5). The runner reports pass rates only. It never sets or changes a bar.

**Code, hashed before any use.** It has not been run on any real read.
- `hercules.sg.refcal`, staged at `tools/sib/sg/pkg/src/hercules/sg/refcal.py`, sha256 **669429e06050e1793b4e9eddf18f81c0eabb3ab3642a03cf196d854d7730e99a**
- `test_sg_refcal.py` (5 known-answer tests, synthetic reads only), sha256 **2f80176dcd0d392775c64f2b10b1ce7c0227c36c3f9442c6b3735077946da6ec**

**Proposed declaration text:**
1. **Material:** REF reads (reader-drawn boxes) of the sealed known-text bank windows already read in READ-CAL, D1-REF and the probes, as recorded reader-output JSON mapped to canvas coordinates. No new read and no image view is needed.
2. **Per window:**
   - agreed letters come from the SG consensus code (>= 2 readers, same identity, 150 px), with the member-median box;
   - then `gate.layout_metrics` runs with px/mm from the volume's metadata.json.
3. **Reported:**
   - the SG 11 pass rate and the pass rate of each component (rows, pitch CV, median height with SG semantics, and median height alone over windows with >= 2 qualifying rows);
   - the pass rate at each candidate B8 fraction bar in (0.5, 0.6, 0.7, 0.75, 0.8, 0.9);
   - the distributions of the height fraction, the pitch CV and the pitch / median letter height (p5 / p25 / p50 / p75 / p95);
   - the number of two-row windows.
4. **Decisions that may follow**, each declared separately and before any candidate exists:
   - the B8 fraction bar, if any;
   - the B9 two-row alternative (a pitch/height range);
   - a record of the SG 11 known-text pass rate as a disclosed limitation.
   No bar is lowered by this calibration. DECL-SG says "never lowered".
5. **Validation of the runner:** synthetic windows with a known pitch, height and row count give exact expected rates:
   - 3 regular windows: 100 % pass;
   - a 4-window mixture: 50 % SG 11, 75 % rows, 50 % height with SG semantics, 75 % height alone;
   - a 76 %-in-band window passes the SG and fails the 0.8 grid bar.
