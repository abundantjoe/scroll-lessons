Provenance: Project HERCULES | owner the owner | [id removed]

# Proposal: mirror-canary answer field (addendum; the frozen briefs and schema are NOT edited)

The frozen brief (`configs/briefs/k_d2_pairs_task.txt`, READCAL-FREEZE / METRIC-HASH-14) and
`configs/reader_output.schema.json` have no mirror answer. DECL-EMPNULL's "mirror detection >= 0.8"
therefore needs an addendum. It applies only to batches that contain mirror canaries and only
after the orchestrator declares it (the brief and schema hashes change, so it is a new METRIC-HASH).

## 1. Addendum text (appended as one sentence before the `The items are:` line)

> Some images may be shown mirrored left-to-right; for each image also answer "mirrored": "Y" if its
> writing or shapes appear mirrored, else "N".

The ANSWER_JSON template gains `"mirrored":"Y|N"` in both `left` and `right`:

```
{{"id":"<item id>","left":{{"rows":"Y|N","mirrored":"Y|N","letters":[...]}},"right":{{"rows":"Y|N","mirrored":"Y|N","letters":[...]}}}}
```

## 2. Schema change (`$defs.side`)

Add one OPTIONAL property; `required` is unchanged, so every existing reader output stays valid:

```json
"mirrored": {"enum": ["Y", "N"]}
```

## 3. Presentation (proposed)

- Each mirror canary is one panel. Its partner panel in the same item is an independently drawn glyph
  or state, randomised per reader.
- The scorer holds `{control_id, item_id, side, mirrored}`.
- A batch holds all 7 glyphs; each is drawn in a random state per reader, so about half are mirrored.
- Letter namings on mirror-canary panels are ignored by the letter scorer. They are not text.

## 4. Scoring (code, already in `hercules.tribunal.validity`)

- `mirror_answers_from_panels(readers, mirror_panels)` turns the per-panel Y/N into
  `score_mirror` answers. A missing or invalid answer counts as wrong.
- Batch void if detection < 0.8 (DECL-TRIBUNAL-1 item 4, accepted).
- Tests: `tests/test_tribunal_validity.py::test_mirror_answers_from_panels`.

## 5. Risk disclosed

HANDED-1/-R2/-R3B found that readers could not tell mirrored reference maps from normal ones
(pooled A 12 : B 14). Mirror canaries are font glyphs with a strong, known asymmetry
(asymmetry index > 0.1 for all 7), so detection there measures reader capability rather than
map handedness. If readers fail this bar on font glyphs, every batch will void under I16. That
outcome should be tested in a harness dry run before the first real batch.
