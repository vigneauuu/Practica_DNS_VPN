"""Compara el filtro infantil de DNS4EU con una referencia documental."""

import argparse
import csv
import hashlib
import ipaddress
import json
from collections import Counter
from itertools import product
from pathlib import Path

from contrastar_doh import CONTROLS, DNS4EU_ENDPOINTS


AVISO = "warning.joindns4.eu"
INFANTIL = "dns4eu_child"
REFERENCIAS = ("dns4eu_unfiltered", "dns4eu_protective")
TIPOS = {"A": 4, "AAAA": 6}
RONDAS = (1, 2)


def direcciones_validas(fila):
    if fila["error"] or fila["rcode"] != "NOERROR":
        return set()
    direcciones = {ipaddress.ip_address(valor) for valor in fila["addresses"]}
    return {
        str(direccion)
        for direccion in direcciones
        if direccion.version == TIPOS[fila["qtype"]]
        and not direccion.is_unspecified
        and not direccion.is_loopback
    }


def estado(fila, aviso):
    if fila["error"]:
        return "error"
    direcciones = direcciones_validas(fila)
    if direcciones and direcciones <= aviso:
        return "aviso"
    if direcciones & aviso or any(ede["code"] in (15, 16, 17) for ede in fila["ede"]):
        return "otra_senal"
    if direcciones:
        return "direccion"
    return "sin_direccion"


def evaluar(observado, esperado):
    if any(rondas != ["direccion", "direccion"] for perfil, rondas in observado.items()
           if perfil in REFERENCIAS):
        return "sin_referencia"
    infantil = observado[INFANTIL]
    if infantil == ["aviso", "aviso"]:
        return "restriccion_observada" if esperado == "restringir" else "aviso_en_educativo"
    if infantil == ["direccion", "direccion"]:
        return "sin_senal" if esperado == "restringir" else "resolucion_observada"
    return "infantil_indeterminado"


def huella(ruta):
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("referencia", type=Path)
    parser.add_argument("respuestas", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--programa-medicion", type=Path,
                        default=Path(__file__).with_name("contrastar_doh.py"),
                        help="copia del programa que generó las respuestas")
    args = parser.parse_args()
    with args.referencia.open(encoding="utf-8", newline="") as archivo:
        casos = list(csv.DictReader(archivo))
    filas = json.loads(args.respuestas.read_text(encoding="utf-8"))
    nombres = {caso["domain"] for caso in casos}
    controles = {*CONTROLS, AVISO}
    indice = {(f["domain"], f["qtype"], f["profile"], f["round"]): f for f in filas}
    previstas = set(product(nombres | controles, TIPOS, DNS4EU_ENDPOINTS, RONDAS))
    if (len(nombres) != len(casos) or nombres & controles or len(indice) != len(filas)
            or previstas != indice.keys()):
        parser.error("Se requieren dos rondas completas de los tres perfiles, sin filas duplicadas")

    avisos = {}
    for tipo in TIPOS:
        calibracion = [direcciones_validas(indice[AVISO, tipo, perfil, ronda])
                       for perfil, ronda in product(DNS4EU_ENDPOINTS, RONDAS)]
        if not calibracion[0] or any(ips != calibracion[0] for ips in calibracion):
            parser.error(f"Direcciones de aviso inconsistentes para {tipo}")
        avisos[tipo] = calibracion[0]

    def observaciones(nombre, tipo):
        return {perfil: [estado(indice[nombre, tipo, perfil, r], avisos[tipo]) for r in RONDAS]
                for perfil in DNS4EU_ENDPOINTS}

    detalle = []
    conteos = {}
    for caso, tipo in product(casos, TIPOS):
        categoria = caso["categories"]
        esperado = caso["expected_child"]
        if esperado not in {"restringir", "resolver"}:
            parser.error(f"Decisión esperada inválida para {caso['domain']}")
        observado = observaciones(caso["domain"], tipo)
        resultado = evaluar(observado, esperado)
        conteos.setdefault(categoria, {}).setdefault(tipo, Counter())[resultado] += 1
        detalle.append({"dominio": caso["domain"], "categoria": categoria, "tipo": tipo,
                        "esperado": esperado, "perfiles": observado, "resultado": resultado})

    horas = [fila["started_at_utc"] for fila in filas]
    informe = {
        "ventana_inicio_consultas_utc": [min(horas), max(horas)],
        "entrada": str(args.referencia),
        "sha256_entrada": huella(args.referencia),
        "sha256_respuestas_locales": huella(args.respuestas),
        "sha256_programa_medicion": huella(args.programa_medicion),
        "consultas": len(filas),
        "respuestas_dns": sum(not fila["error"] for fila in filas),
        "version_http": dict(Counter(fila["http_version"] for fila in filas if not fila["error"])),
        "direcciones_aviso": {tipo: sorted(ips) for tipo, ips in avisos.items()},
        "controles": {dominio: {tipo: observaciones(dominio, tipo) for tipo in TIPOS}
                      for dominio in sorted(controles)},
        "resultados_por_dominio": conteos,
        "detalle": detalle,
    }
    with args.salida.open("x", encoding="utf-8") as archivo:
        json.dump(informe, archivo, indent=2, ensure_ascii=False)
        archivo.write("\n")


if __name__ == "__main__":
    main()
