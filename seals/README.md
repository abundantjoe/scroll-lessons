# seals/

Provenance: Project HERCULES | owner the owner | [id removed]

Only `age`-encrypted seals (`*.age`) live here. Each seal's sha256 is committed in
RULES.md before any render of its windows exists. The identity (private key) is
held by the scorer only, mode 0400, outside the repository, and every key read is
logged. The pre-commit hook rejects any other file in this directory.
