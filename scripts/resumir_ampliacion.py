"""Extrae agregados públicos y conserva por separado los mensajes originales."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import json
import ipaddress
import sqlite3

from pdns_lab.analysis import DECISIVE, agreement
from pdns_lab.corpus import sha256


def rows_from_run(path):
    with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        runs = conn.execute("SELECT * FROM runs").fetchall()
        if len(runs) != 1:
            raise ValueError(f"Se esperaba exactamente una ejecución: {path}")
        run = dict(runs[0])
        rows = [dict(row) for row in conn.execute("SELECT * FROM samples ORDER BY profile, domain, qtype, round")]
    meta = json.loads(run["metadata_json"])
    if len(rows) != meta["expected_samples"] or any(row["run_id"] != run["run_id"] for row in rows):
        raise ValueError(f"Ejecución incompleta: {path}")
    attempts = Counter()
    errors = Counter()
    for row in rows:
        for role, record in json.loads(row["evidence_json"]).items():
            if record is not None:
                attempts[role] += len(record["attempts"])
                errors[role] += sum(bool(attempt["error"]) for attempt in record["attempts"])
    return {
        "run_id": run["run_id"], "created_at_utc": run["created_at"], "db_sha256": sha256(path),
        "profile": meta["profiles"][0]["id"], "observations": len(rows), "queries": sum(attempts.values()),
        "queries_by_role": dict(attempts), "errors_by_role": dict(errors),
        "corpus_sha256": meta["corpus_sha256"], "profiles_sha256": meta["profiles_sha256"],
        "rounds": meta["rounds"], "qtypes": meta["qtypes"], "exploratory": meta["exploratory"],
    }, rows


def summarize_density(rows):
    counts = defaultdict(Counter)
    stability_groups = defaultdict(list)
    labels = {}
    for row in rows:
        profile, domain, qtype = row["profile"], row["domain"], row["qtype"]
        labels[domain] = row["categories"].split("|")
        for category in ["all", *labels[domain]]:
            counts[profile, qtype, category][row["status"]] += 1
        stability_groups[profile, qtype, domain].append(row["status"])
    stable = {
        key: DECISIVE[states[0]]
        for key, states in stability_groups.items()
        if len(states) == 3 and len(set(states)) == 1 and states[0] in DECISIVE
    }
    aggregate = [
        dict(profile=p, qtype=q, category=c, n=sum(counter.values()), states=dict(counter))
        for (p, q, c), counter in sorted(counts.items())
    ]
    profiles = sorted({row["profile"] for row in rows})
    pairwise = []
    for a, b in combinations(profiles, 2):
        for qtype in ("A", "AAAA"):
            pairs = [(stable[a, qtype, domain], stable[b, qtype, domain]) for domain in sorted(labels)
                     if (a, qtype, domain) in stable and (b, qtype, domain) in stable]
            pairwise.append(dict(a=a, b=b, qtype=qtype, excluded=len(labels)-len(pairs), **agreement(pairs)))
    return aggregate, pairwise, dict(Counter(cat for cats in labels.values() for cat in cats))


def doh_pattern(row):
    if row["error"]:
        return "error"
    if any(option["code"] in {15, 16, 17} for option in row["ede"]):
        return "ede_politica"
    addresses = [ipaddress.ip_address(address) for address in row["addresses"]]
    if any(address.is_unspecified or address.is_loopback for address in addresses):
        return "direccion_especial"
    if addresses:
        return "direccion_ordinaria"
    return row["rcode"]


def summarize_doh(path, expected_profiles=8):
    observations = json.loads(path.read_text(encoding="utf-8"))
    keys = {(r["profile"], r["domain"], r["qtype"], r["round"]) for r in observations}
    expected_observations = expected_profiles * 19 * 2 * 2
    if len(keys) != len(observations) or len(observations) != expected_observations:
        raise ValueError(f"La submuestra DoH debe contener {expected_observations} observaciones únicas")
    coverage = defaultdict(set)
    for profile, domain, qtype, round_no in keys:
        coverage[profile].add((domain, qtype, round_no))
    if len(coverage) != expected_profiles or len({frozenset(cases) for cases in coverage.values()}) != 1:
        raise ValueError("Los perfiles DoH deben cubrir los mismos casos")
    counts = defaultdict(Counter)
    profiles = {}
    for row in observations:
        profiles[row["profile"]] = row["endpoint"]
        counts[row["profile"], row["qtype"], row["category"]][doh_pattern(row)] += 1
    return {
        "attempts": len(observations), "answers_received": sum(not r["error"] for r in observations),
        "source_sha256": sha256(path), "profiles": profiles, "rounds": 2, "domain_count": 19,
        "counts": [dict(profile=p, qtype=q, category=c, patterns=dict(values))
                   for (p, q, c), values in sorted(counts.items())],
    }


def adult_details(rows):
    counts = defaultdict(Counter)
    for row in rows:
        if "adultos" not in row["categories"].split("|"):
            continue
        evidence = json.loads(row["evidence_json"])
        target = evidence["target"]["final"]
        key = row["profile"], row["qtype"]
        fingerprint = {
            "rcode": target["rcode"], "addresses": target["addresses"],
            "policy_ede": [o["code"] for o in target["ede"] if o["code"] in {15, 16, 17}],
            "state": row["status"],
        }
        if row["profile"].endswith("_family") or row["profile"] == "cleanbrowsing_adult":
            counts[key][json.dumps(fingerprint, sort_keys=True)] += 1
    return [
        {"profile": p, "qtype": q, "patterns": [dict(observations=n, **json.loads(k)) for k, n in sorted(c.items())]}
        for (p, q), c in sorted(counts.items())
    ]


def summarize_cisco(path):
    controls = json.loads(path.read_text(encoding="utf-8"))
    return {profile: {control: {k: row[k] for k in ("rcode", "addresses", "error")}
                      for control, row in values.items()} for profile, values in controls.items()}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--vpn-directory", default="vpn-verificada")
    parser.add_argument("--mullvad", type=Path, help="archivo de observaciones DoH de Mullvad")
    args = parser.parse_args()
    directory = args.input
    runs, rows = [], []
    for path in sorted(directory.glob("*.sqlite3")):
        meta, observations = rows_from_run(path)
        runs.append(meta)
        rows.extend(observations)
    profiles = {run["profile"] for run in runs}
    if len(profiles) != 14 or len(runs) != 14 or len(rows) != 4200:
        raise ValueError("El contraste requiere 14 perfiles con 300 observaciones cada uno")
    if len({(r["corpus_sha256"], r["profiles_sha256"]) for r in runs}) != 1:
        raise ValueError("Los perfiles deben compartir el corpus y archivo de configuración")
    calibration = json.loads((directory / "calibracion.json").read_text())
    if set(calibration) != profiles:
        raise ValueError("Falta calibración de algún perfil")
    vpn_directory = directory / args.vpn_directory
    vpn = {}
    for name in ("directa", "vpn_sin_filtro", "vpn_con_filtro"):
        values = json.loads((vpn_directory / f"{name}.json").read_text())
        if len(values) != 24 or any(v["status"] != v["expected"] for v in values):
            raise ValueError(f"Control VPN incompleto o discordante: {name}")
        vpn[name] = dict(Counter(v["status"] for v in values))
    routes = [json.loads((vpn_directory / f"ruta-{kind}.json").read_text())[0]["dev"] for kind in ("directa", "vpn")]
    if routes[0] == routes[1] or routes[1] != "tun0":
        raise ValueError("No se comprobó la separación entre el enlace directo y tun0")
    values = json.loads((directory / "proxy.json").read_text())
    if len(values) != 36 or any(v["result"].get("http_status") != v["expected_http"] or
                                 v["result"]["status"] != v["expected_state"] for v in values):
        raise ValueError("Control HTTP incompleto o discordante")
    proxy = {
        mode: dict(Counter(v["result"]["status"] for v in values if v["mode"] == mode))
        for mode in ("directa", "proxy_sin_filtro", "proxy_con_filtro")
    }
    counts, pairwise, categories = summarize_density(rows)
    result = {"scope": "TCP/53 público, etiquetas documentales pendientes de validación final; VPN y proxy de laboratorio",
              "runs": runs, "categories": categories, "observations": len(rows),
              "queries": sum(r["queries"] for r in runs), "counts": counts, "pairwise": pairwise,
              "calibration": {p: {"sent": len(values), "answers_received": sum(not x["error"] for x in values.values())}
                              for p, values in calibration.items()},
              "doh": summarize_doh(directory / "doh.json"),
              "adult_tcp_observed_patterns": adult_details(rows),
              "cisco_control": summarize_cisco(directory / "calibracion-cisco.json"),
              "vpn_local": vpn, "vpn_route_checked": routes[1], "proxy_local": proxy}
    if args.mullvad:
        result["doh_mullvad"] = summarize_doh(args.mullvad, expected_profiles=2)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
