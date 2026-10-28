"""Resumen descriptivo con denominadores y exclusiones por comparación."""
from collections import Counter, defaultdict
from itertools import combinations
import json
import sqlite3

DECISIVE = {"bloqueo_senalizado": 1, "resolucion_observada": 0}


def agreement(pairs):
    counts = Counter(pairs)
    n = len(pairs)
    if not n:
        return {"n": 0, "agreement": None, "kappa": None, "jaccard_block": None,
                "a_block_fraction": None, "b_block_fraction": None}
    observed = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    expected = pa * pb + (1-pa) * (1-pb)
    union = sum(bool(a or b) for a, b in pairs)
    return {"n": n, "agreement": observed, "kappa": (observed-expected)/(1-expected) if expected < 1 else None,
            "jaccard_block": counts[(1, 1)]/union if union else None,
            "a_block_fraction": pa, "b_block_fraction": pb,
            "contingency": {f"{a}{b}": counts[(a,b)] for a,b in [(0,0),(0,1),(1,0),(1,1)]}}


def analyze(path, run_id):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    run = con.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
    if not run:
        con.close()
        raise ValueError("Ejecución no encontrada; seleccione un run_id de este esquema")
    metadata = json.loads(run["metadata_json"])
    rows = [dict(r) for r in con.execute("SELECT * FROM samples WHERE run_id=?", (run_id,))]
    con.close()
    expected = metadata.get("expected_samples")
    report = {"run_id": run_id, "completed_samples": len(rows), "expected_samples": expected,
              "complete": expected is not None and len(rows) == expected,
              "interpretation": "Señales de bloqueo y resolución DNS observada; no exactitud de clasificación ni acceso web garantizado.",
              "counts": [], "pairwise": [], "temporal_stability": []}
    grouped, observations = defaultdict(Counter), defaultdict(list)
    labels = {}
    for row in rows:
        cats = ["ALL"] + row["categories"].split("|")
        labels[row["domain"]] = set(row["categories"].split("|"))
        for category in cats:
            grouped[(row["profile"], row["qtype"], category)][row["status"]] += 1
        observations[(row["domain"], row["profile"], row["qtype"])].append(row)
    for (profile, qtype, category), counts in sorted(grouped.items()):
        total = sum(counts.values())
        decisive = counts["bloqueo_senalizado"] + counts["resolucion_observada"]
        report["counts"].append({"profile": profile, "qtype": qtype, "category": category, "total": total,
                                 "states": dict(counts), "signal_fraction_total": counts["bloqueo_senalizado"]/total,
                                 "signal_fraction_decisive": counts["bloqueo_senalizado"]/decisive if decisive else None,
                                 "decisive_coverage": decisive/total})
    stable = {}
    required_rounds = metadata.get("rounds", 1)
    for key, items in observations.items():
        states = {r["status"] for r in items}
        rounds = {r["round"] for r in items}
        is_stable = len(states) == 1 and next(iter(states)) in DECISIVE and len(rounds) == required_rounds
        if is_stable:
            stable[key] = DECISIVE[next(iter(states))]
        report["temporal_stability"].append({"domain": key[0], "profile": key[1], "qtype": key[2],
                                              "rounds_observed": len(rounds), "states": sorted(states),
                                              "stable_decisive": is_stable})
    profiles = sorted({r["profile"] for r in rows})
    categories = ["ALL"] + sorted(set.union(set(), *labels.values()))
    for a, b in combinations(profiles, 2):
        for qtype in sorted({r["qtype"] for r in rows}):
            for category in categories:
                eligible = [d for d, cats in labels.items() if category == "ALL" or category in cats]
                pairs = [(stable[(d,a,qtype)], stable[(d,b,qtype)]) for d in eligible if (d,a,qtype) in stable and (d,b,qtype) in stable]
                report["pairwise"].append({"a": a, "b": b, "qtype": qtype, "category": category,
                                           "eligible_domains": len(eligible), "excluded_domains": len(eligible)-len(pairs),
                                           "paired_coverage": len(pairs)/len(eligible) if eligible else None, **agreement(pairs)})
    return report
