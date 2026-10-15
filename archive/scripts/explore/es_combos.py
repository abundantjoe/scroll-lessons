"""edgeshape: the declared feature-group combinations (shared by the LOCO and held-out runs)."""
SHP_KEYS = ("dstar", "dslope", "width", "sharp", "cen")
AMP_KEYS = ("amp", "smax", "norm", "curv")

COMBOS = {
    "LVL": ["LVL"], "CH22": ["CH22"], "D1": ["D1"], "D2": ["D2"],
    "SHAPE": ["SHAPE"], "EDGE": ["EDGE"],
    "EDGE_SHP": ["EDGE_SHP"], "EDGE_AMP": ["EDGE_AMP"],
    "D1+D2": ["D1", "D2"], "SHAPE+EDGE": ["SHAPE", "EDGE"],
    "INV_ALL": ["D1", "D2", "SHAPE", "EDGE_SHP"],
    "LVL+D1": ["LVL", "D1"], "LVL+D2": ["LVL", "D2"],
    "LVL+SHAPE": ["LVL", "SHAPE"], "LVL+EDGE": ["LVL", "EDGE"],
    "LVL+EDGE_SHP": ["LVL", "EDGE_SHP"],
    "LVL+SHAPE+EDGE": ["LVL", "SHAPE", "EDGE"],
    "CH22+EDGE_SHP": ["CH22", "EDGE_SHP"],
    "CH22+EDGE": ["CH22", "EDGE"], "CH22+SHAPE": ["CH22", "SHAPE"],
    "CH22+SHAPE+EDGE": ["CH22", "SHAPE", "EDGE"],
    "ALL": ["LVL", "CH22", "D1", "D2", "SHAPE", "EDGE"],
}


def add_subgroups(gidx, names):
    gidx["EDGE_SHP"] = [i for i in gidx["EDGE"] if any(k in names[i].split(":")[1] for k in SHP_KEYS)]
    gidx["EDGE_AMP"] = [i for i in gidx["EDGE"] if any(k in names[i].split(":")[1] for k in AMP_KEYS)]
    return gidx
