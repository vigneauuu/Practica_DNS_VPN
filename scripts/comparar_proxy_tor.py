"""Comprueba acceso HTTPS por ruta directa y por SOCKS5 local de Tor."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess

from pdns_lab.dnsprobe import utcnow


CONTROLS = ("example.com", "nudity.testcategory.com", "malware.testcategory.com",
            "no-existe-pdns-lab.invalid")
ROUNDS = (1, 2)
ROUTES = ("directa", "tor")
CHECK_URL = "https://check.torproject.org/api/ip"


def request(url, proxy, *options):
    return subprocess.run([
        "curl", "-q", "--silent", "--show-error", "--noproxy", "",
        "--proxy", proxy, "--proto", "=https", "--max-time", "15",
        *options, url,
    ], capture_output=True)


def verify(proxy, expected):
    result = request(CHECK_URL, proxy, "--fail")
    result.check_returncode()
    response = json.loads(result.stdout)
    if response["IsTor"] != expected:
        raise RuntimeError("El diagnóstico HTTPS indica una ruta distinta de la solicitada")
    return {"utc": utcnow(), "is_tor": response["IsTor"], "egress": response["IP"]}


def measure(port):
    runs = {}
    for route in ROUTES:
        proxy = f"socks5h://127.0.0.1:{port}" if route == "tor" else ""
        rounds = []
        for number in ROUNDS:
            before = verify(proxy, route == "tor")
            controls = {}
            for name in CONTROLS:
                result = request(f"https://{name}", proxy, "--head", "--output", "/dev/null",
                                 "--write-out", "%{response_code}")
                controls[name] = {"http_status": int(result.stdout), "curl_exit": result.returncode}
            after = verify(proxy, route == "tor")
            rounds.append({"number": number, "before": before, "after": after, "controls": controls})
        runs[route] = rounds
    return runs


def summarize(path, tor_version):
    body = path.read_bytes()
    runs = json.loads(body)
    result = {}
    for route in ROUTES:
        values = runs[route]
        if tuple(r["number"] for r in values) != ROUNDS:
            raise ValueError(f"Rondas incompletas: {route}")
        if any(set(r["controls"]) != set(CONTROLS) for r in values):
            raise ValueError(f"Controles incompletos: {route}")
        checks = [r[key] for r in values for key in ("before", "after")]
        if any(c["is_tor"] != (route == "tor") for c in checks):
            raise ValueError(f"No se confirmó la ruta: {route}")
        controls = {}
        for name in CONTROLS:
            observations = []
            for row in values:
                item = row["controls"][name]
                observations.append(f'http_{item["http_status"]}' if item["curl_exit"] == 0
                                    else f'curl_{item["curl_exit"]}')
            controls[name] = dict(sorted(Counter(observations).items()))
        result[route] = {
            "route_checks": len(checks), "is_tor": checks[0]["is_tor"], "controls": controls,
            "start_utc": checks[0]["utc"], "finish_utc": checks[-1]["utc"],
        }
    route_ips = [{r[key]["egress"] for r, key in product(runs[route], ("before", "after"))}
                 for route in ROUTES]
    if route_ips[0] & route_ips[1]:
        raise ValueError("El diagnóstico devolvió una salida compartida durante la medición")
    return {"tor_version": tor_version, "rounds_per_route": len(ROUNDS), "route_diagnostic": CHECK_URL,
            "head_requests": len(ROUTES) * len(ROUNDS) * len(CONTROLS),
            "sha256_raw": sha256(body).hexdigest(), "routes": result}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--port", type=int)
    options.add_argument("--summarize", type=Path)
    parser.add_argument("--tor-version", help="Versión del cliente en el registro original")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("La salida ya existe; usar una ruta nueva")
    if args.summarize and not args.tor_version:
        parser.error("--summarize requiere --tor-version")
    data = summarize(args.summarize, args.tor_version) if args.summarize else measure(args.port)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
