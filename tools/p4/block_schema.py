# Provenance: Project HERCULES | owner the owner | [id removed]
"""Reader-output validation by brief variant (RULES.md DECL-P4-17, METRIC-HASH-38).

Variants v1, sigma2 and sigma2t use the pinned configs/reader_output.schema.json unchanged
(hercules.scorer.schema.validate_reader_output). The 'block' variant uses configs/reader_output_block.schema.json:
the same schema, plus the optional side fields 'lines' (integer >= 0) and 'marks' (non-letter pen marks), with the
same code-level checks, and finiteness checks on the marks.
"""
import json
import math
import os

BLOCK_SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'configs',
                            'reader_output_block.schema.json')


def _finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def validate_block(obj):
    import jsonschema
    from hercules.scorer.schema import _extra_checks
    schema = json.load(open(BLOCK_SCHEMA, encoding='utf-8'))
    raw = [('/' + '/'.join(str(p) for p in e.absolute_path), e.message)
           for e in jsonschema.Draft202012Validator(schema).iter_errors(obj)]
    if not raw:
        raw = _extra_checks(obj)
        for i, item in enumerate(obj['items']):
            for side in ('left', 'right'):
                for j, m in enumerate(item[side].get('marks', [])):
                    for key in ('x', 'y'):
                        if not _finite(m[key]):
                            raw.append((f'/items/{i}/{side}/marks/{j}/{key}', 'must be a finite number'))
                    for k, v in enumerate(m['box']):
                        if not _finite(v):
                            raw.append((f'/items/{i}/{side}/marks/{j}/box/{k}', 'must be a finite number'))
    errors = [f'{p}: {m}' for p, m in sorted(set(raw))]
    return (not errors, errors)


def validate_for_variant(obj, variant):
    if variant == 'block':
        return validate_block(obj)
    from hercules.scorer.schema import validate_reader_output
    return validate_reader_output(obj)
