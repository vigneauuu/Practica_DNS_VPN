"""Mide DNS por ruta directa y por túnel con controles de salida comprobados."""
from argparse import ArgumentParser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from csv import DictReader
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
import time

import dns.exception
import dns.message
import dns.query

from pdns_lab.dnsprobe import summarize_response, utcnow


BASE = Path("dataset/piloto-50-2026-10-30.csv")
BETTING = Path("dataset/doh-apuestas-subtel-2026-11-18.csv")
TRACE_HOST = "www.cloudflare.com"
TRACE_ADDRESS = "104.16.123.96"
WARNING_NAME = "warning.joindns4.eu"
CONTROLS = (
    "example.com", "no-existe-pdns-lab.invalid",
    "nudity.testcategory.com", "malware.testcategory.com", WARNING_NAME,
)
PROFILES = {
    "dns4eu_sin_filtro": ("unfiltered.joindns4.eu", "86.54.11.100"),
    "dns4eu_infantil": ("child.joindns4.eu", "86.54.11.12"),
}
ROUTE_LABELS = ("directa", "riseup")
QTYPES = ("A", "AAAA")
ROUNDS = (1, 2)


def names():
    with BASE.open(encoding="utf-8", newline="") as source:
        by_name = {r["domain"]: r["categories"] for r in DictReader(source)}
    educational = sorted(name for name in by_name if by_name[name] == "educativo")[:4]
    cases = {name: cat for name, cat in by_name.items()
             if cat != "educativo" or name in educational}
    with BETTING.open(encoding="utf-8", newline="") as source:
        for row in DictReader(source):
            if row["categories"] == "apuestas" and row["domain"] not in cases:
                cases[row["domain"]] = "apuestas_subtel"
    cases.update(dict.fromkeys(CONTROLS, "control"))
    return dict(sorted(cases.items()))


def curl_tls(host, address, path, *extra, request=None):
    return subprocess.run([
        "curl", "-q", "--noproxy", "*", "--ipv4", "--http2", "--silent",
        "--show-error", "--fail", "--max-time", "6", "--proto", "=https",
        "--resolve", f"{host}:443:{address}", *extra, f"https://{host}{path}",
    ], input=request, capture_output=True, check=True)


def route_check(expected_device, dns_server):
    endpoints = [TRACE_ADDRESS, *(address for _, address in PROFILES.values())]
    if dns_server:
        endpoints.append(dns_server)
    routes = {}
    for address in endpoints:
        output = subprocess.check_output(["ip", "-j", "route", "get", address])
        route = json.loads(output)[0]
        if route["dev"] != expected_device:
            raise RuntimeError(f"Ruta a {address}: {route['dev']}, se esperaba {expected_device}")
        routes[address] = route["dev"]
    trace = curl_tls(TRACE_HOST, TRACE_ADDRESS, "/cdn-cgi/trace")
    fields = dict(line.split("=", 1) for line in trace.stdout.decode().splitlines()
                  if "=" in line)
    return {"utc": utcnow(), "routes": routes, "egress": fields["ip"], "loc": fields["loc"]}


def query_doh(question, host, address):
    result = curl_tls(
        host, address, "/dns-query", "--header", "Content-Type: application/dns-message",
        "--header", "Accept: application/dns-message", "--data-binary", "@-",
        "--write-out", "%{stderr}\n%{http_version} %{content_type}\n",
        request=question.to_wire(),
    )
    version, mime = result.stderr.decode().strip().split(maxsplit=1)
    if version != "2" or mime.split(";")[0].strip() != "application/dns-message":
        raise ValueError(f"Respuesta DoH inesperada: {version} {mime}")
    return dns.message.from_wire(result.stdout), "doh_http2"


def query(profile, server, domain, category, qtype, round_no):
    row = dict(profile=profile, domain=domain, category=category, qtype=qtype,
               round=round_no, utc=utcnow())
    question = dns.message.make_query(domain, qtype, use_edns=0, want_dnssec=True)
    try:
        if profile == "dns_riseup":
            response, tcp = dns.query.udp_with_fallback(question, server, timeout=4)
            transport = "tcp" if tcp else "udp"
        else:
            response, transport = query_doh(question, *PROFILES[profile])
        if not question.is_response(response):
            raise ValueError("Respuesta DNS de otra consulta")
        row.update(error=None, transport=transport, **summarize_response(response))
    except (dns.exception.DNSException, ValueError, OSError, subprocess.CalledProcessError) as exc:
        row.update(error=type(exc).__name__)
    return row


def measure(args):
    profiles = list(PROFILES)
    if args.riseup_dns:
        if args.route != "riseup":
            raise ValueError("El DNS interno requiere la ruta Riseup")
        profiles.append("dns_riseup")
    cases = names()
    checks, answers = [], []
    for round_no in ROUNDS:
        before = route_check(args.device, args.riseup_dns)

        def one_profile(profile):
            rows = []
            for (domain, category), qtype in product(cases.items(), QTYPES):
                rows.append(query(profile, args.riseup_dns, domain, category, qtype, round_no))
                time.sleep(.12)
            return rows

        with ThreadPoolExecutor(max_workers=len(profiles)) as pool:
            answers.extend(row for rows in pool.map(one_profile, profiles) for row in rows)
        after = route_check(args.device, args.riseup_dns)
        if (before["egress"], before["loc"]) != (after["egress"], after["loc"]):
            raise RuntimeError("Cambió la salida durante la ronda")
        checks.append({"round": round_no, "before": before, "after": after})
    return {"route": args.route, "device": args.device, "native_dns": args.riseup_dns,
            "checks": checks, "answers": answers}


def state(row, warning):
    if row.get("error"):
        return "error"
    rcode = row["rcode"]
    if rcode != "NOERROR":
        return rcode.lower()
    addresses = row["addresses"]
    if warning and set(addresses) == set(warning):
        return "direccion_aviso"
    if not addresses:
        return "sin_direccion"
    if set(addresses) <= {"0.0.0.0", "::"}:
        return "sumidero"
    return "direccion"


def summarize(paths):
    cases = names()
    summary, egresses, by_route = {}, {}, {}
    for path, route_name in zip(paths, ROUTE_LABELS, strict=True):
        payload = path.read_bytes()
        data = json.loads(payload)
        if data["route"] != route_name:
            raise ValueError(f"Se esperaba {route_name} en {path}")
        profiles = list(PROFILES) + (["dns_riseup"] if route_name == "riseup" else [])
        checks = [r[key] for r in data["checks"] for key in ("before", "after")]
        egresses[route_name] = {c["egress"] for c in checks}
        if len(egresses[route_name]) != 1 or len(checks) != 4:
            raise ValueError(f"Salida inestable o comprobaciones incompletas en {route_name}")
        if any(dev != data["device"] for c in checks for dev in c["routes"].values()):
            raise ValueError(f"Interface inesperada en {route_name}")
        expected = Counter(product(profiles, cases, QTYPES, ROUNDS))
        if Counter((r["profile"], r["domain"], r["qtype"], r["round"])
                   for r in data["answers"]) != expected:
            raise ValueError(f"Mediciones incompletas en {route_name}")
        if any(row["category"] != cases[row["domain"]] for row in data["answers"]):
            raise ValueError(f"Cambió la categoría de un dominio en {route_name}")
        profile_summary = {}
        by_route[route_name] = {}
        for profile in profiles:
            rows = [r for r in data["answers"] if r["profile"] == profile]
            warning_rows = [r for r in rows if r["domain"] == WARNING_NAME]
            fingerprints = {
                r["qtype"]: r["addresses"] for r in warning_rows
                if not r["error"] and r["rcode"] == "NOERROR" and r["addresses"]
            }
            if profile.startswith("dns4eu") and (
                len(fingerprints) != len(QTYPES) or any(
                    r.get("addresses") != fingerprints.get(r["qtype"]) for r in warning_rows
                )
            ):
                raise ValueError(f"Calibración DNS4EU incompleta en {route_name} {profile}")
            if profile == "dns_riseup":
                fingerprints = {}
            by_route[route_name][profile] = {
                (row["domain"], row["qtype"], row["round"]): row
                for row in rows if row["category"] != "control"
            }
            groups = {}
            for category, qtype in product(sorted(set(cases.values())), QTYPES):
                group = [r for r in rows if r["category"] == category and r["qtype"] == qtype]
                groups.setdefault(category, {})[qtype] = {
                    "domains": len({r["domain"] for r in group}),
                    "observations": len(group),
                    "states": dict(sorted(Counter(
                        state(r, fingerprints.get(qtype)) for r in group
                    ).items())),
                }
            control_counts = {
                name: {qtype: dict(sorted(Counter(state(r, fingerprints.get(qtype))
                       for r in rows if r["domain"] == name and r["qtype"] == qtype).items()))
                       for qtype in QTYPES}
                for name in CONTROLS
            }
            profile_summary[profile] = {
                "observations": len(rows),
                "transport": dict(sorted(Counter(r.get("transport", "error") for r in rows).items())),
                "warning_addresses": fingerprints, "groups": groups, "controls": control_counts,
            }
        summary[route_name] = {
            "devices": [data["device"]], "countries": sorted({c["loc"] for c in checks}),
            "route_checks": len(checks), "dns_riseup": data["native_dns"],
            "started_utc": checks[0]["utc"], "finished_utc": checks[-1]["utc"],
            "sha256_raw": sha256(payload).hexdigest(), "profiles": profile_summary,
        }
    if egresses["directa"] & egresses["riseup"]:
        raise ValueError("Las dos rutas dieron la misma salida pública")
    matched = {}
    for profile in PROFILES:
        direct, through = [by_route[route][profile] for route in ROUTE_LABELS]
        verified = [(left, through[key]) for key, left in direct.items()
                    if not left["error"] and not through[key]["error"]]
        direct_warning = summary["directa"]["profiles"][profile]["warning_addresses"]
        tunnel_warning = summary["riseup"]["profiles"][profile]["warning_addresses"]
        matched[profile] = {
            "pairs_planned": len(direct),
            "pairs_with_both_responses": len(verified),
            "pairs_same_state": sum(
                state(left, direct_warning[left["qtype"]]) ==
                state(right, tunnel_warning[right["qtype"]])
                for left, right in verified
            ),
            "pairs_same_addresses": sum(left["addresses"] == right["addresses"]
                                         for left, right in verified),
        }
    return {"domains": cases, "rounds": len(ROUNDS), "egress_changed": True,
            "doh_profiles": {p: list(config) for p, config in PROFILES.items()},
            "matched_without_controls": matched, "routes": summary}


def main():
    parser = ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("medir")
    run.add_argument("route", choices=ROUTE_LABELS)
    run.add_argument("device")
    run.add_argument("output", type=Path)
    run.add_argument("--riseup-dns")
    combine = commands.add_parser("resumir")
    combine.add_argument("direct", type=Path)
    combine.add_argument("riseup", type=Path)
    combine.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("La salida ya existe; usar una ruta nueva")
    result = measure(args) if args.command == "medir" else summarize([args.direct, args.riseup])
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
