#!/usr/bin/env python3
"""Consulta exhaustiva a la API pública de OONI Explorer para Chile (CL) sobre dominios parentales reales."""
from __future__ import annotations

import asyncio
import csv
import datetime as dt
import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "docs" / "evidencia" / "ooni-chile-2026-11-25.json"


async def main() -> None:
    d4 = json.loads((ROOT / "docs" / "evidencia" / "politica-dns4eu-2026-11-19.json").read_text())
    subtel = sorted({x["dominio"] for x in d4["detalle"] if x["categoria"] == "apuestas"})
    adult_4 = sorted({x["dominio"] for x in d4["detalle"] if x["categoria"] == "adultos"})
    with (ROOT / "dataset" / "referencia-adulto-ofcom-2026-11-19.csv").open() as f:
        adult_ofcom = sorted({r["domain"] for r in csv.DictReader(f) if "adulto" in (r.get("category") or r.get("categories") or "")})
    weapons = ["ruger.com", "sigsauer.com", "smith-wesson.com", "glock.com", "beretta.com", "colt.com",
               "mossberg.com", "winchester.com", "springfield-armory.com", "heckler-koch.com",
               "taurususa.com", "browning.com", "fnherstal.com"]
    edu_sample = ["uchile.cl", "uc.cl", "udp.cl", "usm.cl", "mit.edu", "stanford.edu"]

    targets = (
        [(d, "apuestas_subtel") for d in subtel]
        + [(d, "adultos_ue") for d in adult_4]
        + [(d, "adultos_ofcom") for d in adult_ofcom]
        + [(d, "armas") for d in weapons]
        + [(d, "educativo") for d in edu_sample]
        + [("example.com", "control_tecnico")]
    )

    sem = asyncio.Semaphore(8)
    results_cl = []
    # Also test bare root domain without www. just in case OONI stores root vs www
    async with httpx.AsyncClient(timeout=12.0) as client:
        # Check recent global CL web_connectivity volume to verify API works cleanly
        agg = await client.get("https://api.ooni.io/api/v1/aggregation", params={
            "probe_cc": "CL", "test_name": "web_connectivity", "since": "2026-09-01", "until": "2026-11-26"
        })
        cl_agg = agg.json() if agg.status_code == 200 else {"error": agg.status_code}

        async def check_one(dom: str, cat: str) -> dict:
            async with sem:
                dom_bare = dom.removeprefix("www.")
                urls = list(dict.fromkeys([
                    f"https://{dom}/",
                    f"https://www.{dom_bare}/",
                    f"http://{dom}/",
                    f"http://www.{dom_bare}/",
                ]))
                hits_all = []
                for u in urls:
                    try:
                        r = await client.get("https://api.ooni.io/api/v1/measurements", params={
                            "probe_cc": "CL", "input": u, "test_name": "web_connectivity",
                            "since": "2026-09-01", "limit": 50
                        })
                        if r.status_code == 200:
                            hits_all.extend(r.json().get("results", []))
                    except Exception:
                        pass
                # Deduplicate by measurement_uid
                uniq = {x.get("measurement_uid", i): x for i, x in enumerate(hits_all)}
                vals = list(uniq.values())
                recent_2026 = [x for x in vals if str(x.get("measurement_start_time", "")).startswith("2026")]
                sep_nov_2026 = [x for x in recent_2026 if str(x.get("measurement_start_time", "")) >= "2026-09-01"]
                return {
                    "domain": dom, "category": cat,
                    "count_2024_2026": len(vals),
                    "count_2026": len(recent_2026),
                    "count_sep_nov_2026": len(sep_nov_2026),
                    "anomalies_2024_2026": sum(1 for x in vals if x.get("anomaly")),
                    "confirmed_2024_2026": sum(1 for x in vals if x.get("confirmed")),
                    "anomalies_2026": sum(1 for x in recent_2026 if x.get("anomaly")),
                    "confirmed_2026": sum(1 for x in recent_2026 if x.get("confirmed")),
                    "anomalies_sep_nov_2026": sum(1 for x in sep_nov_2026 if x.get("anomaly")),
                    "latest_utc": max((x.get("measurement_start_time", "") for x in vals), default=None),
                    "asns_2026": sorted({x.get("probe_asn") for x in recent_2026 if x.get("probe_asn")}),
                    "sample_inputs": sorted({x.get("input") for x in vals if x.get("input")})[:3],
                }

        results_cl = await asyncio.gather(*(check_one(d, c) for d, c in targets))

    with_hits = [r for r in results_cl if r["count_2024_2026"] > 0]
    with_hits_2026 = [r for r in results_cl if r["count_2026"] > 0]
    out = {
        "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "probe_cc": "CL",
        "window_historical": "2024-01-01..2026-11-26",
        "cl_web_connectivity_aggregation_sep_nov_2026": cl_agg,
        "total_domains_queried": len(targets),
        "domains_with_any_cl_records_2024_2026": len(with_hits),
        "domains_with_cl_records_2026": len(with_hits_2026),
        "hits_detail": sorted(with_hits, key=lambda x: (-x["count_2026"], -x["count_2024_2026"])),
        "all_results_summary": {
            cat: {
                "queried": sum(1 for r in results_cl if r["category"] == cat),
                "with_hits_2024_2026": sum(1 for r in results_cl if r["category"] == cat and r["count_2024_2026"] > 0),
                "with_hits_2026": sum(1 for r in results_cl if r["category"] == cat and r["count_2026"] > 0),
                "total_measurements_2026": sum(r["count_2026"] for r in results_cl if r["category"] == cat),
                "anomalies_2026": sum(r["anomalies_2026"] for r in results_cl if r["category"] == cat),
            }
            for cat in ("apuestas_subtel", "adultos_ue", "adultos_ofcom", "armas", "educativo", "control_tecnico")
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print("=== OONI CHILE COMPLETE ===")
    print("CL Sep-Nov 2026 agg:", cl_agg)
    print("Summary by cat:", json.dumps(out["all_results_summary"], indent=2))
    print("Top hits:", with_hits[:10])


if __name__ == "__main__":
    asyncio.run(main())
