Provenance: Project HERCULES | owner the owner | [id removed]

# ASK (task amx), 2026-09-25

Each question gives my proposed default. Every default that I can apply myself under the integrity rules is already applied. The rest are orchestrator actions that I will not take myself.

1. **Declare DECL-AMX-1 as drafted (`proposals/decl_amx_1.txt`)?**
   Default: declare **AMX-TRAIN only**. Leave AMX-INF undeclared and keep C2-NT fp32.
   - Why: bf16 inference is forecast to fail the 99.9 % within-±2 bar (97.7-98.2 % measured on synthetic input through the official chain).
   - fp32 inference costs only about 3.2 min per 2 x 2 cm window.
   - Training is where AMX pays: about 2x per fine-tune.
   Applied by me: nothing. Declarations are yours.

2. **If AMX-INF is declared anyway: who produces the w044 maps?**
   Default: an orchestrator-authorised job.
   - Steps: re-render the C3-NT-R1 crop, run the fp32 re-run (which must match sha256 `1d540b92...` / `addbb866...`), then the bf16 run via `tools/sib/amx/infer_bf16.py`, then `amx_gate.py`.
   - I am not permitted to map real data.

3. **AMX-TRAIN P16 wrapper**
   Default: `tools/sib/amx/d3_train_bf16.py` (sha256 `4768879b...18ec`). It runs `tools/d3/d3_train.py` (sha256 `2943b1b6...f52f`) unchanged inside CPU bf16 autocast.
   - Run with `--arm CTRL --out <new dir>` and 3 threads, paired against the existing fp32 CTRL log.
   - Note: the trainer's own summary will still say "fp32" in its recipe field. The wrapper prints the trainer's sha256 so the run is identifiable.
   - The wrapper is written but not run, because no pool exists in this container and nothing is declared.
   Applied: wrapper written and committed.

4. **P32' calibration run** (a second fp32 run at 4 threads, measuring how far two fp32 runs drift apart)
   Default: yes, if AMX-TRAIN is declared. Cost is about 1.3 h. It is reported only, with no bar.

5. **int8**
   Default: dropped. No `torchao` install.

6. **Cached-feature / letter-context path**
   Default: parked as a measured prototype. Any training use needs its own declaration.

STATUS: DONE. The task is complete. The next task can start without waiting on any of these answers.
