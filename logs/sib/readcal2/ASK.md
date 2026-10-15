Provenance: Project HERCULES | owner the owner | [id removed]

# readcal2 ASK (numbered; each with the default I continue on)

1. RCPICK-1 window coordinates. The 33 READ-CAL picker windows (w053 24, w047 3, w024 6) are "used by READ-CAL"
   and must be excluded, but their coordinates exist only in /work/readcal/picker_key.json (a key file I must not
   touch) and in /work/readcal/bank_readcal.json, neither of which is in this container or the repo.
   Please publish the 33 (segment, y0, x0) (numbers only, not the key) to logs/readcal/ or answer here.
   DEFAULT: fail-closed reconstruction. I re-run the RCBANK-1 attempt-2 rule on a 256 px grid; if my candidate counts
   reproduce 251 / 165 / 1731, I exclude EVERY window that overlaps any reconstructed candidate lying on the 1024 px
   grid (a superset of the 33 if they sit on that grid, as RULES.md DECL-D1-A4 says for w053). If the counts do not
   reproduce, I exclude all three E0 segments' RCPICK-1-eligible area and say so. Either way the list flags it.

2. Tier N segments. "Clean PHerc0139" in the records = w024, w047, w053 (+ title strip, < 2 cm tall). Their non-base
   3-D neighbours w023 w025 w026 w037 w048 w049 w050 w051 w052 w054 w055 w056 w057 are excluded from D2 training
   entirely (pairs0139 exclusion.json), are not base-trained, and parts of them are other windings.
   DEFAULT: list them as tier N (flagged) beside tier E0; the picker sees E0 first; a tier-N window must pass the same
   base / used / sealed tests. Say "E0 only" to drop tier N.

3. PHerc0814. The far segments are ribbons (RCBANK-1: best window coverage 0.899 at 2 x 2 cm). They are also D2
   training material for the pairs0814 sibling.
   DEFAULT: list 0814 windows at coverage >= 0.75 (flagged "0814-ribbon"), and a chosen 0814 window + every segment
   same-papyrus with it (+16 vox) becomes a D2 hold-out (as devloop R6). Say "no 0814" to drop them.

4. Second reader model. The task says the orchestrator names the frozen reader plus one other model version.
   DEFAULT in the proposal: frozen model = "fable" (READCAL-FREEZE); the second is a placeholder <M2> for the
   orchestrator to fill before declaration.

5. Candidate images for the picker. DEFAULT: I do NOT push PNGs; tools/sib/readcal2/build_ref_windows.py rebuilds
   the K_D2-geometry REF displays of any listed window here deterministically (uuid names, manifest with sha256).
   Say "push" and I write small PNGs (1068 px, INTER_AREA, raw 0-255) under logs/sib/readcal2/img_candidates/
   without viewing them.

6. Base maps made here. For the exemplar noise model I ran the C2-NT base model on the two SEAL-J-D1 w053 blank
   windows only (organizer SV path, as C3 "teamsv"), never on any candidate window. Tell me if that must be recorded
   somewhere beyond logs/sib/readcal2/runs.jsonl and noise_psd.json.
