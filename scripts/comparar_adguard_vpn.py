"""Registro de rutas y respuestas para una sesión de control de AdGuard VPN."""
from argparse import ArgumentParser
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from itertools import product
from pathlib import Path
import json
import subprocess
import time

from comparar_rutas_dns import QTYPES, ROUNDS, TRACE_ADDRESS, TRACE_HOST, WARNING_NAME, names, query_doh
from comparar_proxy_tor import CONTROLS as WEB_CONTROLS, request
import dns.exception
import dns.message
import dns.query
from pdns_lab.dnsprobe import summarize_response, utcnow

POLICIES = {
    "sin_filtro": ("unfiltered.adguard-dns.com", "94.140.14.140"),
    "familiar": ("family.adguard-dns.com", "94.140.14.15"),
}
MODES = ("referencia_doh", "tun", "socks", "resumir")
TUN_DNS_ADDRESS = "94.140.14.35"


def trace(proxy):
    response = request(f"https://{TRACE_HOST}/cdn-cgi/trace", proxy, "--fail",
                       *(("--resolve", f"{TRACE_HOST}:443:{TRACE_ADDRESS}") if not proxy else ()))
    response.check_returncode()
    fields = dict(line.split("=", 1) for line in response.stdout.decode().splitlines()
                  if "=" in line)
    return {"utc": utcnow(), "egress": fields["ip"], "country": fields["loc"]}


def dns_observation(name, category, qtype, round_no, args):
    row = dict(domain=name, category=category, qtype=qtype, round=round_no, utc=utcnow())
    question = dns.message.make_query(name, qtype, use_edns=0, want_dnssec=True)
    try:
        if args.mode == "tun":
            answer, via_tcp = dns.query.udp_with_fallback(question, args.resolver, timeout=6)
            transport = "tcp" if via_tcp else "udp"
        else:
            answer, transport = query_doh(question, *POLICIES[args.policy])
        if not question.is_response(answer):
            raise ValueError("Respuesta de otra pregunta")
        row.update(error=None, transport=transport, **summarize_response(answer))
    except (dns.exception.DNSException, OSError, ValueError, subprocess.CalledProcessError) as error:
        row["error"] = type(error).__name__
    return row


def route_snapshot(args):
    endpoints = [TRACE_ADDRESS]
    if args.mode == "tun":
        endpoints.append(args.resolver)
    routes = {}
    for endpoint in endpoints:
        route = json.loads(subprocess.check_output(["ip", "-j", "route", "get", endpoint]))[0]
        routes[endpoint] = route["dev"]
    if args.device and routes[TRACE_ADDRESS] != args.device:
        raise RuntimeError(f"Ruta inesperada para el diagnóstico: {routes[TRACE_ADDRESS]}")
    return {"devices": routes, **trace(proxy="")}


def measure_dns(args):
    cases = names()
    cases.pop(WARNING_NAME)
    checks = []
    rows = []
    for round_no in ROUNDS:
        before = route_snapshot(args)

        def sequence(qtype):
            results = []
            for name, category in cases.items():
                results.append(dns_observation(name, category, qtype, round_no, args))
                time.sleep(.10)
            return results

        with ThreadPoolExecutor(max_workers=len(QTYPES)) as pool:
            rows.extend(row for group in pool.map(sequence, QTYPES) for row in group)
        after = route_snapshot(args)
        if before["egress"] != after["egress"] or before["devices"] != after["devices"]:
            raise RuntimeError("Cambió la ruta durante la ronda")
        checks.append({"round": round_no, "before": before, "after": after})
    return {"mode": args.mode, "policy": args.policy, "configured_dns": args.resolver,
            "route_checks": checks, "answers": rows}


def measure_proxy(port):
    checks = []
    rows = []
    routes = {"direct": "", "proxy": f"socks5h://127.0.0.1:{port}"}
    for round_no in ROUNDS:
        before = {route: trace(proxy) for route, proxy in routes.items()}
        for route, name in product(routes, WEB_CONTROLS):
            result = request(f"https://{name}", routes[route], "--head", "--output", "/dev/null",
                             "--write-out", "%{response_code}")
            rows.append({"route": route, "domain": name, "round": round_no,
                         "status": int(result.stdout or b"0"), "curl_exit": result.returncode})
        after = {route: trace(proxy) for route, proxy in routes.items()}
        if any(probes["direct"]["egress"] == probes["proxy"]["egress"] for probes in (before, after)):
            raise RuntimeError("El proxy no produjo una salida IP distinta")
        checks.append({"round": round_no, "before": before, "after": after})
    return {"mode": "socks", "route_checks": checks, "requests": rows}


def dns_response(row):
    if row["error"]:
        return "error"
    if row["addresses"] == [TUN_DNS_ADDRESS]:
        return "direccion_aviso"
    if any(ede["code"] in (15, 16, 17) for ede in row["ede"]):
        return "ede_politica"
    if row["rcode"] != "NOERROR":
        return row["rcode"].lower()
    return "direccion" if row["addresses"] else "sin_direccion"


def summarize(path):
    file_map = {
        "doh_sin_filtro": "referencia-sin-filtro.json",
        "doh_familiar": "referencia-familiar.json",
        "tun_sin_filtro": "tun-sin_filtro.json",
        "tun_familiar": "tun-familiar.json",
        "socks": "socks.json",
    }
    cases = names()
    cases.pop(WARNING_NAME)
    expected = Counter(product(cases.items(), QTYPES, ROUNDS))
    phases, scopes = {}, {}
    for phase, file_name in file_map.items():
        source = (path / file_name).read_bytes()
        data = json.loads(source)
        if phase == "socks":
            checks = [probe for r in data["route_checks"] for key in ("before", "after")
                      for probe in (r[key],)]
            if any(probe["direct"]["egress"] == probe["proxy"]["egress"] for probe in checks):
                raise ValueError("No se verificó un cambio de salida por proxy")
            records = data["requests"]
            if Counter((r["route"], r["domain"], r["round"]) for r in records) != Counter(
                product(("direct", "proxy"), WEB_CONTROLS, ROUNDS)
            ):
                raise ValueError("Faltan solicitudes HTTPS o se repiten")
            controls = {route: {} for route in ("direct", "proxy")}
            for route, name in product(controls, WEB_CONTROLS):
                rows = [r for r in records if r["route"] == route and r["domain"] == name]
                controls[route][name] = dict(Counter(
                    f'http_{r["status"]}' if r["status"] else f'curl_{r["curl_exit"]}' for r in rows
                ))
            phases[phase] = {"requests": len(records), "controls_by_route": controls,
                             "route_checks": len(checks), "egress_changes": True,
                             "started_utc": checks[0]["direct"]["utc"],
                             "finished_utc": checks[-1]["proxy"]["utc"]}
        else:
            rows = data["answers"]
            if Counter(((r["domain"], r["category"]), r["qtype"], r["round"])
                       for r in rows) != expected:
                raise ValueError(f"Consultas incompletas en {phase}")
            checks = [r[key] for r in data["route_checks"] for key in ("before", "after")]
            scopes[phase] = {r["egress"] for r in checks}
            expected_device = "tun0" if phase.startswith("tun") else None
            if expected_device and any(set(r["devices"].values()) != {expected_device} for r in checks):
                raise ValueError(f"Salida inesperada en {phase}")
            groups = {}
            for category, qtype in product(sorted(set(cases.values())), QTYPES):
                subset = [r for r in rows if r["category"] == category and r["qtype"] == qtype]
                groups.setdefault(category, {})[qtype] = {
                    "queries": len(subset),
                    "states": dict(sorted(Counter(dns_response(r) for r in subset).items())),
                }
            phases[phase] = {"queries": len(rows), "answers": sum(r["error"] is None for r in rows),
                             "transport": dict(Counter(r.get("transport", "error") for r in rows)),
                             "route_checks": len(checks),
                             "route_interfaces": sorted({v for r in checks for v in r["devices"].values()}),
                             "resolver_in_container": data["configured_dns"],
                             "countries": sorted({r["country"] for r in checks}),
                             "started_utc": checks[0]["utc"], "finished_utc": checks[-1]["utc"],
                             "groups": groups}
        phases[phase]["raw_sha256"] = sha256(source).hexdigest()
    return {"domains": cases, "rounds_per_phase": len(ROUNDS),
            "tunnel_same_egress": len(scopes["tun_sin_filtro"] | scopes["tun_familiar"]) == 1,
            "tunnel_splits_from_reference": not bool(
                (scopes["tun_sin_filtro"] | scopes["tun_familiar"]) &
                (scopes["doh_sin_filtro"] | scopes["doh_familiar"])
            ), "phases": phases}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=MODES)
    parser.add_argument("output", type=Path)
    parser.add_argument("--policy", choices=POLICIES)
    parser.add_argument("--resolver")
    parser.add_argument("--device")
    parser.add_argument("--port", type=int, default=19080)
    parser.add_argument("--datos", type=Path, help="Directorio con las cinco fases originales")
    args = parser.parse_args()
    if args.mode in ("referencia_doh", "tun") and not args.policy:
        parser.error("La prueba DNS requiere --policy")
    if args.mode == "tun" and not (args.resolver and args.device):
        parser.error("El túnel requiere resolutor del sistema y dispositivo observado")
    if args.output.exists():
        parser.error("La salida ya existe")
    if args.mode == "resumir":
        if not args.datos:
            parser.error("El resumen requiere --datos")
        data = summarize(args.datos)
    elif args.mode == "socks":
        data = measure_proxy(args.port)
    else:
        data = measure_dns(args)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
