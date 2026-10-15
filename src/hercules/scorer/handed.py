# Provenance: Project HERCULES | owner the owner | [id removed]
"""DECL-HANDED vote counting (scorer only; reads the key under /srv/scorer)."""
import json
import sys

BAR_VOTES = 10  # of 12: >= 10 votes for one state fixes the convention


def count_votes(reader_outputs, key):
    """reader_outputs: list of {"pairs":[{"id","normal":"LEFT|RIGHT|UNSURE"}]} (valid
    readers only). key: {item_id: {"left": "A"|"B", "right": "A"|"B"}}.
    UNSURE and missing pairs count as no vote."""
    votes = {"A": 0, "B": 0, "none": 0}
    for out in reader_outputs:
        seen = {p.get("id"): p.get("normal") for p in out.get("pairs", [])}
        for item_id, k in key.items():
            side = seen.get(item_id)
            if side in ("LEFT", "RIGHT"):
                votes[k[side.lower()]] += 1
            else:
                votes["none"] += 1
    return votes


def verdict(votes):
    if votes["A"] >= BAR_VOTES:
        return "A", +1
    if votes["B"] >= BAR_VOTES:
        return "B", -1
    return "AMBIGUOUS", None


if __name__ == "__main__":
    key = {k: v for k, v in json.load(open(sys.argv[1])).items() if isinstance(v, dict)}
    outs = [json.load(open(p)) for p in sys.argv[2:]]
    v = count_votes(outs, key)
    print(json.dumps({"votes": v, "verdict": verdict(v)}))
