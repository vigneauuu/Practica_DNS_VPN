"""Resume el contraste de perfiles familiares de Cloudflare y AdGuard por dominio."""

import argparse
import csv
import json
from collections import Counter
from itertools import product
from pathlib import Path

from contrastar_doh import CONTROLS, FAMILY_ENDPOINTS
from evaluar_politica_dns4eu import RONDAS, TIPOS, direcciones_validas, evaluar, huella


PERFILES = {
    "cloudflare": ("cloudflare_family", ("cloudflare_standard", "cloudflare_security")),
    "adguard": ("adguard_family", ("adguard_open", "adguard_default")),
}
AVISO_ADGUARD = "94.140.14.35"
FUENTE_AVISO_ADGUARD = "https://github.com/AdguardTeam/AdGuardHome/issues/5028"


def estado(fila):
    if fila["error"]:
        return "error"
    ips = direcciones_validas(fila)
    if any(ede["code"] in (15, 16, 17) for ede in fila["ede"]):
        return "aviso"
    if fila["profile"].startswith("adguard_") and AVISO_ADGUARD in ips:
        return "aviso" if ips == {AVISO_ADGUARD} else "mezcla"
    return "direccion" if ips else "sin_direccion"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("referencia", type=Path)
    parser.add_argument("respuestas", type=Path)
    parser.add_argument("resultado", type=Path)
    args = parser.parse_args()
    with args.referencia.open(encoding="utf-8", newline="") as archivo:
        corpus = {row["domain"]: row["categories"] for row in csv.DictReader(archivo)}
    if set(corpus.values()) != {"adultos", "educativo"} or set(corpus) & set(CONTROLS):
        parser.error("El conjunto debe contener solo adultos y educativos con fuente documentada")
    filas = json.loads(args.respuestas.read_text(encoding="utf-8"))
    indice = {(r["domain"], r["qtype"], r["profile"], r["round"]): r for r in filas}
    if len(indice) != len(filas) or indice.keys() != set(product(
            set(corpus) | set(CONTROLS), TIPOS, FAMILY_ENDPOINTS, RONDAS)):
        parser.error("La ejecución debe registrar las dos rondas de los seis perfiles")

    def observaciones(nombre, tipo, perfiles):
        return {p: [estado(indice[nombre, tipo, p, r]) for r in RONDAS] for p in perfiles}

    detalle = []
    resumen = {}
    for (nombre, categoria), tipo, (operador, (familiar, referencias)) in product(
            corpus.items(), TIPOS, PERFILES.items()):
        esperado = "restringir" if categoria == "adultos" else "resolver"
        estados = observaciones(nombre, tipo, (familiar, *referencias))
        resultado = evaluar(estados, esperado, infantil=familiar, referencias=referencias)
        resumen.setdefault(operador, {}).setdefault(tipo, {}).setdefault(categoria, Counter())[resultado] += 1
        detalle.append({"dominio": nombre, "categoria": categoria, "tipo": tipo, "operador": operador,
                        "esperado": esperado, "perfiles": estados, "resultado": resultado})
    horas = [fila["started_at_utc"] for fila in filas]
    total = {
        "ventana_inicio_utc": [min(horas), max(horas)],
        "sha256_referencia": huella(args.referencia),
        "sha256_respuestas_locales": huella(args.respuestas),
        "consultas": len(filas),
        "respuestas_dns": sum(not fila["error"] for fila in filas),
        "version_http": Counter(r.get("http_version") for r in filas if not r["error"]),
        "errores_por_perfil": Counter(r["profile"] for r in filas if r["error"]),
        "aviso_adguard": {"direccion": AVISO_ADGUARD, "fuente": FUENTE_AVISO_ADGUARD},
        "controles": {nombre: {tipo: observaciones(nombre, tipo, FAMILY_ENDPOINTS) for tipo in TIPOS}
                      for nombre in CONTROLS},
        "por_dominio": resumen,
        "detalle": detalle,
    }
    with args.resultado.open("x", encoding="utf-8") as archivo:
        json.dump(total, archivo, ensure_ascii=False, indent=2)
        archivo.write("\n")


if __name__ == "__main__":
    main()
