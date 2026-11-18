"""Resume las consultas DNS y los controles HTTPS de la comparación con WARP."""
from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path


DNS_PHASES = ("direct", "warp_off", "warp_full")
PROXY_PHASES = ("proxy_off", "proxy_full")
QTYPES = ("A", "AAAA")
ROUNDS = (1, 2)
VIA = ("direct", "socks5h")
CONTROLS = ("example.com", "no-existe-pdns-lab.invalid", "nudity.testcategory.com", "malware.testcategory.com")


def check_grid(rows, keys, grid):
    observed = Counter(tuple(row[key] for key in keys) for row in rows)
    if observed != Counter(grid):
        raise ValueError(f"Combinaciones ausentes, repetidas o inesperadas para {keys}")


def dns_phase(data, labels):
    phase = data["phase"]
    rows = data["dns"]
    check_grid(rows, ("domain", "qtype", "round"), product(labels, QTYPES, ROUNDS))
    if any(row["category"] != labels[row["domain"]] for row in rows):
        raise ValueError("Cambió la categoría de un dominio")
    check_grid(data["rounds"], ("number",), product(ROUNDS))
    tunneled = phase != "direct"
    expected_trace = "on" if tunneled else "off"
    checks = [rnd[when] for rnd in data["rounds"] for when in ("before", "after")]
    for check in checks:
        if check["trace"] != expected_trace or ("CloudflareWARP" in check["links"]) != tunneled:
            raise ValueError(f"Diagnóstico de ruta inesperado en {phase}")
        if (check["route_device"] == "CloudflareWARP") != tunneled:
            raise ValueError(f"Interfaz de salida inesperada en {phase}")
    category_counts = {}
    for category in sorted(set(labels.values())):
        category_counts[category] = {}
        for qtype in QTYPES:
            subset = [r for r in rows if r["category"] == category and r["qtype"] == qtype]
            category_counts[category][qtype] = {
                "domains": len({r["domain"] for r in subset}),
                "observations": len(subset),
                "states": dict(sorted(Counter(r["shape"] for r in subset).items())),
            }
    control_counts = {}
    for domain in CONTROLS:
        control_counts[domain] = {}
        for qtype in QTYPES:
            values = [r["shape"] for r in rows if r["domain"] == domain and r["qtype"] == qtype]
            control_counts[domain][qtype] = dict(sorted(Counter(values).items()))
    return {
        "observations": len(rows),
        "domains": len(labels),
        "trace": expected_trace,
        "route_checks": len(checks),
        "route_devices": sorted({check["route_device"] for check in checks}),
        "started_utc": data["rounds"][0]["before"]["utc"],
        "finished_utc": data["rounds"][-1]["after"]["utc"],
        "requested_policy": data["requested_policy"],
        "categories": category_counts,
        "controls": control_counts,
    }


def proxy_phase(data):
    rows = data["requests"]
    check_grid(rows, ("domain", "round", "via"), product(CONTROLS, ROUNDS, VIA))
    check_grid(data["rounds"], ("number",), product(ROUNDS))
    expected = {"direct": "off", "socks5h": "on"}
    checks = [rnd[when] for rnd in data["rounds"] for when in ("before", "after")]
    if any(check != expected for check in checks):
        raise ValueError("El diagnóstico de salida no respalda la comparación del proxy")
    outcomes = {}
    for domain in CONTROLS:
        outcomes[domain] = {}
        for via in VIA:
            subset = [row for row in rows if row["domain"] == domain and row["via"] == via]
            states = [f'HTTP_{r["code"]}' if r["code"] else f'curl_{r["curl_exit"]}' for r in subset]
            outcomes[domain][via] = dict(sorted(Counter(states).items()))
    return {
        "requests": len(rows),
        "requested_policy": data["requested_policy"],
        "trace": expected,
        "route_checks_per_path": len(checks),
        "outcomes": outcomes,
    }


def summarize(raw):
    labels = json.loads((raw / "domains.json").read_text())
    sources = {}
    dns, proxy = {}, {}
    for phase in DNS_PHASES + PROXY_PHASES:
        filename = f"{phase}.json"
        payload = (raw / filename).read_bytes()
        data = json.loads(payload)
        if data["phase"] != phase:
            raise ValueError(f"Fase incorrecta en {filename}")
        sources[filename] = sha256(payload).hexdigest()
        if phase in DNS_PHASES:
            dns[phase] = dns_phase(data, labels)
        else:
            proxy[phase] = proxy_phase(data)
    page_file = raw / "proxy_verify.json"
    page_bytes = page_file.read_bytes()
    pages = json.loads(page_bytes)
    sources[page_file.name] = sha256(page_bytes).hexdigest()
    page_domains = ("nudity.testcategory.com", "malware.testcategory.com")
    check_grid(pages["pages"], ("domain", "via"), product(page_domains, VIA))
    if pages["before"] != {"direct": "off", "socks5h": "on"} or pages["before"] != pages["after"]:
        raise ValueError("No se verificó la ruta en la comprobación del contenido")
    page_checks = {}
    for domain in page_domains:
        checks = [r for r in pages["pages"] if r["domain"] == domain]
        page_checks[domain] = {
            "same_sha256": checks[0]["sha256"] == checks[1]["sha256"],
            "body_bytes": {r["via"]: r["body_bytes"] for r in checks},
            "body_sha256": {r["via"]: r["sha256"] for r in checks},
        }
    sources["domains.json"] = sha256((raw / "domains.json").read_bytes()).hexdigest()
    return {
        "client": "Cloudflare WARP Linux 2026.8.2115.0",
        "tunnel_protocol": "MASQUE",
        "rounds_per_condition": len(ROUNDS),
        "source_sha256": sources,
        "dns": {"observations": sum(p["observations"] for p in dns.values()), "domains": len(labels), "phases": dns},
        "proxy": {
            "requests": sum(p["requests"] for p in proxy.values()),
            "domains": len(CONTROLS),
            "phases": proxy,
            "additional_get": {
                "requests": len(pages["pages"]),
                "requested_policy": pages["policy"],
                "trace_before_and_after": pages["before"],
                "controls": page_checks,
            },
        },
    }


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path, help="Carpeta con los registros originales")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = summarize(args.raw)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
