# RESUME NOW: one-shot restart instructions (written 2026-09-25 ~20:30Z)

Provenance: Project HERCULES | owner the owner | [id removed]

The owner pasted "Read configs/prompt/RESUME_NOW.md and do it" into a fresh conversation. Do the following in order, without asking the owner anything. Nothing ever waits on the owner.

## 1. Load context (reading only)
- configs/prompt/hercules_master_v7.md, all of it. It points to the binding v6 prompt at /tmp/claude-0/-home-user-dominion/b19d92e8-9f98-5674-bc2b-8bf468fb8442/scratchpad/prompt_v6.txt. Read that too, and never reproduce its personal sentence about the owner.
- RULES.md: every entry from DECL-P4-1 onward. At the time of writing that means:
  - DECL-OFFLOAD-1
  - OWNER-CONFLICT-LABELS
  - CORR-RETRACE-RULE
  - REG-0841-R1
  - REG-0841-NA
  - DECL-AMX-1
  - anything newer.
- STATE.md, the tail of CHANGELOG.md, logs/sib/registry.json (19 sibling sessions, created on the owner's go-ahead at about 18:22Z to add compute), logs/p4/ (Paris 4 reconnaissance), and /work/d3/logs/infer_arms.log.

## 2. Commit and push first
`cd /home/user/dominion && git status --short`.
- Commit anything uncommitted, with the provenance trailer plus the session's attribution lines.
- Push with `git push -u origin claude/gifted-bell-gavnl5`, retrying up to 4 times.

## 3. Re-create the sibling sweep routine
This is the owner's standing request. Use create_trigger, firing into this session, every 40 minutes if allowed, otherwise hourly, with this prompt:

"HERCULES sibling sweep:
(1) check every sibling in logs/sib/registry.json (get_session, list_events):
  - answer any that are waiting for a decision, under RULES.md (read the ASK.md or REPORT.md on its branch);
  - nudge idle ones that have jobs in flight;
  - give finished ones their next task;
(2) harvest the results into CHANGELOG.md, then commit and push;
(3) check that the D3 waiter and jobs are running, and restart per hercules_master_v7.md section 2 if not;
(4) advance D3 and the Paris 4 title programme;
(5) confirm this routine is still armed."

Then run one sweep right away.

## 4. D3: all 4 arms are trained, and all maps finished at 19:51Z
Continue exactly as hercules_master_v7.md section 3.1 lays out:
1. `d3_build.py --full`
2. the stage-2 record, committed before the jobs
3. `d3_jobs.py`
4. the 24 sealed-output reads, audited
5. score_d3
6. the audit workflow
7. the D3-VERDICT record

Keep a background waiter plus a send_later fallback armed, because the container is reclaimed when the conversation is idle.

## 5. Paris 4 title (top owner priority)
Read logs/p4/recon.*. If it is missing, relaunch reconnaissance per DECL-P4-1 item 1. Then:
- P4-A, once the D3 CPU steps are done;
- DECL-P4-2, declared before any title-region map exists;
- P4-B.
Title words come only from imaging evidence.

## 6. Rules that must hold
- If a tool or safety check blocks an action, never reword or rework it to get past the block; tell the owner plainly.
- Only one conversation may orchestrate at a time.
- Owner messages start with "No submission ready" plus at most 3 lines, and end with "Integrity: none" or one line per integrity event.
