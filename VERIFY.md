# How to verify this project independently (OWNER-STANDING-ORDER-4 item 4)
Provenance: Project HERCULES | owner the owner | [id removed]

Everything here is plain text in this repository. The sha256 values are fingerprints, not encryption. Each one lets you confirm that a file you can read is byte-for-byte the file that was declared before any result existed.

## 1. The decision log has not been rewritten
```
PYTHONPATH=src python3 -m hercules.records.rules_append verify
```
RULES.md is append-only, and each entry carries the sha256 of the previous one. The command re-computes the whole chain and prints OK, or the first entry that breaks it. Git history (`git log -p RULES.md`) shows every append, with its time.

## 2. The code, briefs and schemas used for a result are the ones declared beforehand
Each METRIC-HASH-NN entry in RULES.md lists `sha256  path` lines. To check one entry against the current files:
```
awk '/^## METRIC-HASH-38$/{p=1;next} /^## /{p=0} p' RULES.md | grep -E '^[0-9a-f]{64}  ' | sha256sum -c
```
Replace 38 with any entry number. To check a file as it was at the commit that scored a result, use `git show <commit>:<path> | sha256sum`.

## 3. The blind reads happened as recorded (remote harness batches)
For each batch, `tools/p4/rh_verify.py` re-checks 12 items from the harness sibling's own commits:
- the keys and jobs were committed before any reader ran (commit A before commit B);
- the image files are the ones listed;
- every reader was given exactly the frozen brief;
- the transcripts' timestamps come after commit A;
- the sealed answer equals what the reader wrote.
Its outputs are logs/p4/rh_verify_<batch>.json. Reader transcripts (gz) are in each harness branch under logs/sib/rh-*/.../B/transcripts/.

## 4. Re-scoring without any key
Reader answers are sealed (encrypted) only until a channel's final verdict, so that no one can peek while reads are still under way. After the verdict they are committed in plain text under logs/p4/unsealed/<batch>/ (only while this repository is private). Every census number can then be recomputed from those files, the batch keys and tools/p4/score_p4.py.

## 5. What each result claims
- Every result entry in RULES.md names its declaration, its inputs (with sha256) and its outputs.
- CHANGELOG.md records each action in time order.
- logs/owner/INBOX.md records each owner request and what was done about it.
