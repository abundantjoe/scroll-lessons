#!/bin/sh
# Method v8 (RULES.md): extend the declared crop rule to 8 windows on the two pure-training segments, prepare the new crops,
# build no-veto labels, train with AUC checkpoint selection, judge once on the 7 evaluation crops.
cd "$(dirname "$0")/.."

# 1. extend the crop lists, with exactly the arguments the original selection used (density-ordered and deterministic,
#    so crops 1-4 must come back identical; step 2 verifies that and aborts if not).
for SEG in 20230929220926 20231012184424; do
  cp data/s1/$SEG/crops.json /tmp/crops_before_$SEG.json
  .venv/bin/python scripts/s1_select_crops.py $SEG data/s1/labels/${SEG}_inklabels_L.png \
    data/s1/$SEG/label_registration.json data/s1/$SEG/overview/onsheet_ds8.png data/s1/$SEG/crops.json 99 || exit 1
  .venv/bin/python scripts/s1_refine_reg.py data/s1/$SEG/crops.json data/s1/labels/${SEG}_inklabels_L.png \
    data/s1/$SEG/overview/ink_ds8.jpg || exit 1
done

# 2. integrity check: the first four crops of each segment must be byte-identical to the ones already trained on
.venv/bin/python - <<'PY' || exit 1
import json, sys
for seg in ("20230929220926", "20231012184424"):
    old = json.load(open(f"/tmp/crops_before_{seg}.json"))["crops"]
    new = json.load(open(f"data/s1/{seg}/crops.json"))["crops"]
    want = {"20230929220926": 4, "20231012184424": 11}[seg]      # measured maxima under the unchanged strict rule
    assert len(new) == want, f"{seg}: expected {want} crops, got {len(new)}"
    for a, b in zip(old[:4], new[:4]):
        for k in ("name", "y0", "x0", "side"):
            assert a[k] == b[k], f"{seg} {a['name']}: {k} changed {a[k]} -> {b[k]}"
    print(f"{seg}: crops 1-4 unchanged, added {[c['name'] for c in new[4:]]}")
PY
for SEG in 20230929220926 20231012184424; do cp data/s1/$SEG/crops.json stats/s1_crops_$SEG.json; done
echo V8_CROPS_SELECTED

# 3. prepare the new crops (fetch -> topography -> masks -> pooled stack; raw chunks deleted per crop).
#    run_s1_prep.sh skips any crop that already has ds8_x.npy, so only held5-8 are built. Depth range as originally used.
for SEG in 20230929220926 20231012184424; do
  scripts/run_s1_prep.sh $SEG 24 84 || exit 1
done
echo V8_CROPS_PREPARED

# 4. no-veto labels for every training crop
D=""
for SEG in 20230929220926 20231012184424; do
  for n in $(.venv/bin/python -c "import json;print(' '.join(x['name'] for x in json.load(open('data/s1/'+'$SEG'+'/crops.json'))['crops']))"); do
    test -f data/s1/$SEG/derived/$n/ds8_x.npy && D="$D data/s1/$SEG/derived/$n"
  done
done
.venv/bin/python scripts/build_noveto_y.py data/s1/20231005123336/derived/train $D || exit 1

# 5. train: 16 crops, no team veto, checkpoint chosen by validation pixel AUC
DIRS=data/s1/20231005123336/derived/train
for SEG in 20230929220926 20231012184424; do
  for n in $(.venv/bin/python -c "import json;print(' '.join(x['name'] for x in json.load(open('data/s1/'+'$SEG'+'/crops.json'))['crops']))"); do
    test "$SEG/$n" = "20231012184424/held4" && continue
    test -f data/s1/$SEG/derived/$n/ds8_y_noveto.npy && DIRS="$DIRS,data/s1/$SEG/derived/$n"
  done
done
echo "v8 training dirs: $DIRS"
rm -f data/s1/v8_unet.pt
V5_Y=ds8_y_noveto.npy V5_SELECT=auc V5_LR=3e-4 V5_WD=1e-4 V5_VAL_DIR=data/s1/20231012184424/derived/held4 OMP_NUM_THREADS=3 \
  .venv/bin/python scripts/s1_v5.py train "$DIRS" data/s1/v8_unet.pt 12000 || exit 1

# 6. judge once
EVAL='20231005123336 held1|20231005123336 held2|20231005123336 held3|20231210121321 held1|20231210121321 held2|20231210121321 held3|20231210121321 held4'
OLDIFS=$IFS
IFS='|'
for spec in $EVAL; do
  IFS=$OLDIFS
  set -- $spec
  SEG=$1; n=$2; DD=data/s1/$SEG/derived/$n
  OMP_NUM_THREADS=2 .venv/bin/python scripts/s1_v5.py predict $DD data/s1/v8_unet.pt v8 || exit 1
  .venv/bin/python scripts/s1_judge.py $DD data/s1/$SEG/crops.json $n data/s1/labels/${SEG}_inklabels_L.png v8 2.4 || exit 1
  IFS='|'
done
IFS=$OLDIFS
S='20231005123336:held1 20231005123336:held2 20231005123336:held3 20231210121321:held1 20231210121321:held2 20231210121321:held3 20231210121321:held4'
.venv/bin/python scripts/stroke_test.py $S
.venv/bin/python scripts/local_stroke_test.py $S
echo V8_JUDGED
