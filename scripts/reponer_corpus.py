"""Construye el inventario de candidatos tras retirar las etiquetas de armas de UT1."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import random
import re
from urllib.parse import urlsplit
import zipfile

from cotejar_inventario import ROR_ARCHIVE, ROR_TABLE, homepage_host
from pdns_lab.corpus import experimental_rows, normalize_domain, read_corpus, sha256, write_corpus

ROOT = Path(__file__).resolve().parents[1]
CRUCH = "https://consejoderectores.cl/el-consejo/universidades-cruch/"
IPEDS = "https://nces.ed.gov/ipeds/datacenter/data/HD2024.zip"
IPEDS_SHA = "d98425c123d7c0e872aec6e83960dfb501884818bf17385c340790f3d1f28345"
CRUCH_SITES_SHA = "a4af429036d02b1e3ee20590c9b1ec5c8e7b54116483c2becee6c2dc7af241b0"


class MemberMap(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sites = {}

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag != "g" or not values.get("id", "").startswith("duo_"):
            return
        action = re.fullmatch(r"window\.open\('([^']+)', '_blank'\)", values.get("onclick", ""))
        if action:
            self.sites[action[1]] = values["title"]


def official_sites(ror, ipeds, cruch):
    if sha256(ror) != ROR_ARCHIVE or sha256(ipeds) != IPEDS_SHA:
        raise ValueError("La edición de ROR o de IPEDS difiere del cotejo publicado.")
    # Se conserva el nombre exacto de cada página institucional, incluido www.
    ror_by_host = defaultdict(dict)
    with zipfile.ZipFile(ror) as z, z.open(ROR_TABLE) as stream:
        rows = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8"))
        for row in rows:
            if "education" not in row["types"].split("; ") or row["status"] != "active":
                continue
            hosts = set(row["domains"].lower().split("; "))
            hosts.update(homepage_host(url) for url in row["links.type.website"].split("; "))
            for host in hosts:
                if host and host.endswith((".cl", ".edu")):
                    ror_by_host[host][row["id"]] = row["locations.geonames_details.country_code"]
    directories = defaultdict(list)
    if cruch.suffix == ".csv":
        with cruch.open(encoding="utf-8", newline="") as f:
            members = {r["url"]: r["institucion"] for r in csv.DictReader(f)}
    else:
        parser = MemberMap()
        parser.feed(cruch.read_text(encoding="utf-8"))
        members = parser.sites
    signature = json.dumps(sorted(members.items()), ensure_ascii=False).encode()
    if hashlib.sha256(signature).hexdigest() != CRUCH_SITES_SHA:
        raise ValueError("La lista de universidades del CRUCH difiere de la edición consultada.")
    for url, name in members.items():
        host = homepage_host(url)
        if host:
            directories[host].append({"fuente": "CRUCH", "pais": "CL", "institucion": name,
                                      "pagina_en_directorio": url, "directorio": CRUCH})
    with zipfile.ZipFile(ipeds) as z, z.open("HD2024.csv") as stream:
        rows = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"))
        for row in rows:
            if row["CYACTIVE"] != "1" or row["DEGGRANT"] != "1":
                continue
            url = row["WEBADDR"].strip()
            host = homepage_host(url if "://" in url else "https://" + url)
            if host and re.fullmatch(r"(?:www\.)?[a-z0-9-]+\.edu", host):
                directories[host].append({"fuente": "IPEDS HD2024", "pais": "US",
                                          "institucion": row["INSTNM"], "UNITID": row["UNITID"],
                                          "pagina_en_directorio": url})
    sites = {}
    for host, records in directories.items():
        if len(records) != 1 or len(ror_by_host.get(host, {})) != 1:
            continue
        ror_id, country = next(iter(ror_by_host[host].items()))
        if country == records[0]["pais"]:
            sites[host] = {**records[0], "ROR": ror_id}
    return sites, len(members)


def inventory_row(host, category, evidence):
    return {"domain": normalize_domain(host), "categories": category,
            "sources": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            "validation_status": "pending", "validation_evidence": "",
            "reviewer": "", "reviewed_at": ""}


def assemble(ror, ipeds, cruch):
    dataset = ROOT / "dataset"
    docs = ROOT / "docs/evidencia"
    initial = read_corpus(dataset / "corpus-parental-candidatos.csv")
    kept = list(experimental_rows(initial))
    historical = read_corpus(dataset / "corpus.csv")
    used = {r["domain"] for r in initial + historical}
    additions = {}
    methods = Counter()

    def add(host, category, evidence, method):
        if host not in used:
            additions[host] = inventory_row(host, category, evidence)
            methods[method] += 1
            used.add(host)

    pilot = json.loads((docs / "piloto-50-revision-documental.json").read_text())
    subtel = json.loads((docs / "contraste-apuestas-subtel-2026-11-18.json").read_text())
    panel = dataset / "referencia-politica-dns4eu-2026-11-19.csv"
    with panel.open(encoding="utf-8", newline="") as f:
        betting = [r for r in csv.DictReader(f) if r["categories"] == "apuestas"]
    names = [urlsplit(r["source_url"]).hostname for r in betting]
    digest = hashlib.sha256(("\n".join(names) + "\n").encode()).hexdigest()
    if digest != subtel["sha256_nombres_de_host"] or names != [r["domain"] for r in betting]:
        raise ValueError("El panel de apuestas difiere de la nómina de Subtel.")
    for index, host in enumerate(names, 1):
        add(host, "apuestas", [{"directorio": subtel["fuente"]["url"], "posicion": index,
                                "url_en_nomina": betting[index-1]["source_url"]}], "Subtel")
    ofcom = dataset / "referencia-adulto-ofcom-2026-11-19.csv"
    with ofcom.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["categories"] == "adultos":
                add(row["domain"], "adultos", [{"fuente": "Ofcom, decisión sobre AVS Group Ltd",
                    "documento": row["source_url"], "apartados": ["3.2", "3.40"]}], "Ofcom")
    for r in pilot:
        add(r["domain"], r["category"], [{"ficha": "docs/evidencia/piloto-50-revision-documental.json",
                                          "url_documental": r["url"], "fecha_evidencia": r["review_date"]}],
            "Piloto")
    sites, member_count = official_sites(ror, ipeds, cruch)
    excluded_aliases = {h.removeprefix("www.") for h in used}
    sites = {h: v for h, v in sites.items() if h.removeprefix("www.") not in excluded_aliases}
    config = json.loads((ROOT / "config/estudio.json").read_text())
    by_country = Counter(e["pais"] for e in sites.values())
    remaining = config["target_unique_domains"] - len(kept) - len(additions)
    local = sorted(h for h, e in sites.items() if e["pais"] == "CL")
    usa = sorted(h for h, e in sites.items() if e["pais"] == "US")
    # Sin cuotas de categorías. Los portales chilenos entran primero por el lugar del estudio.
    rng = random.Random(config["seed"])
    rng.shuffle(usa)
    for host in local + usa:
        if remaining <= 0:
            break
        alias = host.removeprefix("www.")
        if alias in excluded_aliases:
            continue
        e = sites[host]
        add(host, "educativo", [e], e["fuente"])
        excluded_aliases.add(alias)
        remaining -= 1
    if remaining != 0:
        raise ValueError("El conjunto documental no permite alcanzar la meta.")
    rows = sorted(kept + list(additions.values()), key=lambda r: r["domain"])
    summary = {"filas_iniciales": len(initial), "filas_conservadas": len(kept),
               "etiquetas_armas_retiradas": len(initial) - len(kept), "incorporaciones": len(additions),
               "incorporaciones_por_fuente": dict(sorted(methods.items())),
               "incorporaciones_por_categoria": dict(sorted(Counter(r["categories"] for r in additions.values()).items())),
               "composicion": dict(sorted(Counter(r["categories"] for r in rows).items())),
               "dominios_unicos": len({r["domain"] for r in rows}),
               "revisiones_finales": sum(r["validation_status"] == "validated" for r in rows),
               "portales_directorio_CRUCH": member_count,
               "coincidencias_educativas_disponibles_por_pais": dict(sorted(by_country.items())),
               "semilla": config["seed"], "sha256_registros_CRUCH": CRUCH_SITES_SHA, "sha256_IPEDS": IPEDS_SHA,
               "sha256_ROR": ROR_ARCHIVE, "sha256_panel": sha256(panel), "sha256_lista_Ofcom": sha256(ofcom),
               "sha256_inventario_anterior": sha256(dataset / "corpus-parental-candidatos.csv"),
               "sha256_piloto_documental": sha256(docs / "piloto-50-revision-documental.json")}
    return rows, summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("ror", "ipeds", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    p.add_argument("--cruch", type=Path, default=ROOT / "dataset/fuentes/directorio_cruch_2026-11-19.csv")
    args = p.parse_args()
    manifest = args.output.with_suffix(".build.json")
    if args.output.exists() or manifest.exists():
        p.error("Elegir una ruta nueva para conservar las revisiones existentes.")
    rows, summary = assemble(args.ror, args.ipeds, args.cruch)
    write_corpus(args.output, rows)
    summary["sha256_corpus"] = sha256(args.output)
    manifest.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
