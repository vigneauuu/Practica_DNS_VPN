#!/usr/bin/env python3
"""Benchmark unificado e insesgado (A-Z) de los 9 proveedores PDNS (20 perfiles DoH HTTP/2).

Corrige el sesgo de truncamiento lexicográfico detectado al auditar las muestras heredadas
(adultos_top400.csv con 100 % prefijo '0' y casinos_top400.csv con 96 % en '0-9'/'a')
mediante muestreo aleatorio uniforme sin reemplazo (semilla fija 20261126) sobre los
listados oficiales completos de UT1 adult/domains (4.590.350 dominios válidos) y
StevenBlack gambling-only/hosts (6.744 dominios válidos).

Evalúa 548 nombres en total:
- 42 sitios chilenos de apuestas (nómina oficial Subtel/SCJ, 01-09-2026)
- 22 plataformas adultas regulatorias (Comisión Europea DSA + Ofcom)
- 13 fabricantes oficiales de armas de fuego
- 166 portales universitarios CRUCH/IPEDS con portada HTTPS verificada
- 150 candidatos adultos muestreados uniformemente A-Z desde UT1 adult/domains
- 150 candidatos de apuestas muestreados uniformemente A-Z desde StevenBlack gambling
- 5 controles técnicos conocidos
"""
from __future__ import annotations

import asyncio
import csv
import datetime as dt
import hashlib
import ipaddress
import json
import random
import re
import tarfile
import time
from collections import Counter, defaultdict
from pathlib import Path

import dns.flags
import dns.message
import dns.rcode
import dns.rdatatype
import httpx

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT.parent / "material_original" / "bibliografia"
UT1_ADULT_TAR = ARCHIVE_DIR / "ut1_adult_2026-11-26.tar.gz"
SB_GAMBLING_HOSTS = ARCHIVE_DIR / "stevenblack_gambling_2026-11-26.hosts"

DATASET_OUT = ROOT / "dataset" / "benchmark-pdns-2026-11-26.csv"
RAW_OUT = ROOT / "results" / "benchmark-pdns-2026-11-26" / "raw.jsonl"
EVIDENCE_OUT = ROOT / "docs" / "evidencia" / "benchmark-pdns-2026-11-26.json"

SEED = 20261126
ROUNDS = 2
QTYPES = ("A", "AAAA")
N_CAND_ADULT = 150
N_CAND_GAMBLING = 150

WEAPONS_VERIFIED = [
    ("ruger.com", "Fabricante oficial de armas (Sturm, Ruger & Co., catálogo oficial)"),
    ("sigsauer.com", "Fabricante oficial de armas (SIG Sauer, catálogo oficial)"),
    ("smith-wesson.com", "Fabricante oficial de armas (Smith & Wesson, catálogo oficial)"),
    ("glock.com", "Fabricante oficial de armas (GLOCK Ges.m.b.H., catálogo oficial)"),
    ("beretta.com", "Fabricante oficial de armas (Fabbrica d'Armi Pietro Beretta, catálogo oficial)"),
    ("colt.com", "Fabricante oficial de armas (Colt's Manufacturing Company, catálogo oficial)"),
    ("mossberg.com", "Fabricante oficial de armas (O.F. Mossberg & Sons, catálogo oficial)"),
    ("winchester.com", "Fabricante oficial de armas (Winchester Repeating Arms, catálogo oficial)"),
    ("springfield-armory.com", "Fabricante oficial de armas (Springfield Armory, catálogo oficial)"),
    ("heckler-koch.com", "Fabricante oficial de armas (Heckler & Koch, catálogo oficial)"),
    ("taurususa.com", "Fabricante oficial de armas (Taurus Armas, catálogo oficial)"),
    ("browning.com", "Fabricante oficial de armas (Browning Arms Company, catálogo oficial)"),
    ("fnherstal.com", "Fabricante oficial de armas (FN Herstal, catálogo oficial)"),
]

CONTROLS = [
    ("example.com", "control_tecnico", "Control positivo IANA (RFC 2606)"),
    ("no-existe-pdns-lab.invalid", "control_tecnico", "Control NXDOMAIN legítimo (RFC 2606)"),
    ("nudity.testcategory.com", "control_tecnico", "Control de categoría adulto Cloudflare"),
    ("malware.testcategory.com", "control_tecnico", "Control de categoría malware Cloudflare"),
    ("warning.joindns4.eu", "control_tecnico", "Calibración de dirección de aviso DNS4EU"),
]

# Todos los 20 perfiles lógicos de los 9 proveedores vía DoH HTTP/2.
# Nota metodológica explícita: CleanBrowsing no dispone de un perfil gratuito sin filtro,
# por lo que sus dos perfiles utilizan cloudflare_standard como referencia externa abierta.
PROFILES = [
    {"id": "cloudflare_standard", "provider": "Cloudflare", "role": "reference", "ref": None, "ref_type": None,
     "url": "https://cloudflare-dns.com/dns-query"},
    {"id": "cloudflare_security", "provider": "Cloudflare", "role": "security", "ref": "cloudflare_standard", "ref_type": "intra_provider",
     "url": "https://security.cloudflare-dns.com/dns-query"},
    {"id": "cloudflare_family", "provider": "Cloudflare", "role": "parental", "ref": "cloudflare_standard", "ref_type": "intra_provider",
     "url": "https://family.cloudflare-dns.com/dns-query", "declares": ["adultos"]},
    {"id": "google_public", "provider": "Google Public DNS", "role": "reference", "ref": None, "ref_type": None,
     "url": "https://dns.google/dns-query"},
    {"id": "quad9_unfiltered", "provider": "Quad9", "role": "reference", "ref": None, "ref_type": None,
     "url": "https://dns10.quad9.net/dns-query"},
    {"id": "quad9_secure", "provider": "Quad9", "role": "security", "ref": "quad9_unfiltered", "ref_type": "intra_provider",
     "url": "https://dns.quad9.net/dns-query"},
    {"id": "adguard_unfiltered", "provider": "AdGuard DNS", "role": "reference", "ref": None, "ref_type": None,
     "url": "https://unfiltered.adguard-dns.com/dns-query"},
    {"id": "adguard_default", "provider": "AdGuard DNS", "role": "security", "ref": "adguard_unfiltered", "ref_type": "intra_provider",
     "url": "https://dns.adguard-dns.com/dns-query"},
    {"id": "adguard_family", "provider": "AdGuard DNS", "role": "parental", "ref": "adguard_unfiltered", "ref_type": "intra_provider",
     "url": "https://family.adguard-dns.com/dns-query", "declares": ["adultos"]},
    {"id": "cleanbrowsing_adult", "provider": "CleanBrowsing", "role": "parental", "ref": "cloudflare_standard", "ref_type": "external_reference",
     "url": "https://doh.cleanbrowsing.org/doh/adult-filter/", "declares": ["adultos"]},
    {"id": "cleanbrowsing_family", "provider": "CleanBrowsing", "role": "parental", "ref": "cloudflare_standard", "ref_type": "external_reference",
     "url": "https://doh.cleanbrowsing.org/doh/family-filter/", "declares": ["adultos"]},
    {"id": "controld_open", "provider": "Control D", "role": "reference", "ref": None, "ref_type": None,
     "url": "https://freedns.controld.com/p0"},
    {"id": "controld_family", "provider": "Control D", "role": "parental", "ref": "controld_open", "ref_type": "intra_provider",
     "url": "https://freedns.controld.com/family", "declares": ["adultos"]},
    {"id": "opendns_standard", "provider": "Cisco OpenDNS", "role": "reference", "ref": None, "ref_type": None,
     "url": "https://doh.opendns.com/dns-query"},
    {"id": "opendns_family", "provider": "Cisco OpenDNS", "role": "parental", "ref": "opendns_standard", "ref_type": "intra_provider",
     "url": "https://doh.familyshield.opendns.com/dns-query", "declares": ["adultos"]},
    {"id": "mullvad_open", "provider": "Mullvad DNS", "role": "reference", "ref": None, "ref_type": None,
     "url": "https://dns.mullvad.net/dns-query"},
    {"id": "mullvad_family", "provider": "Mullvad DNS", "role": "parental", "ref": "mullvad_open", "ref_type": "intra_provider",
     "url": "https://family.dns.mullvad.net/dns-query", "declares": ["adultos", "apuestas"]},
    {"id": "dns4eu_unfiltered", "provider": "DNS4EU", "role": "reference", "ref": None, "ref_type": None,
     "url": "https://unfiltered.joindns4.eu/dns-query"},
    {"id": "dns4eu_protective", "provider": "DNS4EU", "role": "security", "ref": "dns4eu_unfiltered", "ref_type": "intra_provider",
     "url": "https://protective.joindns4.eu/dns-query"},
    {"id": "dns4eu_child", "provider": "DNS4EU", "role": "parental", "ref": "dns4eu_unfiltered", "ref_type": "intra_provider",
     "url": "https://child.joindns4.eu/dns-query", "declares": ["adultos", "apuestas", "armas"]},
]


def is_valid_domain(d: str) -> bool:
    if not d or len(d) > 253 or "." not in d:
        return False
    try:
        ipaddress.ip_address(d)
        return False
    except ValueError:
        pass
    labels = d.split(".")
    if any(not lbl or len(lbl) > 63 or lbl.startswith("-") or lbl.endswith("-") or "_" in lbl for lbl in labels):
        return False
    if not re.fullmatch(r"[a-z0-9.-]+", d):
        return False
    if labels[-1].isdigit():
        return False
    return True


def build_benchmark_dataset() -> tuple[list[dict[str, str]], dict]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(domain: str, group: str, category: str, source: str) -> None:
        d = domain.strip().lower().rstrip(".")
        if not d or d in seen:
            return
        seen.add(d)
        rows.append({"domain": d, "group": group, "category": category, "source": source})

    # 1. 42 Subtel gambling
    d4 = json.loads((ROOT / "docs" / "evidencia" / "politica-dns4eu-2026-11-19.json").read_text())
    for dom in sorted({x["dominio"] for x in d4["detalle"] if x["categoria"] == "apuestas"}):
        add(dom, "apuestas_subtel", "apuestas", "Nómina oficial Subtel/SCJ (01-09-2026)")

    # 2. 22 EC + Ofcom adult
    for dom in sorted({x["dominio"] for x in d4["detalle"] if x["categoria"] == "adultos"}):
        add(dom, "adultos_reg", "adultos", "Comisión Europea DSA (27-05-2025)")
    with (ROOT / "dataset" / "referencia-adulto-ofcom-2026-11-19.csv").open() as f:
        for r in csv.DictReader(f):
            cat = r.get("category") or r.get("categories") or ""
            if "adulto" in cat:
                add(r["domain"], "adultos_reg", "adultos", "Ofcom AVS Group Final Decision (03-12-2025)")

    # 3. 13 verified firearms manufacturers
    for dom, src in WEAPONS_VERIFIED:
        add(dom, "armas_verif", "armas", src)

    # 4. 166 HTTPS-verified CRUCH/IPEDS educational portals
    pe = json.loads((ROOT / "docs" / "evidencia" / "portadas-educativas-2026-11-20.json").read_text())
    edu_verified = sorted(
        r["dominio"] for r in pe["resultados"]
        if r.get("estado") == "titulo_y_enlace_academico"
    )
    assert len(edu_verified) == 166, f"Expected 166 verified edu, got {len(edu_verified)}"
    for dom in edu_verified:
        add(dom, "educativo_verif", "educativo", "ROR x CRUCH/IPEDS con portada HTTPS verificada (20-11-2026)")

    # 5. Unbiased uniform A-Z random samples from complete official UT1 adult & StevenBlack gambling snapshots
    ut1_sha = hashlib.sha256(UT1_ADULT_TAR.read_bytes()).hexdigest()
    sb_sha = hashlib.sha256(SB_GAMBLING_HOSTS.read_bytes()).hexdigest()

    ut1_pool: set[str] = set()
    ut1_raw = 0
    with tarfile.open(UT1_ADULT_TAR, "r:gz") as tf:
        f = tf.extractfile("adult/domains")
        assert f is not None
        for line in f:
            ut1_raw += 1
            d = line.decode("utf-8", errors="ignore").strip().lower().rstrip(".")
            if is_valid_domain(d):
                ut1_pool.add(d)

    sb_pool: set[str] = set()
    sb_raw = 0
    for line in SB_GAMBLING_HOSTS.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
            sb_raw += 1
            d = parts[1].strip().lower().rstrip(".")
            if d not in ("localhost", "localhost.localdomain", "local", "0.0.0.0") and is_valid_domain(d):
                sb_pool.add(d)

    # Remove cross-category overlap & already included regulatory/verified domains
    overlap_ut1_sb = ut1_pool & sb_pool
    ut1_elig = sorted(ut1_pool - overlap_ut1_sb - seen)
    sb_elig = sorted(sb_pool - overlap_ut1_sb - seen)

    rng = random.Random(SEED)
    adult_sample = sorted(rng.sample(ut1_elig, N_CAND_ADULT))
    gambling_sample = sorted(rng.sample(sb_elig, N_CAND_GAMBLING))

    for dom in adult_sample:
        add(dom, "adultos_cand", "adultos", f"Muestra aleatoria uniforme A-Z UT1 adult/domains (semilla {SEED})")
    for dom in gambling_sample:
        add(dom, "apuestas_cand", "apuestas", f"Muestra aleatoria uniforme A-Z StevenBlack gambling (semilla {SEED})")

    # 6. 5 technical controls
    for dom, grp, src in CONTROLS:
        add(dom, grp, "control_tecnico", src)

    DATASET_OUT.parent.mkdir(parents=True, exist_ok=True)
    with DATASET_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["domain", "group", "category", "source"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    sampling_meta = {
        "seed": SEED,
        "ut1_adult": {
            "source_url": "https://dsi.ut-capitole.fr/blacklists/download/adult.tar.gz",
            "snapshot_date": "2026-11-26",
            "tar_sha256": ut1_sha,
            "raw_lines": ut1_raw,
            "valid_unique": len(ut1_pool),
            "eligible_after_exclusions": len(ut1_elig),
            "sampled": N_CAND_ADULT,
            "sample_distinct_first_chars": len({d[0] for d in adult_sample}),
            "sample_starts_with_digit": sum(1 for d in adult_sample if d[0].isdigit()),
        },
        "stevenblack_gambling": {
            "source_url": "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/gambling-only/hosts",
            "snapshot_date": "2026-11-26",
            "hosts_sha256": sb_sha,
            "raw_entries": sb_raw,
            "valid_unique": len(sb_pool),
            "eligible_after_exclusions": len(sb_elig),
            "sampled": N_CAND_GAMBLING,
            "sample_distinct_first_chars": len({d[0] for d in gambling_sample}),
            "sample_starts_with_digit": sum(1 for d in gambling_sample if d[0].isdigit()),
        },
        "cross_overlap_excluded": len(overlap_ut1_sb),
    }
    return rows, sampling_meta


def parse_dns_response(wire: bytes) -> dict:
    msg = dns.message.from_wire(wire)
    rcode = dns.rcode.to_text(msg.rcode())
    ips_a: list[str] = []
    ips_aaaa: list[str] = []
    cnames: list[str] = []
    ttls: list[int] = []
    for rrset in msg.answer:
        ttls.append(rrset.ttl)
        for rr in rrset:
            if rrset.rdtype == dns.rdatatype.A:
                ips_a.append(rr.to_text())
            elif rrset.rdtype == dns.rdatatype.AAAA:
                ips_aaaa.append(rr.to_text())
            elif rrset.rdtype == dns.rdatatype.CNAME:
                cnames.append(rr.to_text().rstrip("."))
    ede_codes: list[int] = []
    for opt in msg.options:
        if getattr(opt, "otype", None) == 15:
            code = getattr(opt, "code", None)
            if code is not None:
                ede_codes.append(int(code))
    return {
        "rcode": rcode,
        "ips_a": sorted(ips_a),
        "ips_aaaa": sorted(ips_aaaa),
        "cnames": sorted(cnames),
        "ede": sorted(set(ede_codes)),
        "ad": bool(msg.flags & dns.flags.AD),
        "ttl_min": min(ttls) if ttls else None,
    }


async def run_profile(profile: dict, items: list[dict[str, str]], concurrency: int = 4, delay: float = 0.02, use_http2: bool = True) -> tuple[list[dict], dict]:
    pid = profile["id"]
    url = profile["url"]
    records: list[dict] = []
    round_times: dict[int, dict[str, str]] = {}
    sem = asyncio.Semaphore(concurrency)

    async def send_with_h2_reconnect(client_box: list[httpx.AsyncClient], wire: bytes) -> httpx.Response:
        try:
            return await client_box[0].post(
                url,
                content=wire,
                headers={"content-type": "application/dns-message", "accept": "application/dns-message"},
            )
        except (httpx.RemoteProtocolError, httpx.LocalProtocolError, httpx.ReadError):
            async with httpx.AsyncClient(http2=use_http2, verify=True, timeout=8.0, follow_redirects=False) as fresh:
                return await fresh.post(
                    url,
                    content=wire,
                    headers={"content-type": "application/dns-message", "accept": "application/dns-message"},
                )

    limits = httpx.Limits(max_connections=max(6, concurrency * 2), max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(http2=use_http2, verify=True, timeout=8.0, limits=limits, follow_redirects=False) as client:
        client_box = [client]
        for rnd in range(1, ROUNDS + 1):
            t_start = dt.datetime.now(dt.timezone.utc).isoformat()
            rng = random.Random(SEED + rnd * 100 + sum(ord(c) for c in pid))
            order = list(items)
            rng.shuffle(order)

            async def query_one(it: dict[str, str], qtype: str) -> dict:
                async with sem:
                    q = dns.message.make_query(it["domain"], qtype, use_edns=True, want_dnssec=True)
                    wire = q.to_wire()
                    t0 = time.perf_counter()
                    ts = dt.datetime.now(dt.timezone.utc).isoformat()
                    try:
                        resp = await send_with_h2_reconnect(client_box, wire)
                        ms = round((time.perf_counter() - t0) * 1000, 1)
                        if resp.status_code == 200:
                            parsed = parse_dns_response(resp.content)
                            rec = {
                                "profile": pid, "domain": it["domain"], "group": it["group"],
                                "category": it["category"], "qtype": qtype, "round": rnd,
                                "ts_utc": ts, "http_status": resp.status_code, "http_version": resp.http_version,
                                "ms": ms, "error": None, **parsed,
                            }
                        else:
                            rec = {
                                "profile": pid, "domain": it["domain"], "group": it["group"],
                                "category": it["category"], "qtype": qtype, "round": rnd,
                                "ts_utc": ts, "http_status": resp.status_code, "http_version": resp.http_version,
                                "ms": ms, "error": f"HTTP_{resp.status_code}",
                                "rcode": None, "ips_a": [], "ips_aaaa": [], "cnames": [], "ede": [], "ad": False, "ttl_min": None,
                            }
                    except Exception as e:
                        ms = round((time.perf_counter() - t0) * 1000, 1)
                        rec = {
                            "profile": pid, "domain": it["domain"], "group": it["group"],
                            "category": it["category"], "qtype": qtype, "round": rnd,
                            "ts_utc": ts, "http_status": None, "http_version": None,
                            "ms": ms, "error": type(e).__name__,
                            "rcode": None, "ips_a": [], "ips_aaaa": [], "cnames": [], "ede": [], "ad": False, "ttl_min": None,
                        }
                    await asyncio.sleep(delay)
                    return rec

            tasks = [query_one(it, qt) for it in order for qt in QTYPES]
            batch = await asyncio.gather(*tasks)
            records.extend(batch)
            t_end = dt.datetime.now(dt.timezone.utc).isoformat()
            round_times[rnd] = {"start_utc": t_start, "end_utc": t_end}
            if rnd < ROUNDS:
                await asyncio.sleep(2.0)

    t1 = dt.datetime.fromisoformat(round_times[1]["start_utc"])
    t2 = dt.datetime.fromisoformat(round_times[2]["start_utc"])
    t1_end = dt.datetime.fromisoformat(round_times[1]["end_utc"])
    meta = {
        "round_times": round_times,
        "round1_duration_s": round((t1_end - t1).total_seconds(), 2),
        "inter_round_start_delta_s": round((t2 - t1).total_seconds(), 2),
        "inter_round_pause_s": round((t2 - t1_end).total_seconds(), 2),
        "errors": sum(1 for r in records if r["error"] is not None),
        "total_queries": len(records),
    }
    print(f"  [DONE] {pid:22s}: queries={meta['total_queries']} errors={meta['errors']} r1={meta['round1_duration_s']}s delta_r1_r2={meta['inter_round_start_delta_s']}s", flush=True)
    return records, meta


def classify_single(rec: dict, dns4eu_warn_v4: set[str], dns4eu_warn_v6: set[str]) -> str:
    if rec["error"] is not None:
        return "error_red"
    pid = rec["profile"]
    qt = rec["qtype"]
    ips = set(rec["ips_a"] if qt == "A" else rec["ips_aaaa"])
    ede_policy = bool(set(rec["ede"]) & {15, 16, 17})
    rcode = rec["rcode"]

    if ede_policy:
        return "bloqueo_senalizado"
    if ips & {"0.0.0.0", "::"}:
        if pid in ("cloudflare_family", "cloudflare_security", "adguard_family", "adguard_default", "controld_family"):
            return "bloqueo_senalizado"
    if pid in ("adguard_family", "adguard_default") and ("94.140.14.35" in ips or "::ffff:94.140.14.35" in ips):
        return "bloqueo_senalizado"
    if pid == "opendns_family" and (
        ips & {"146.112.61.106", "146.112.61.104", "146.112.61.105", "146.112.61.107", "146.112.61.108", "146.112.61.109", "146.112.61.110"}
        or any(ip.startswith("::ffff:146.112.61.") for ip in ips)
    ):
        return "bloqueo_senalizado"
    if pid in ("dns4eu_child", "dns4eu_protective") and ((qt == "A" and (ips & dns4eu_warn_v4)) or (qt == "AAAA" and (ips & dns4eu_warn_v6))):
        return "bloqueo_senalizado"

    if rcode == "NOERROR" and ips:
        if ips & {"0.0.0.0", "::", "127.0.0.1", "::1"}:
            return "anomalia"
        return "resolucion_observada"
    if rcode == "NXDOMAIN":
        return "nxdomain"
    if rcode == "NOERROR" and not ips:
        return "nodata"
    return "otro_error_dns"


def pairwise_stats(states_a: dict[str, str], states_b: dict[str, str], domains: list[str]) -> dict:
    c00 = c01 = c10 = c11 = 0
    for d in domains:
        sa = states_a.get(d)
        sb = states_b.get(d)
        if sa not in ("resolucion_observada", "bloqueo_senalizado") or sb not in ("resolucion_observada", "bloqueo_senalizado"):
            continue
        ba = 1 if sa == "bloqueo_senalizado" else 0
        bb = 1 if sb == "bloqueo_senalizado" else 0
        if ba == 0 and bb == 0:
            c00 += 1
        elif ba == 0 and bb == 1:
            c01 += 1
        elif ba == 1 and bb == 0:
            c10 += 1
        else:
            c11 += 1
    n = c00 + c01 + c10 + c11
    if n == 0:
        return {"n": 0, "c00": 0, "c01": 0, "c10": 0, "c11": 0, "agreement": None, "kappa": None, "jaccard": None}
    po = (c00 + c11) / n
    pa = (c10 + c11) / n
    pb = (c01 + c11) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    kappa = None if abs(1 - pe) < 1e-12 else round((po - pe) / (1 - pe), 4)
    union = c01 + c10 + c11
    jaccard = None if union == 0 else round(c11 / union, 4)
    return {
        "n": n, "c00": c00, "c01": c01, "c10": c10, "c11": c11,
        "agreement": round(po, 4), "kappa": kappa, "jaccard": jaccard,
        "rate_a": round(pa, 4), "rate_b": round(pb, 4),
    }


async def run_provider_group(profs: list[dict], items: list[dict[str, str]], sequential: bool, conc: int, delay: float) -> list[tuple[dict, list[dict], dict]]:
    out = []
    if sequential:
        for p in profs:
            recs, meta = await run_profile(p, items, concurrency=conc, delay=delay, use_http2=True)
            out.append((p, recs, meta))
    else:
        res = await asyncio.gather(*(run_profile(p, items, concurrency=conc, delay=delay, use_http2=True) for p in profs))
        for p, (recs, meta) in zip(profs, res):
            out.append((p, recs, meta))
    return out


async def main() -> None:
    t0_all = time.perf_counter()
    items, sampling_meta = build_benchmark_dataset()
    grp_counts = Counter(it["group"] for it in items)
    print(f"Benchmark dataset built: {len(items)} total names -> {dict(grp_counts)}", flush=True)
    print("Sampling meta:", json.dumps(sampling_meta, ensure_ascii=False), flush=True)

    # Group by provider so rate-limited operators (DNS4EU, Control D, CleanBrowsing) run gently sequentially
    # while distinct providers run concurrently.
    by_provider: dict[str, list[dict]] = defaultdict(list)
    for p in PROFILES:
        by_provider[p["provider"]].append(p)

    coros = []
    for prov, plist in by_provider.items():
        if prov == "DNS4EU":
            coros.append(run_provider_group(plist, items, sequential=True, conc=4, delay=0.015))
        elif prov in ("Control D", "CleanBrowsing"):
            coros.append(run_provider_group(plist, items, sequential=True, conc=2, delay=0.035))
        else:
            coros.append(run_provider_group(plist, items, sequential=False, conc=4, delay=0.02))

    grouped_results = await asyncio.gather(*coros)
    all_records: list[dict] = []
    profile_meta: dict[str, dict] = {}
    for batch in grouped_results:
        for p, recs, meta in batch:
            all_records.extend(recs)
            profile_meta[p["id"]] = meta

    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    with RAW_OUT.open("w") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    dns4eu_v4: set[str] = set()
    dns4eu_v6: set[str] = set()
    for r in all_records:
        if r["domain"] == "warning.joindns4.eu" and r["profile"].startswith("dns4eu_"):
            dns4eu_v4.update(r["ips_a"])
            dns4eu_v6.update(r["ips_aaaa"])
    print(f"DNS4EU calibrated warning IPs: v4={sorted(dns4eu_v4)} v6={sorted(dns4eu_v6)}")

    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in all_records:
        grouped[(r["profile"], r["qtype"], r["domain"])].append(r)

    raw_states: dict[tuple[str, str, str], list[str]] = {}
    for k, recs in grouped.items():
        recs_sorted = sorted(recs, key=lambda x: x["round"])
        raw_states[k] = [classify_single(x, dns4eu_v4, dns4eu_v6) for x in recs_sorted]

    prof_map = {p["id"]: p for p in PROFILES}

    def ref_resolves(pid: str, qt: str, dom: str) -> bool:
        ref_id = prof_map[pid]["ref"]
        if not ref_id:
            return False
        st = raw_states.get((ref_id, qt, dom), [])
        return len(st) == ROUNDS and all(s == "resolucion_observada" for s in st)

    domain_state: dict[tuple[str, str, str], str] = {}
    consistency_counts: dict[tuple[str, str], Counter] = defaultdict(Counter)

    nxdomain_blockers = {"cleanbrowsing_adult", "cleanbrowsing_family", "mullvad_family", "quad9_secure"}
    eval_items = [it for it in items if it["group"] != "control_tecnico"]
    eval_domains = [it["domain"] for it in eval_items]
    domain_group = {it["domain"]: it["group"] for it in items}
    domain_cat = {it["domain"]: it["category"] for it in items}

    for p in PROFILES:
        pid = p["id"]
        for qt in QTYPES:
            for dom in eval_domains:
                st_list = raw_states.get((pid, qt, dom), [])
                if len(st_list) != ROUNDS:
                    domain_state[(pid, qt, dom)] = "incompleto"
                    consistency_counts[(pid, qt)]["incompleto"] += 1
                    continue
                if any(s == "error_red" for s in st_list):
                    domain_state[(pid, qt, dom)] = "error_red"
                    consistency_counts[(pid, qt)]["error_red"] += 1
                    continue
                if st_list[0] != st_list[1]:
                    domain_state[(pid, qt, dom)] = "inconsistente"
                    consistency_counts[(pid, qt)]["inconsistente"] += 1
                    continue
                consistency_counts[(pid, qt)]["consistente"] += 1
                s = st_list[0]
                if s == "bloqueo_senalizado":
                    domain_state[(pid, qt, dom)] = "bloqueo_senalizado"
                elif s == "resolucion_observada":
                    domain_state[(pid, qt, dom)] = "resolucion_observada"
                elif s == "nxdomain":
                    if pid in nxdomain_blockers and ref_resolves(pid, qt, dom):
                        domain_state[(pid, qt, dom)] = "bloqueo_senalizado"
                    elif p["ref"] and ref_resolves(pid, qt, dom):
                        domain_state[(pid, qt, dom)] = "anomalia"
                    else:
                        domain_state[(pid, qt, dom)] = "indeterminado"
                else:
                    domain_state[(pid, qt, dom)] = "indeterminado"

    summary_by_group: dict[str, dict] = {}
    for p in PROFILES:
        pid = p["id"]
        summary_by_group[pid] = {}
        for qt in QTYPES:
            summary_by_group[pid][qt] = {}
            for grp in ("apuestas_subtel", "adultos_reg", "armas_verif", "educativo_verif", "adultos_cand", "apuestas_cand"):
                g_doms = [d for d in eval_domains if domain_group[d] == grp]
                c_all = Counter(domain_state[(pid, qt, d)] for d in g_doms)
                if p["ref"]:
                    comp_doms = [d for d in g_doms if ref_resolves(pid, qt, d)]
                    c_ref = Counter(domain_state[(pid, qt, d)] for d in comp_doms)
                else:
                    comp_doms = g_doms
                    c_ref = c_all
                summary_by_group[pid][qt][grp] = {
                    "n_total": len(g_doms),
                    "states_all": dict(c_all),
                    "n_ref_comparable": len(comp_doms),
                    "states_ref_comparable": dict(c_ref),
                }

    parental_ids = [p["id"] for p in PROFILES if p["role"] == "parental"]
    live_a = [d for d in eval_domains if domain_state[("cloudflare_standard", "A", d)] == "resolucion_observada"]
    live_aaaa = [d for d in eval_domains if domain_state[("cloudflare_standard", "AAAA", d)] == "resolucion_observada"]
    pairwise_a: dict[str, list[dict]] = {}
    slices = {
        "all_eval": live_a,
        "adultos_all": [d for d in live_a if domain_cat[d] == "adultos"],
        "adultos_reg": [d for d in live_a if domain_group[d] == "adultos_reg"],
        "adultos_cand": [d for d in live_a if domain_group[d] == "adultos_cand"],
        "apuestas_all": [d for d in live_a if domain_cat[d] == "apuestas"],
        "apuestas_subtel": [d for d in live_a if domain_group[d] == "apuestas_subtel"],
        "apuestas_cand": [d for d in live_a if domain_group[d] == "apuestas_cand"],
        "armas_verif": [d for d in live_a if domain_group[d] == "armas_verif"],
        "educativo_verif": [d for d in live_a if domain_group[d] == "educativo_verif"],
    }
    for sname, sdoms in slices.items():
        rows_pw = []
        for i, pa in enumerate(parental_ids):
            sa = {d: domain_state[(pa, "A", d)] for d in sdoms}
            for pb in parental_ids[i + 1:]:
                sb = {d: domain_state[(pb, "A", d)] for d in sdoms}
                rows_pw.append({"a": pa, "b": pb, **pairwise_stats(sa, sb, sdoms)})
        pairwise_a[sname] = rows_pw

    discrepancies: dict[str, list[dict]] = defaultdict(list)
    edu_false_positives: list[dict] = []
    for d in live_a:
        grp = domain_group[d]
        cat = domain_cat[d]
        blocked_by = [pid for pid in parental_ids if domain_state[(pid, "A", d)] == "bloqueo_senalizado"]
        allowed_by = [pid for pid in parental_ids if domain_state[(pid, "A", d)] == "resolucion_observada"]
        if grp == "educativo_verif" and blocked_by:
            edu_false_positives.append({"domain": d, "blocked_by": blocked_by, "allowed_by": allowed_by})
        decl_profiles = [p["id"] for p in PROFILES if p["role"] == "parental" and cat in p.get("declares", [])]
        if len(decl_profiles) >= 2:
            d_blk = [pid for pid in decl_profiles if domain_state[(pid, "A", d)] == "bloqueo_senalizado"]
            d_all = [pid for pid in decl_profiles if domain_state[(pid, "A", d)] == "resolucion_observada"]
            if d_blk and d_all:
                discrepancies[grp].append({
                    "domain": d, "blocked_by_declaring": d_blk, "allowed_by_declaring": d_all,
                    "n_blocked": len(d_blk), "n_allowed": len(d_all),
                })

    consistency_summary = {}
    for p in PROFILES:
        pid = p["id"]
        consistency_summary[pid] = {}
        for qt in QTYPES:
            cc = consistency_counts[(pid, qt)]
            tot_no_err = cc["consistente"] + cc["inconsistente"]
            consistency_summary[pid][qt] = {
                "consistente": cc["consistente"],
                "inconsistente": cc["inconsistente"],
                "error_red": cc["error_red"],
                "rate_over_completed": round(cc["consistente"] / tot_no_err, 4) if tot_no_err else None,
                "rate_over_all": round(cc["consistente"] / len(eval_domains), 4),
            }

    controls_summary: dict[str, dict] = {}
    for dom, _, _ in CONTROLS:
        controls_summary[dom] = {}
        for p in PROFILES:
            pid = p["id"]
            controls_summary[dom][pid] = {qt: raw_states.get((pid, qt, dom), []) for qt in QTYPES}

    dataset_sha = hashlib.sha256(DATASET_OUT.read_bytes()).hexdigest()
    raw_sha = hashlib.sha256(RAW_OUT.read_bytes()).hexdigest()
    evidence = {
        "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "seed": SEED,
        "rounds": ROUNDS,
        "qtypes": list(QTYPES),
        "dataset_path": "dataset/benchmark-pdns-2026-11-26.csv",
        "dataset_sha256": dataset_sha,
        "raw_sha256": raw_sha,
        "sampling_meta": sampling_meta,
        "profile_references": {p["id"]: {"ref": p["ref"], "ref_type": p["ref_type"]} for p in PROFILES},
        "total_domains_including_controls": len(items),
        "eval_domains_count": len(eval_domains),
        "live_in_cloudflare_standard_A": len(live_a),
        "live_in_cloudflare_standard_AAAA": len(live_aaaa),
        "live_by_group_cf_std_A": dict(Counter(domain_group[d] for d in live_a)),
        "live_by_group_cf_std_AAAA": dict(Counter(domain_group[d] for d in live_aaaa)),
        "group_counts": dict(grp_counts),
        "dns4eu_warning_ips": {"A": sorted(dns4eu_v4), "AAAA": sorted(dns4eu_v6)},
        "profile_meta": profile_meta,
        "consistency_summary": consistency_summary,
        "summary_by_group": summary_by_group,
        "pairwise_A": pairwise_a,
        "discrepancies_among_declaring_profiles_A": {
            k: {"count": len(v), "examples": v[:40]} for k, v in discrepancies.items()
        },
        "educational_false_positives_A": edu_false_positives,
        "controls_summary": controls_summary,
        "elapsed_total_s": round(time.perf_counter() - t0_all, 1),
    }
    EVIDENCE_OUT.write_text(json.dumps(evidence, indent=2, ensure_ascii=False))
    print(f"\n=== UNBIASED A-Z BENCHMARK COMPLETE in {evidence['elapsed_total_s']}s ===", flush=True)
    print(f"Total queries: {len(all_records)}, Total errors: {sum(m['errors'] for m in profile_meta.values())}")
    print(f"Live in CF Standard A: {len(live_a)} / {len(eval_domains)} -> {evidence['live_by_group_cf_std_A']}")
    print(f"Live in CF Standard AAAA: {len(live_aaaa)} / {len(eval_domains)} -> {evidence['live_by_group_cf_std_AAAA']}")
    print("Educational false positives:", len(edu_false_positives), edu_false_positives[:5])
    for grp, info in evidence["discrepancies_among_declaring_profiles_A"].items():
        print(f"Discrepancies in {grp}: {info['count']} domains! Sample:", [x["domain"] for x in info["examples"][:8]])


if __name__ == "__main__":
    asyncio.run(main())
