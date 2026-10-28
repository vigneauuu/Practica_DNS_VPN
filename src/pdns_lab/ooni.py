"""Intercambio local con OONI, sin ejecutar ni publicar mediciones."""
import json
from pathlib import Path
from urllib.parse import urlsplit
from .corpus import normalize_domain


def export_urls(rows, path):
    validated = [r for r in rows if r["validation_status"] == "validated"]
    if not validated:
        raise ValueError("No hay dominios con categorías validadas para exportar")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f'https://{r["domain"]}/\n' for r in validated), encoding="utf-8")
    return len(validated)


def import_measurements(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        items = data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        items = [json.loads(line) for line in text.splitlines() if line.strip()]
    rows = []
    for item in items:
        if item.get("test_name") != "web_connectivity":
            continue
        test = item.get("test_keys") or {}
        url = item.get("input", "")
        host = urlsplit(url).hostname
        if not host:
            continue
        # Se conserva la evaluación original; no se interpreta "blocking" como booleano.
        rows.append({"domain": normalize_domain(host), "input": url,
                     "measurement_start_time": item.get("measurement_start_time"),
                     "test_version": item.get("test_version"), "software_version": item.get("software_version"),
                     "probe_cc": item.get("probe_cc"), "probe_asn": item.get("probe_asn"),
                     "accessible": test.get("accessible"), "blocking": test.get("blocking"),
                     "dns_consistency": test.get("dns_consistency"),
                     "http_experiment_failure": test.get("http_experiment_failure")})
    return rows
