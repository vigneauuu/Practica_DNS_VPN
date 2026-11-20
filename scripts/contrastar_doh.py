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

from pdns_lab.corpus import experimental_rows
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
DNS4EU_ENDPOINTS = {
    "dns4eu_unfiltered": "https://unfiltered.joindns4.eu/dns-query",
    "dns4eu_protective": "https://protective.joindns4.eu/dns-query",
    "dns4eu_child": "https://child.joindns4.eu/dns-query",
}
FAMILY_ENDPOINTS = {
    "cloudflare_standard": ENDPOINTS["cloudflare_standard"],
    "cloudflare_security": "https://security.cloudflare-dns.com/dns-query",
    "cloudflare_family": ENDPOINTS["cloudflare_family"],
    "adguard_open": ENDPOINTS["adguard_open"],
    "adguard_default": "https://dns.adguard-dns.com/dns-query",
    "adguard_family": ENDPOINTS["adguard_family"],
}
CONTROLS = ["example.com", "no-existe-pdns-lab.invalid", "nudity.testcategory.com", "malware.testcategory.com"]


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--corpus", type=Path, default=Path("dataset/piloto-50-2026-10-30.csv"))
    parser.add_argument("--todos-educativos", action="store_true",
                        help="incluye todos los dominios educativos del archivo")
    parser.add_argument("--control-adicional", action="append", default=[], metavar="DOMINIO",
                        help="añade un control técnico al inicio de cada ronda")
    profiles = parser.add_mutually_exclusive_group()
    profiles.add_argument("--mullvad", action="store_const", dest="endpoints", const=MULLVAD_ENDPOINTS,
                          help="mide solo los dos perfiles públicos de Mullvad")
    profiles.add_argument("--dns4eu", action="store_const", dest="endpoints", const=DNS4EU_ENDPOINTS,
                          help="mide los perfiles sin filtro, protector y con protección infantil de DNS4EU")
    profiles.add_argument("--familia", action="store_const", dest="endpoints", const=FAMILY_ENDPOINTS,
                          help="contrasta perfiles familiares y de referencia de Cloudflare y AdGuard")
    parser.set_defaults(endpoints=ENDPOINTS)
    args = parser.parse_args()
    use_http2 = args.endpoints is not ENDPOINTS
    with args.corpus.open(encoding="utf-8", newline="") as source:
        corpus = list(experimental_rows(csv.DictReader(source)))
    educational = sorted(row["domain"] for row in corpus if row["categories"] == "educativo")[:4]
    cases = [(name, "control") for name in [*CONTROLS, *args.control_adicional]]
    cases += [(row["domain"], row["categories"]) for row in corpus
              if args.todos_educativos or row["categories"] != "educativo" or row["domain"] in educational]

    def measure(pair):
        profile, endpoint = pair
        observations = []
        with httpx.Client(verify=True, trust_env=False, follow_redirects=False,
                          http2=use_http2, timeout=3) as client:
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
                    if use_http2:
                        row["http_version"] = answer.http_version
                except (dns.exception.DNSException, httpx.HTTPError, OSError, ValueError) as exc:
                    row.update(error=type(exc).__name__, rcode=None, addresses=[], ede=[])
                    if isinstance(exc, httpx.HTTPStatusError):
                        row["http_status"] = exc.response.status_code
                observations.append(row)
                time.sleep(.08)
        print(profile, sum(v["error"] is None for v in observations), "/", len(observations), flush=True)
        return observations

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = [row for group in pool.map(measure, args.endpoints.items()) for row in group]
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
