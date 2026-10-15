Provenance: Project HERCULES | owner the owner | [id removed]

# pairs0814b: open questions (work continues on the defaults)

Q1 Output paths. The pairs0814 code is run UNCHANGED, and it writes to hard-coded repo paths
   (logs/sib/pairs0814/{stage_a,registry,runs.jsonl}). DEFAULT: run it as is in this checkout; its outputs are then
   copied byte-for-byte to logs/sib/pairs0814b/{stage_a,registry,runs_code.jsonl}. Nothing is committed under
   logs/sib/pairs0814/ or tools/sib/pairs0814/ on this branch, so the two branches never collide.
Q2 Environment. docker/env/setup_env.sh hard-codes proxy port 46883; this container's proxy is on another port.
   DEFAULT: use tools/sib/pairs0814/setup_env_sib.sh + vc_build_sib.sh (the pairs0814 sibling copies, which take the
   port from HTTPS_PROXY; otherwise identical, same villa SHA, deps image, checkpoint sha256).
Q3 Shards. stage_b.py writes one npz per 1536 px block (<= 16 PASS patches, np.savez_compressed, same arrays and
   dtypes that stage C packs); packing into 20-patch shards is stage_c.py, which is not in this task. DEFAULT: push the
   stage B block npz files unchanged (each < 90 MB, sha256 per file, batches <= 500 MB) under
   data/sib/pairs0814b/blockpairs/<seg>/<by>_<bx>.npz; the registry rows' staged_sha256 matches the file. The
   orchestrator or pairs0814 packs them with stage C.
Q4 Root index. The organizer root metadata.json fetched here has sha256 8119d1c2... (identical to pairs0814's
   protocol_check), and the 9.362 um volume metadata.json sha256 7db0a497... (identical). DEFAULT: proceed; if a later
   fetch differs, stop and record it.
