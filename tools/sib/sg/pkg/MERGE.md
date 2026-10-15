Provenance: Project HERCULES | owner the owner | [id removed]

# Merging the staged SG package

This is staged here because the builder's write scope is `tools/sib/sg/` (ASK.md Q1). The layout under `pkg/` is exactly the merged layout.

```
cp -r tools/sib/sg/pkg/src/hercules/sg src/hercules/sg
cp tools/sib/sg/pkg/tests/test_sg_*.py tests/
source /opt/hv/bin/activate && PYTHONPATH=src pytest -q          # plain pytest collects tests/test_sg_*.py
python -m hercules.records.codehash $(git ls-files src/hercules/sg)   # for the METRIC-HASH entry
```

Before the merge, `tools/sib/sg/pkg/run_merged_tests.sh [pytest args]` runs the same plain pytest on a scratch copy of the repo with the package overlaid. With no arguments it runs the whole suite.
CLI after the merge: `python -m hercules.sg.cli INPUTS.json --out RESULT.json [--crops C.npz --patches P.npz]`.
