# .signing

Provenance: Project HERCULES | owner the owner | [id removed]

Commits are SSH-signed by the cloud environment's provisioned signer (git config
`gpg.ssh.program`), not by a key generated in the project. `allowed_signers` lists the
signer public key extracted from the signature of commit ffcc2bf (2026-09-24). Verify
offline with `git -c gpg.ssh.allowedSignersFile=.signing/allowed_signers verify-commit <sha>`
using a stock `ssh-keygen` (the environment's signer program does not implement
verification). A per-session key generated earlier on day 0 was never used for any
commit and was deleted.
