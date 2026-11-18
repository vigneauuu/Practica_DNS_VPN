"""Contrasta respuestas TCP con DoH autenticado en una submuestra fija."""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from itertools import product
from pathlib import Path
import csv
import json
import time

import dns.exception
import dns.message
import httpx

from pdns_lab.dnsprobe import summarize_response, utcnow

ENDPOINTS = {
    "cloudflare_standard": "https://cloudflare-dns.com/dns-query",
    "cloudflare_family": "https://family.cloudflare-dns.com/dns-query",
    "adguard_open": "https://unfiltered.adguard-dns.com/dns-query",
    "adguard_family": "https://family.adguard-dns.com/dns-query",
    "cleanbrowsing_adult": "https://doh.cleanbrowsing.org/doh/adult-filter/",
    "cleanbrowsing_family": "https://doh.cleanbrowsing.org/doh/family-filter/",
    "controld_open": "https://freedns.controld.com/p0",
    "controld_family": "https://freedns.controld.com/family",
}
MULLVAD_ENDPOINTS = {
    "mullvad_open": "https://dns.mullvad.net/dns-query",
    "mullvad_family": "https://family.dns.mullvad.net/dns-query",
}
CONTROLS = ["example.com", "no-existe-pdns-lab.invalid", "nudity.testcategory.com", "malware.testcategory.com"]


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--corpus", type=Path, default=Path("dataset/piloto-50-2026-10-30.csv"))
    parser.add_argument("--mullvad", action="store_true",
                        help="mide solo los dos perfiles públicos de Mullvad")
    args = parser.parse_args()
    corpus = list(csv.DictReader(args.corpus.open(encoding="utf-8")))
    educational = sorted(row["domain"] for row in corpus if row["categories"] == "educativo")[:4]
    cases = [(name, "control") for name in CONTROLS]
    cases += [(row["domain"], row["categories"]) for row in corpus
              if row["categories"] != "educativo" or row["domain"] in educational]

    def measure(pair):
        profile, endpoint = pair
        observations = []
        with httpx.Client(verify=True, trust_env=False, follow_redirects=False,
                          http2=args.mullvad, timeout=3) as client:
            for round_no, (domain, category), qtype in product((1, 2), cases, ("A", "AAAA")):
                row = dict(profile=profile, endpoint=endpoint, domain=domain, category=category,
                           qtype=qtype, round=round_no, started_at_utc=utcnow())
                q = dns.message.make_query(domain, qtype, use_edns=0, want_dnssec=True)
                try:
                    answer = client.post(endpoint, content=q.to_wire(), headers={
                        "Content-Type": "application/dns-message", "Accept": "application/dns-message",
                    })
                    answer.raise_for_status()
                    if answer.headers.get("content-type", "").split(";")[0].strip() != "application/dns-message":
                        raise ValueError("Tipo de respuesta DoH inesperado")
                    response = dns.message.from_wire(answer.content)
                    if not q.is_response(response):
                        raise ValueError("Respuesta DNS no corresponde a la pregunta")
                    row.update(error=None, **summarize_response(response))
                    if args.mullvad:
                        row["http_version"] = answer.http_version
                except (dns.exception.DNSException, httpx.HTTPError, OSError, ValueError) as exc:
                    row.update(error=type(exc).__name__, rcode=None, addresses=[], ede=[])
                observations.append(row)
                time.sleep(.08)
        print(profile, sum(v["error"] is None for v in observations), "/", len(observations), flush=True)
        return observations

    endpoints = MULLVAD_ENDPOINTS if args.mullvad else ENDPOINTS
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = [row for group in pool.map(measure, endpoints.items()) for row in group]
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
