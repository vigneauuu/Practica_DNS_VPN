"""Reproduce el cotejo documental del inventario parental del 19 de noviembre."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
from urllib.parse import urlsplit
import zipfile

from pdns_lab.corpus import UT1_AGRESSIF_SHA256, read_corpus, sha256

ROOT = Path(__file__).resolve().parents[1]
ROR_ARCHIVE = "40bdfe53bcf8c5216ce9f1af35ab07b4851aa6083738654ac6c570834f98136b"
ROR_TABLE = "v2.16-2026-11-19-ror-data.csv"
CITIZEN_COMMIT = "fe6ca9beb46e127878b1448005347296787025ec"
CITIZEN_TABLES = "0d47b2c873d5930ca305412262331c08b1fd7ca18b6b16e42d4672be3e2e9105"


def homepage_host(url):
    parsed = urlsplit(url)
    if (parsed.scheme in {"http", "https"} and parsed.path in {"", "/"}
            and not parsed.query and not parsed.fragment):
        return parsed.hostname
    return None


def education_records(archive, candidates):
    if sha256(archive) != ROR_ARCHIVE:
        raise ValueError("La copia de ROR difiere de la edición v2.16 utilizada.")
    with zipfile.ZipFile(archive) as data, data.open(ROR_TABLE) as raw:
        for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8")):
            if row["status"] != "active" or "education" not in row["types"].split("; "):
                continue
            domains = set(row["domains"].lower().split("; "))
            sites = {homepage_host(url) for url in row["links.type.website"].split("; ")}
            for name in sorted(candidates.intersection(domains | sites)):
                yield name, {"fuente": "ROR", "registro": row["id"],
                             "campo": "domains" if name in domains else "links.type.website"}


def citizen_records(archive, inventory):
    wanted = {"apuestas": "GMB", "adultos": "PORN"}
    digest = hashlib.sha256()
    matches = []
    with zipfile.ZipFile(archive) as data:
        for name in sorted(data.namelist()):
            path = PurePosixPath(name)
            if path.parent.name != "lists" or path.suffix != ".csv" or path.name.startswith("00-"):
                continue
            raw = data.read(name)
            digest.update(f"{path.name} {hashlib.sha256(raw).hexdigest()}\n".encode())
            for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")):
                host = homepage_host(row["url"])
                if host not in inventory:
                    continue
                if wanted.get(inventory[host]["categories"]) == row["category_code"]:
                    matches.append((host, {"fuente": "Citizen Lab", "archivo": path.name,
                                           "url_registrada": row["url"], "codigo": row["category_code"],
                                           "fecha_incorporacion": row["date_added"]}))
    if digest.hexdigest() != CITIZEN_TABLES:
        raise ValueError("Las tablas de Citizen Lab difieren de la revisión utilizada.")
    return matches


def audit(ror, citizen, ut1):
    corpus_path = ROOT / "dataset/corpus-parental-candidatos.csv"
    pilot_path = ROOT / "dataset/piloto-50-2026-10-30.csv"
    subtel_path = ROOT / "docs/evidencia/contraste-apuestas-subtel-2026-11-18.json"
    snapshots = {
        corpus_path: "7c88702279954ed3875d818ad53e544a0f887f89d927c549b8b631dd2bbaba9c",
        pilot_path: "62bd71191d68863c08687db571a548259a46b9561416a59e424f3b48cda01885",
        subtel_path: "723c2475185a3e7c6f5e77aac6c3a7bbc4079f927022a04103c573e44e6f8fd3",
    }
    for path, expected in snapshots.items():
        if sha256(path) != expected:
            raise ValueError(f"El archivo {path.name} difiere de la edición del cotejo.")
    inventory = {r["domain"]: r for r in read_corpus(corpus_path)}
    pilot_edu = {r["domain"] for r in read_corpus(pilot_path) if r["categories"] == "educativo"}
    with tarfile.open(ut1) as data:
        original = data.extractfile("agressif/domains").read()
    legacy = ROOT / "dataset/armas_top400.csv"
    if original != legacy.read_bytes() or sha256(legacy) != UT1_AGRESSIF_SHA256:
        raise ValueError("agressif/domains y la copia heredada deben ser idénticos a la edición analizada.")
    source_names = set(original.decode().splitlines())
    excluded = {d for d, r in inventory.items() if r["categories"] == "armas" and d in source_names}

    subtel = json.loads(subtel_path.read_text(encoding="utf-8"))
    previous = next(r for r in subtel["resultados"] if r["archivo"] == "dataset/corpus-parental-candidatos.csv")
    evidence = defaultdict(list)
    for host in previous["nombres_coincidentes"]:
        if inventory[host]["categories"] != "apuestas":
            raise ValueError(f"La etiqueta de {host} difiere del cotejo previo de Subtel.")
        evidence[host].append({"fuente": "Subtel"})
    educational = {d for d, r in inventory.items() if r["categories"] in {"popular", "referencia_biblioteca"}}
    for host, entry in education_records(ror, educational):
        evidence[host].append(entry)
    for host, entry in citizen_records(citizen, inventory):
        evidence[host].append(entry)

    matches = []
    counts = Counter()
    by_source = Counter()
    for host, entries in sorted(evidence.items()):
        sources = {r["fuente"] for r in entries}
        by_source.update(sources)
        category = "institucion_educativa" if "ROR" in sources else inventory[host]["categories"]
        counts[category] += 1
        matches.append({"dominio": host, "grupo_inicial": inventory[host]["categories"],
                        "asociacion_documental": category, "evidencia": entries})
    matched = set(evidence)
    if matched & excluded:
        raise ValueError("Una coincidencia afecta a un dominio con procedencia en conflicto.")
    return {
        "fecha_cotejo": "2026-11-19",
        "fuentes": {
            "ROR": {"version": "2.16", "doi": "https://doi.org/10.5281/zenodo.24378467",
                    "sha256_zip": ROR_ARCHIVE},
            "Citizen Lab": {"commit": CITIZEN_COMMIT,
                            "url": f"https://github.com/citizenlab/test-lists/tree/{CITIZEN_COMMIT}",
                            "sha256_contenido_tablas": CITIZEN_TABLES},
            "UT1": {"url": "https://dsi.ut-capitole.fr/blacklists/download/agressif.tar.gz",
                    "miembro": "agressif/domains", "archivo_heredado": legacy.name,
                    "sha256_comun": UT1_AGRESSIF_SHA256},
            "Subtel": {"url": subtel["fuente"]["url"], "evidencia_previa": str(subtel_path.relative_to(ROOT)),
                       "sha256_evidencia": snapshots[subtel_path]},
        },
        "sha256_inventario": snapshots[corpus_path], "sha256_piloto": snapshots[pilot_path],
        "dominios_inventariados": len(inventory),
        "dominios_con_coincidencia": len(matched), "coincidencias_por_asociacion": dict(sorted(counts.items())),
        "dominios_por_fuente_positiva": dict(sorted(by_source.items())),
        "educativos_ROR_tambien_en_piloto": len(educational & matched & pilot_edu),
        "dominios_con_etiqueta_armas_retirada": len(excluded),
        "otros_sin_coincidencia_en_el_cotejo": len(inventory.keys() - matched - excluded),
        "validaciones_finales_asignadas_por_este_cotejo": 0,
        "coincidencias": matches,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ror", required=True, type=Path)
    parser.add_argument("--citizen", required=True, type=Path)
    parser.add_argument("--ut1", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.ror, args.citizen, args.ut1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
