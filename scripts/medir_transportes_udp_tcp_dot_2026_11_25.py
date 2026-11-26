#!/usr/bin/env python3
"""Experimento pareado de 4 transportes DNS: UDP/53 vs. TCP/53 (mismo timeout 2,5 s), DoH y DoT/853.

Responde empíricamente dos preguntas directas del estudio:
1. Paridad de disponibilidad y filtrado entre UDP/53 y TCP/53 con idéntico tiempo de espera (2,5 s)
   registrando bandera TC (truncamiento) y timeouts.
2. Existencia y paridad de servicios PDNS sobre DNS-over-TLS (DoT, puerto 853, RFC 7858) frente a DoH y TCP/53.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import socket
import time
from collections import Counter, defaultdict
from pathlib import Path

import dns.flags
import dns.message
import dns.query
import dns.rcode
import dns.rdatatype
import httpx

ROOT = Path(__file__).resolve().parent.parent
RAW_OUT = ROOT / "results" / "transportes-2026-11-25" / "raw.json"
EVIDENCE_OUT = ROOT / "docs" / "evidencia" / "transportes-udp-tcp-doh-dot-2026-11-25.json"

TIMEOUT_PORT53 = 2.5
TIMEOUT_TLS = 3.5
ROUNDS = 2
QTYPES = ("A", "AAAA")

DOMAINS = [
    # 6 adulto regulatorio (4 UE + 2 Ofcom)
    ("pornhub.com", "adultos"),
    ("xvideos.com", "adultos"),
    ("xnxx.com", "adultos"),
    ("stripchat.com", "adultos"),
    ("adultwork.com", "adultos"),
    ("vivastreet.co.uk", "adultos"),
    # 6 apuestas Subtel (incluye las 2 omisiones previas de DNS4EU)
    ("betano.com", "apuestas"),
    ("coolbet.com", "apuestas"),
    ("jugabet.cl", "apuestas"),
    ("rojabet.cl", "apuestas"),
    ("latamwinonline.com", "apuestas"),
    ("www.nayafacil-903.com", "apuestas"),
    # 4 armas oficiales
    ("ruger.com", "armas"),
    ("sigsauer.com", "armas"),
    ("smith-wesson.com", "armas"),
    ("glock.com", "armas"),
    # 4 educativos verificados (2 CRUCH + 2 IPEDS)
    ("uchile.cl", "educativo"),
    ("uc.cl", "educativo"),
    ("mit.edu", "educativo"),
    ("stanford.edu", "educativo"),
    # 4 controles técnicos
    ("example.com", "control_tecnico"),
    ("no-existe-pdns-lab.invalid", "control_tecnico"),
    ("nudity.testcategory.com", "control_tecnico"),
    ("malware.testcategory.com", "control_tecnico"),
]

PROVIDERS = [
    {"id": "cloudflare_standard", "ip53": "1.1.1.1", "dot_ip": "1.1.1.1", "dot_host": "one.one.one.one",
     "doh_url": "https://cloudflare-dns.com/dns-query"},
    {"id": "cloudflare_family", "ip53": "1.1.1.3", "dot_ip": "1.1.1.3", "dot_host": "family.cloudflare-dns.com",
     "doh_url": "https://family.cloudflare-dns.com/dns-query"},
    {"id": "google_public", "ip53": "8.8.8.8", "dot_ip": "8.8.8.8", "dot_host": "dns.google",
     "doh_url": "https://dns.google/dns-query"},
    {"id": "quad9_unfiltered", "ip53": "9.9.9.10", "dot_ip": "9.9.9.10", "dot_host": "dns10.quad9.net",
     "doh_url": "https://dns10.quad9.net/dns-query"},
    {"id": "quad9_secure", "ip53": "9.9.9.9", "dot_ip": "9.9.9.9", "dot_host": "dns.quad9.net",
     "doh_url": "https://dns.quad9.net/dns-query"},
    {"id": "adguard_unfiltered", "ip53": "94.140.14.140", "dot_ip": "94.140.14.140", "dot_host": "unfiltered.adguard-dns.com",
     "doh_url": "https://unfiltered.adguard-dns.com/dns-query"},
    {"id": "adguard_family", "ip53": "94.140.14.15", "dot_ip": "94.140.14.15", "dot_host": "family.adguard-dns.com",
     "doh_url": "https://family.adguard-dns.com/dns-query"},
    {"id": "cleanbrowsing_family", "ip53": "185.228.168.168", "dot_ip": "185.228.168.168", "dot_host": "family-filter-dns.cleanbrowsing.org",
     "doh_url": "https://doh.cleanbrowsing.org/doh/family-filter/"},
    {"id": "controld_family", "ip53": "76.76.2.4", "dot_ip": None, "dot_host": "family.freedns.controld.com",
     "doh_url": "https://freedns.controld.com/family"},
    {"id": "opendns_family", "ip53": "208.67.222.123", "dot_ip": None, "dot_host": None,
     "doh_url": "https://doh.familyshield.opendns.com/dns-query"},
    {"id": "mullvad_family", "ip53": None, "dot_ip": "194.242.2.6", "dot_host": "family.dns.mullvad.net",
     "doh_url": "https://family.dns.mullvad.net/dns-query"},
    {"id": "dns4eu_child", "ip53": None, "dot_ip": "86.54.11.12", "dot_host": "child.joindns4.eu",
     "doh_url": "https://child.joindns4.eu/dns-query"},
]


def parse_msg(msg: dns.message.Message) -> dict:
    ips_a, ips_aaaa = [], []
    for rrset in msg.answer:
        for rr in rrset:
            if rrset.rdtype == dns.rdatatype.A:
                ips_a.append(rr.to_text())
            elif rrset.rdtype == dns.rdatatype.AAAA:
                ips_aaaa.append(rr.to_text())
    ede = sorted({int(opt.code) for opt in msg.options if getattr(opt, "otype", None) == 15 and getattr(opt, "code", None) is not None})
    return {
        "rcode": dns.rcode.to_text(msg.rcode()),
        "tc": bool(msg.flags & dns.flags.TC),
        "ips_a": sorted(ips_a),
        "ips_aaaa": sorted(ips_aaaa),
        "ede": ede,
    }


def classify_norm(pid: str, qt: str, rec: dict) -> str:
    if rec["error"] is not None:
        return "error"
    ips = set(rec["ips_a"] if qt == "A" else rec["ips_aaaa"])
    if set(rec["ede"]) & {15, 16, 17}:
        return "bloqueo"
    if ips & {"0.0.0.0", "::"} and pid in ("cloudflare_family", "adguard_family", "controld_family"):
        return "bloqueo"
    if pid == "adguard_family" and ("94.140.14.35" in ips or "::ffff:94.140.14.35" in ips):
        return "bloqueo"
    if pid == "opendns_family" and (any(ip.startswith("146.112.61.") or ip.startswith("::ffff:146.112.61.") for ip in ips)):
        return "bloqueo"
    if pid == "dns4eu_child" and ("51.15.69.11" in ips or any(ip.startswith("2001:bc8:") or ip == "51.15.69.11" for ip in ips)):
        return "bloqueo"
    if rec["rcode"] == "NXDOMAIN":
        return "nxdomain"
    if rec["rcode"] == "NOERROR" and ips:
        return "resolucion"
    if rec["rcode"] == "NOERROR" and not ips:
        return "nodata"
    return f"rcode_{rec['rcode']}"


def main() -> None:
    t0_all = time.perf_counter()
    # Resolve Control D DoT IP dynamically
    for p in PROVIDERS:
        if p["id"] == "controld_family" and p["dot_host"]:
            try:
                p["dot_ip"] = socket.gethostbyname(p["dot_host"])
            except Exception:
                p["dot_ip"] = None

    # Check DNS4EU warning IPv6 via DoH
    warn_v6 = set()
    with httpx.Client(http2=True, timeout=5.0) as c:
        q = dns.message.make_query("warning.joindns4.eu", "AAAA", use_edns=True)
        r = dns.message.from_wire(c.post("https://child.joindns4.eu/dns-query", content=q.to_wire(),
                                         headers={"content-type": "application/dns-message"}).content)
        for rrset in r.answer:
            if rrset.rdtype == dns.rdatatype.AAAA:
                for rr in rrset:
                    warn_v6.add(rr.to_text())

    # OpenDNS DoT availability check (port 853)
    opendns_dot_check = {}
    for host in ("doh.familyshield.opendns.com", "208.67.222.123"):
        try:
            ip = host if host[0].isdigit() else socket.gethostbyname(host)
            q = dns.message.make_query("example.com", "A", use_edns=True)
            dns.query.tls(q, ip, server_hostname="dns.opendns.com", timeout=2.5)
            opendns_dot_check[host] = "OK"
        except Exception as e:
            opendns_dot_check[host] = type(e).__name__

    records: list[dict] = []
    # Quick UDP/53 reachability check per profile (10 queries: 4 controls + 6 adult on A) to avoid wasting 120s on hard-dropped UDP
    # Wait: let's run FULL 2 rounds on A for UDP/53 on ALL 10 port-53 profiles if fast, OR test first 6 domains (adult+controls) across all 10 profiles
    # Actually 10 profiles x 24 domains x 1 round x 2.5s timeout if dropped would take 600s sequentially — let's use ThreadPoolExecutor across profiles!
    from concurrent.futures import ThreadPoolExecutor

    def run_port53_paired(p: dict) -> list[dict]:
        pid = p["id"]
        ip = p["ip53"]
        if not ip:
            return []
        out = []
        # Run 10 paired domains (4 EC adult + 2 Subtel + 2 edu + 2 controls) x 2 rounds x A & AAAA = 40 UDP + 40 TCP per profile!
        # Even if all 40 UDP time out at 2.5s, with 10 profiles in parallel it's max 100s — or with 1 round for dropped profiles?
        # Even better: run ALL 24 domains on TCP/53 (2 rounds, A & AAAA = 96 queries, takes ~3s),
        # and run paired UDP/53 at IDENTICAL 2.5s timeout on 12 domains (4 EC adult + 2 Subtel + 2 armas + 2 edu + 2 controls) x 2 rounds x A = 24 queries (max 60s in parallel, 1s when UDP works)!
        udp_subset = [
            "pornhub.com", "xvideos.com", "xnxx.com", "stripchat.com",
            "betano.com", "coolbet.com", "ruger.com", "sigsauer.com",
            "uchile.cl", "mit.edu", "example.com", "no-existe-pdns-lab.invalid",
        ]
        for rnd in range(1, ROUNDS + 1):
            for dom, cat in DOMAINS:
                for qt in QTYPES:
                    q = dns.message.make_query(dom, qt, use_edns=True, want_dnssec=True)
                    # TCP/53
                    t0 = time.perf_counter()
                    try:
                        r = dns.query.tcp(q, ip, timeout=TIMEOUT_PORT53)
                        out.append({"profile": pid, "transport": "tcp53", "domain": dom, "category": cat,
                                    "qtype": qt, "round": rnd, "ms": round((time.perf_counter()-t0)*1000, 1),
                                    "error": None, **parse_msg(r)})
                    except Exception as e:
                        out.append({"profile": pid, "transport": "tcp53", "domain": dom, "category": cat,
                                    "qtype": qt, "round": rnd, "ms": round((time.perf_counter()-t0)*1000, 1),
                                    "error": type(e).__name__, "rcode": None, "tc": False, "ips_a": [], "ips_aaaa": [], "ede": []})
                    # Paired UDP/53 right after on the 12-domain subset (A only so worst-case parallel wall clock <= 60s)
                    if qt == "A" and dom in udp_subset:
                        t0 = time.perf_counter()
                        try:
                            r = dns.query.udp(q, ip, timeout=TIMEOUT_PORT53)
                            out.append({"profile": pid, "transport": "udp53", "domain": dom, "category": cat,
                                        "qtype": qt, "round": rnd, "ms": round((time.perf_counter()-t0)*1000, 1),
                                        "error": None, **parse_msg(r)})
                        except Exception as e:
                            out.append({"profile": pid, "transport": "udp53", "domain": dom, "category": cat,
                                        "qtype": qt, "round": rnd, "ms": round((time.perf_counter()-t0)*1000, 1),
                                        "error": type(e).__name__, "rcode": None, "tc": False, "ips_a": [], "ips_aaaa": [], "ede": []})
        print(f"  [PORT53 DONE] {pid}", flush=True)
        return out

    def run_dot_and_doh(p: dict) -> list[dict]:
        pid = p["id"]
        out = []
        with httpx.Client(http2=True, verify=True, timeout=TIMEOUT_TLS, follow_redirects=False) as client:
            for rnd in range(1, ROUNDS + 1):
                for dom, cat in DOMAINS:
                    for qt in QTYPES:
                        q = dns.message.make_query(dom, qt, use_edns=True, want_dnssec=True)
                        # DoH
                        t0 = time.perf_counter()
                        try:
                            resp = client.post(p["doh_url"], content=q.to_wire(),
                                               headers={"content-type": "application/dns-message", "accept": "application/dns-message"})
                            if resp.status_code == 200:
                                out.append({"profile": pid, "transport": "doh", "domain": dom, "category": cat,
                                            "qtype": qt, "round": rnd, "ms": round((time.perf_counter()-t0)*1000, 1),
                                            "error": None, **parse_msg(dns.message.from_wire(resp.content))})
                            else:
                                out.append({"profile": pid, "transport": "doh", "domain": dom, "category": cat,
                                            "qtype": qt, "round": rnd, "ms": round((time.perf_counter()-t0)*1000, 1),
                                            "error": f"HTTP_{resp.status_code}", "rcode": None, "tc": False, "ips_a": [], "ips_aaaa": [], "ede": []})
                        except Exception as e:
                            out.append({"profile": pid, "transport": "doh", "domain": dom, "category": cat,
                                        "qtype": qt, "round": rnd, "ms": round((time.perf_counter()-t0)*1000, 1),
                                        "error": type(e).__name__, "rcode": None, "tc": False, "ips_a": [], "ips_aaaa": [], "ede": []})
                        # DoT/853
                        if p["dot_ip"] and p["dot_host"]:
                            t0 = time.perf_counter()
                            try:
                                r = dns.query.tls(q, p["dot_ip"], server_hostname=p["dot_host"], timeout=TIMEOUT_TLS)
                                out.append({"profile": pid, "transport": "dot853", "domain": dom, "category": cat,
                                            "qtype": qt, "round": rnd, "ms": round((time.perf_counter()-t0)*1000, 1),
                                            "error": None, **parse_msg(r)})
                            except Exception as e:
                                out.append({"profile": pid, "transport": "dot853", "domain": dom, "category": cat,
                                            "qtype": qt, "round": rnd, "ms": round((time.perf_counter()-t0)*1000, 1),
                                            "error": type(e).__name__, "rcode": None, "tc": False, "ips_a": [], "ips_aaaa": [], "ede": []})
        print(f"  [DOH/DOT DONE] {pid}", flush=True)
        return out

    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = [ex.submit(run_port53_paired, p) for p in PROVIDERS] + [ex.submit(run_dot_and_doh, p) for p in PROVIDERS]
        for fut in futs:
            records.extend(fut.result())

    # Normalize DNS4EU IPv6 warning check
    for r in records:
        if r["profile"] == "dns4eu_child" and r["qtype"] == "AAAA" and (set(r["ips_aaaa"]) & warn_v6):
            r["norm_state"] = "bloqueo"
        else:
            r["norm_state"] = classify_norm(r["profile"], r["qtype"], r)

    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    RAW_OUT.write_text(json.dumps(records, indent=2, ensure_ascii=False))

    # Summarize availability & parity across transports
    avail = defaultdict(lambda: defaultdict(lambda: {"ok": 0, "err": 0, "tc_true": 0, "ms_median": None}))
    ms_vals = defaultdict(list)
    for r in records:
        k = (r["profile"], r["transport"])
        if r["error"] is None:
            avail[r["profile"]][r["transport"]]["ok"] += 1
            if r["tc"]:
                avail[r["profile"]][r["transport"]]["tc_true"] += 1
            ms_vals[k].append(r["ms"])
        else:
            avail[r["profile"]][r["transport"]]["err"] += 1
    for (pid, tr), vals in ms_vals.items():
        if vals:
            avail[pid][tr]["ms_median"] = round(sorted(vals)[len(vals)//2], 1)

    # Parity checks: for every (profile, domain, qtype, round), compare norm_state across transports where both succeeded!
    by_key = defaultdict(dict)
    for r in records:
        by_key[(r["profile"], r["domain"], r["qtype"], r["round"])][r["transport"]] = r["norm_state"]

    parity = defaultdict(lambda: {"compared": 0, "matched": 0, "mismatches": []})
    pairs = [("udp53", "tcp53"), ("tcp53", "doh"), ("tcp53", "dot853"), ("doh", "dot853")]
    for (pid, dom, qt, rnd), tmap in by_key.items():
        for t1, t2 in pairs:
            if t1 in tmap and t2 in tmap and tmap[t1] != "error" and tmap[t2] != "error":
                pk = f"{t1}_vs_{t2}"
                parity[pk]["compared"] += 1
                if tmap[t1] == tmap[t2]:
                    parity[pk]["matched"] += 1
                else:
                    parity[pk]["mismatches"].append({"profile": pid, "domain": dom, "qtype": qt, "round": rnd, t1: tmap[t1], t2: tmap[t2]})

    # Adult/Gambling/Weapons blocking summary in DoT/853 specifically (A)
    dot_cat_summary = defaultdict(lambda: defaultdict(Counter))
    for r in records:
        if r["transport"] == "dot853" and r["qtype"] == "A":
            dot_cat_summary[r["profile"]][r["category"]][r["norm_state"]] += 1

    evidence = {
        "fecha_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "timeout_port53_s": TIMEOUT_PORT53,
        "timeout_tls_s": TIMEOUT_TLS,
        "rounds": ROUNDS,
        "domains_count": len(DOMAINS),
        "raw_sha256": hashlib.sha256(RAW_OUT.read_bytes()).hexdigest(),
        "opendns_dot_probe": opendns_dot_check,
        "availability_by_profile_transport": {pid: dict(tmap) for pid, tmap in avail.items()},
        "transport_parity": {k: {"compared": v["compared"], "matched": v["matched"], "mismatch_count": len(v["mismatches"]), "mismatches": v["mismatches"][:15]} for k, v in parity.items()},
        "dot853_category_A": {pid: {cat: dict(c) for cat, c in cmap.items()} for pid, cmap in dot_cat_summary.items()},
        "elapsed_total_s": round(time.perf_counter() - t0_all, 1),
    }
    EVIDENCE_OUT.write_text(json.dumps(evidence, indent=2, ensure_ascii=False))
    print(f"\n=== 4-TRANSPORT EXPERIMENT COMPLETE in {evidence['elapsed_total_s']}s ===", flush=True)
    for pid, tmap in evidence["availability_by_profile_transport"].items():
        line = "  " + f"{pid:22s}: " + " | ".join(f"{t}={v['ok']}/{v['ok']+v['err']}({v['ms_median']}ms)" for t, v in sorted(tmap.items()))
        print(line)
    print("PARITY:", {k: f"{v['matched']}/{v['compared']} (mismatches={v['mismatch_count']})" for k, v in evidence["transport_parity"].items()})


if __name__ == "__main__":
    main()
