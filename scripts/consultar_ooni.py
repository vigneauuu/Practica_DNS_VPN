"""Consulta metadatos públicos de OONI y conserva los campos que usa el estudio."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode
from urllib.request import urlopen

from pdns_lab.ooni import import_measurements


API = "https://api.ooni.io/api/v1"
URL_CONTROL = "https://example.com/"
CONTROLES_CL = (
    "example.com",
    "cam.ac.uk",
    "cambridgeenglish.org",
    "ehess.fr",
    "em-lyon.com",
)
DIAS_CONTROL = (("2026-11-18", "2026-11-19"), ("2026-11-19", "2026-11-20"))


def consultar(recurso, parametros):
    url = f"{API}/{recurso}?{urlencode(parametros)}"
    with urlopen(url, timeout=35) as respuesta:
        cuerpo = respuesta.read()
    return url, cuerpo


def resumir_medicion(publica, archivo_temporal):
    uid = publica["measurement_uid"]
    url, cuerpo = consultar("raw_measurement", {"measurement_uid": uid})
    archivo_temporal.write_bytes(cuerpo)
    medicion, = import_measurements(archivo_temporal)
    if medicion["input"] != URL_CONTROL:
        raise ValueError(f"La medición {uid} no corresponde a {URL_CONTROL}")
    return {
        "identificador": uid,
        "medicion_original": url,
        "sha256_original": sha256(cuerpo).hexdigest(),
        "anomalia_segun_indice": publica["anomaly"],
        "confirmado_segun_indice": publica["confirmed"],
        "fallo_segun_indice": publica["failure"],
        **medicion,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida", type=Path, help="Archivo JSON de resultados públicos")
    args = parser.parse_args()
    salida = {
        "fecha_consulta_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "busquedas_chile": [],
        "control_publico": [],
    }
    for dominio in CONTROLES_CL:
        url, cuerpo = consultar("measurements", {
            "test_name": "web_connectivity", "probe_cc": "CL", "domain": dominio,
            "since": "2026-10-20", "until": "2026-11-20", "limit": 5,
        })
        respuesta = json.loads(cuerpo)
        salida["busquedas_chile"].append({
            "dominio": dominio,
            "consulta": url,
            "filas_en_pagina": len(respuesta["results"]),
            "siguiente_pagina": bool(respuesta["metadata"]["next_url"]),
        })

    with TemporaryDirectory() as temporal:
        archivo_temporal = Path(temporal) / "medicion.json"
        for desde, hasta in DIAS_CONTROL:
            url, cuerpo = consultar("measurements", {
                "test_name": "web_connectivity", "input": URL_CONTROL,
                "since": desde, "until": hasta, "limit": 5,
            })
            respuesta = json.loads(cuerpo)
            salida["control_publico"].append({
                "consulta": url,
                "siguiente_pagina": bool(respuesta["metadata"]["next_url"]),
                "mediciones": [
                    resumir_medicion(publica, archivo_temporal)
                    for publica in respuesta["results"]
                ],
            })
    args.salida.write_text(json.dumps(salida, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
