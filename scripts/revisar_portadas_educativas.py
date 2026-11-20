"""Registra la portada HTTPS de los portales cotejados en ROR y CRUCH o IPEDS."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlsplit

import httpx
from pdns_lab.corpus import read_corpus, sha256

LIMIT = 384 * 1024
ACADEMIC_PATH = re.compile(
    r"(?:^|[/_\-])(?:academics?|academic-programs|acad[eé]mic[oa]s?|admissions?|admisi[oó]n|"
    r"undergraduate|postgraduate|undergrad|pregrado|postgrado|carreras|degrees|majors|"
    r"undergraduate-studies)(?:[/_.\-]|$)", re.IGNORECASE)


class AcademicPage(HTMLParser):
    def __init__(self, url, domain):
        super().__init__()
        self.url = url
        self.domain = domain
        self.title = []
        self.in_title = False
        self.academic_links = []

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "a" and len(self.academic_links) < 2:
            href = dict(attrs).get("href")
            if not href:
                return
            dest = urlsplit(urljoin(self.url, href))
            name = dest.hostname or ""
            if (dest.scheme in {"http", "https"} and (name == self.domain or name.endswith("." + self.domain))
                    and ACADEMIC_PATH.search(unquote(dest.path))):
                link = name + dest.path
                if link not in self.academic_links:
                    self.academic_links.append(link[:200])

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def check_site(client, host):
    base = host.removeprefix("www.")
    url = "https://" + host + "/"
    row = {"dominio": host, "inicio_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        for attempt in range(4):
            with client.stream("GET", url) as response:
                row.update(url=url, http=response.status_code)
                if response.is_redirect and "location" in response.headers:
                    next_url = urlsplit(urljoin(url, response.headers["location"]))
                    if (next_url.scheme != "https" or next_url.hostname not in {base, "www." + base}
                            or next_url.port not in (443, None) or next_url.username or next_url.password):
                        row["estado"] = "redireccion_fuera_del_portal"
                        return row
                    if attempt == 3:
                        break
                    url = next_url.geturl()
                    continue
                if response.status_code != 200:
                    row["estado"] = "respuesta_http_sin_portada"
                    return row
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type:
                    row["estado"] = "tipo_distinto_de_html"
                    return row
                prefix = bytearray()
                for chunk in response.iter_bytes(chunk_size=8192):
                    prefix.extend(chunk[:LIMIT-len(prefix)])
                    if len(prefix) >= LIMIT:
                        break
                parser = AcademicPage(url, base)
                parser.feed(prefix.decode(response.encoding or "utf-8", errors="replace"))
                title = " ".join("".join(parser.title).split())[:150]
                row.update(titulo=title, enlaces_academicos=parser.academic_links,
                           bytes_leidos=len(prefix), sha256_bytes_leidos=hashlib.sha256(prefix).hexdigest())
                row["estado"] = "titulo_y_enlace_academico" if title and parser.academic_links else "html_sin_ambos_indicios"
                return row
        row["estado"] = "limite_de_redirecciones"
    except (httpx.HTTPError, ValueError, LookupError) as exc:
        row.update(estado="fallo_de_lectura", error=type(exc).__name__)
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("corpus", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    if args.output.exists():
        p.error("Indique una salida nueva para conservar las comprobaciones anteriores.")
    hosts = []
    for row in read_corpus(args.corpus):
        if row["categories"] != "educativo" or not row["sources"].startswith("["):
            continue
        for source in json.loads(row["sources"]):
            host = row["domain"]
            if (source.get("fuente") in {"CRUCH", "IPEDS HD2024"} and source.get("ROR", "").startswith("https://ror.org/")
                    and re.fullmatch(r"(?:www\.)?[a-z0-9-]+\.(?:cl|edu)", host)):
                hosts.append(host)
                break
    # Se consulta solo la portada de cada universidad. No se siguen enlaces ni se descargan sus recursos.
    with httpx.Client(timeout=5, trust_env=False, follow_redirects=False,
                      headers={"User-Agent": "Practica-DNS-VPN/1.0", "Accept": "text/html"}) as client:
        with ThreadPoolExecutor(max_workers=6) as workers:
            results = list(workers.map(lambda name: check_site(client, name), sorted(hosts)))
    summary = {"sha256_corpus": sha256(args.corpus), "portales": len(results), "max_bytes_por_portada": LIMIT,
               "estados": dict(sorted(Counter(r["estado"] for r in results).items())), "resultados": results}
    with args.output.open("x", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
