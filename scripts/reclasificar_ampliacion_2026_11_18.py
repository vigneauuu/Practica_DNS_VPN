#!/usr/bin/env python3
"""Reclasificación verificada con huellas por operador y auditoría temporal de la ampliación TCP/53 (18-11-2026).

Lee en solo lectura las 14 bases SQLite originales en results/ampliacion-2026-11-18/ sin modificarlas,
conserva el conteo original y produce:
1. Estados reclasificados con huellas documentadas/calibradas por proveedor (AdGuard, OpenDNS, Control D, CleanBrowsing).
2. Falsos positivos educativos exactos (sobre los 39 portales educativos) en los 14 perfiles TCP/53.
3. Consistencia exacta entre rondas (3 rondas) y tiempos reales transcurridos entre rondas (UTC).
4. Matrices de acuerdo real (acuerdo observado, Cohen's Kappa y similitud de Jaccard) entre perfiles.
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AMP_DIR = ROOT / "results" / "ampliacion-2026-11-18"
OUT_JSON = ROOT / "docs" / "evidencia" / "reclasificacion-ampliacion-tcp-2026-11-25.json"

PROFILES = [
    "cloudflare_standard", "cloudflare_security", "cloudflare_family",
    "google_public", "quad9_reference", "quad9_secure",
    "adguard_open", "adguard_family",
    "cleanbrowsing_adult", "cleanbrowsing_family",
    "controld_open", "controld_family",
    "opendns_standard", "opendns_family",
]


def classify_calibrated(profile: str, qtype: str, rcode: str | None, answers: list[str], ede: list[int],
                        error: str | None, ctrl_ok: bool) -> str:
    if error:
        return "error_red"
    ips = set(answers)
    if set(ede) & {15, 16, 17}:
        return "bloqueo_senalizado"
    if profile in ("cloudflare_family", "cloudflare_security", "controld_family", "adguard_family") and (ips & {"0.0.0.0", "::"}):
        return "bloqueo_senalizado"
    if profile == "adguard_family" and ("94.140.14.35" in ips or "::ffff:94.140.14.35" in ips):
        return "bloqueo_senalizado"
    if profile == "opendns_family" and any(ip.startswith("146.112.61.") or ip.startswith("::ffff:146.112.61.") for ip in ips):
        return "bloqueo_senalizado"
    if profile in ("cleanbrowsing_adult", "cleanbrowsing_family") and rcode == "NXDOMAIN":
        return "bloqueo_senalizado" if ctrl_ok else "indeterminado"
    if rcode == "NOERROR" and ips:
        if ips & {"0.0.0.0", "::", "127.0.0.1", "::1"}:
            return "anomalia"
        return "resolucion_observada"
    if rcode in ("NXDOMAIN", "NOERROR") and not ips:
        return "anomalia" if (rcode == "NXDOMAIN" and ctrl_ok) else "indeterminado"
    return "indeterminado"


def main() -> None:
    # Load pilot domain categories from piloto-50-2026-10-30.csv
    import csv
    dom_cat: dict[str, str] = {}
    with (ROOT / "dataset" / "piloto-50-2026-10-30.csv").open() as f:
        for r in csv.DictReader(f):
            dom_cat[r["domain"].strip().lower()] = r["categories"].strip().split("|")[0]

    per_profile_summary = {}
    stable_domain_state: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    inter_round_stats = {}

    for pid in PROFILES:
        db = AMP_DIR / f"{pid}.sqlite3"
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT domain, categories, qtype, round, status, evidence_json FROM samples"
        ).fetchall()
        conn.close()

        by_qt_cat = defaultdict(lambda: defaultdict(Counter))
        by_qt_dom_states: dict[tuple[str, str], list[str]] = defaultdict(list)
        round_ts: dict[int, list[dt.datetime]] = defaultdict(list)
        raw_errors = 0

        for o in rows:
            dom = o["domain"].strip().lower()
            qt = o["qtype"]
            rnd = int(o["round"])
            cat = dom_cat.get(dom, o["categories"].split("|")[0])
            ev = json.loads(o["evidence_json"])
            qtgt = ev.get("target", {}).get("final")
            if not qtgt:
                continue
            ts_str = qtgt.get("time")
            if ts_str:
                round_ts[rnd].append(dt.datetime.fromisoformat(ts_str.replace("Z", "+00:00")))
            err = qtgt.get("error")
            if err:
                raw_errors += 1
            ans = qtgt.get("addresses") or []
            ede = [int(x["code"]) for x in (qtgt.get("ede") or []) if isinstance(x, dict) and "code" in x]
            rcode = qtgt.get("rcode")

            # Check before/after controls
            cb = (ev.get("control_before") or {}).get("final")
            ca = (ev.get("control_after") or {}).get("final")
            ctrl_ok = False
            if cb and ca:
                ans_b = cb.get("addresses") or []
                ans_a = ca.get("addresses") or []
                ctrl_ok = (cb.get("rcode") == "NOERROR" and bool(ans_b) and ca.get("rcode") == "NOERROR" and bool(ans_a))

            st = classify_calibrated(pid, qt, rcode, ans, ede, err, ctrl_ok)
            by_qt_cat[qt][cat][st] += 1
            by_qt_cat[qt]["ALL"][st] += 1
            by_qt_dom_states[(qt, dom)].append(st)

        # Inter-round timing
        r_starts = {r: min(ts) for r, ts in round_ts.items() if ts}
        r_ends = {r: max(ts) for r, ts in round_ts.items() if ts}
        deltas = []
        if 1 in r_starts and 2 in r_starts:
            deltas.append(round((r_starts[2] - r_starts[1]).total_seconds(), 2))
        if 2 in r_starts and 3 in r_starts:
            deltas.append(round((r_starts[3] - r_starts[2]).total_seconds(), 2))
        inter_round_stats[pid] = {
            "total_duration_s": round((max(r_ends.values()) - min(r_starts.values())).total_seconds(), 2) if r_starts else None,
            "start_deltas_s": deltas,
            "target_errors": raw_errors,
        }

        # Stability/consistency per qtype
        cons_by_qt = {}
        for qt in ("A", "AAAA"):
            cons = incons = errs = 0
            for dom in sorted(dom_cat.keys()):
                sts = by_qt_dom_states.get((qt, dom), [])
                if any(s == "error_red" for s in sts):
                    errs += 1
                    continue
                if len(sts) == 3 and len(set(sts)) == 1:
                    cons += 1
                    stable_domain_state[(pid, qt)][dom] = sts[0]
                else:
                    incons += 1
            cons_by_qt[qt] = {
                "consistente": cons, "inconsistente": incons, "con_error_red": errs,
                "tasa_consistencia_sin_error": round(cons / (cons + incons), 4) if (cons + incons) else None,
                "tasa_consistencia_total": round(cons / 50, 4),
            }

        per_profile_summary[pid] = {
            "counts": {qt: {cat: dict(c) for cat, c in cmap.items()} for qt, cmap in by_qt_cat.items()},
            "consistency": cons_by_qt,
            "edu_false_positives_A": by_qt_cat["A"]["educativo"].get("bloqueo_senalizado", 0),
            "edu_resolved_A": by_qt_cat["A"]["educativo"].get("resolucion_observada", 0),
        }

    # Pairwise Kappa & Jaccard among the 6 parental TCP profiles post-calibration!
    parental_tcp = ["cloudflare_family", "adguard_family", "cleanbrowsing_adult", "cleanbrowsing_family", "controld_family", "opendns_family"]
    pairwise_post = {}
    all_doms = sorted(dom_cat.keys())
    for qt in ("A", "AAAA"):
        pw_rows = []
        for i, pa in enumerate(parental_tcp):
            for pb in parental_tcp[i + 1:]:
                c00 = c01 = c10 = c11 = 0
                for d in all_doms:
                    sa = stable_domain_state[(pa, qt)].get(d)
                    sb = stable_domain_state[(pb, qt)].get(d)
                    if sa not in ("resolucion_observada", "bloqueo_senalizado") or sb not in ("resolucion_observada", "bloqueo_senalizado"):
                        continue
                    ba = 1 if sa == "bloqueo_senalizado" else 0
                    bb = 1 if sb == "bloqueo_senalizado" else 0
                    if ba == 0 and bb == 0: c00 += 1
                    elif ba == 0 and bb == 1: c01 += 1
                    elif ba == 1 and bb == 0: c10 += 1
                    else: c11 += 1
                n = c00 + c01 + c10 + c11
                po = (c00 + c11) / n if n else None
                pa_r = (c10 + c11) / n if n else 0
                pb_r = (c01 + c11) / n if n else 0
                pe = pa_r * pb_r + (1 - pa_r) * (1 - pb_r)
                kappa = None if (not n or abs(1 - pe) < 1e-12) else round((po - pe) / (1 - pe), 4)
                jacc = None if (c01 + c10 + c11) == 0 else round(c11 / (c01 + c10 + c11), 4)
                pw_rows.append({"a": pa, "b": pb, "n": n, "c00": c00, "c01": c01, "c10": c10, "c11": c11,
                                "agreement": round(po, 4) if po is not None else None, "kappa": kappa, "jaccard": jacc})
        pairwise_post[qt] = pw_rows

    # Compute overall 91-pair coverage distribution post-calibration!
    cov_dist = {"A": Counter(), "AAAA": Counter()}
    for qt in ("A", "AAAA"):
        for i, pa in enumerate(PROFILES):
            for pb in PROFILES[i + 1:]:
                n = sum(
                    1 for d in all_doms
                    if stable_domain_state[(pa, qt)].get(d) in ("resolucion_observada", "bloqueo_senalizado")
                    and stable_domain_state[(pb, qt)].get(d) in ("resolucion_observada", "bloqueo_senalizado")
                )
                cov_dist[qt][n] += 1

    out = {
        "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_dir": "results/ampliacion-2026-11-18/",
        "per_profile": per_profile_summary,
        "inter_round_timing": inter_round_stats,
        "pairwise_parental_post_calibration": pairwise_post,
        "coverage_91_pairs_post_calibration": {qt: dict(sorted(c.items())) for qt, c in cov_dist.items()},
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print("=== RECLASIFICACION TCP/53 COMPLETADA ===")
    print("Coverage 91 pairs post-cal:", out["coverage_91_pairs_post_calibration"])
    print("Inter-round deltas median (s):", statistics.median([d for v in inter_round_stats.values() for d in v["start_deltas_s"]]))
    print("Target errors per profile:", {k: v["target_errors"] for k, v in inter_round_stats.items() if v["target_errors"]})
    print("Edu FP A across all 14 profiles:", {k: v["edu_false_positives_A"] for k, v in per_profile_summary.items()})
    print("Pairwise parental A sample:", pairwise_post["A"][:5])


if __name__ == "__main__":
    main()
