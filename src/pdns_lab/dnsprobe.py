"""Consultas DNS explícitas con conservación de mensajes y errores."""
import base64
import ipaddress
import time
from datetime import datetime, timezone
import dns.edns
import dns.exception
import dns.flags
import dns.message
import dns.query
import dns.rcode
import dns.rdatatype

BLOCK_EDE = {15, 16, 17, 18}


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def summarize_response(response):
    sections = {}
    addresses, cnames = [], []
    for section in ("answer", "authority", "additional"):
        sections[section] = []
        for rrset in getattr(response, section):
            values = [rr.to_text() for rr in rrset]
            sections[section].append({"name": str(rrset.name), "type": dns.rdatatype.to_text(rrset.rdtype), "ttl": rrset.ttl, "values": values})
            if section == "answer" and rrset.rdtype in (dns.rdatatype.A, dns.rdatatype.AAAA):
                addresses.extend(values)
            if section == "answer" and rrset.rdtype == dns.rdatatype.CNAME:
                cnames.extend(v.rstrip(".") for v in values)
    ede = [{"code": int(o.code), "text": o.text or ""} for o in response.options if isinstance(o, dns.edns.EDEOption)]
    return {"rcode": dns.rcode.to_text(response.rcode()), "flags": dns.flags.to_text(response.flags),
            "addresses": sorted(set(addresses)), "cnames": cnames, "ede": ede, **sections,
            "wire_base64": base64.b64encode(response.to_wire()).decode("ascii"), "text": response.to_text()}


def probe(domain, qtype, endpoint, *, timeout=3, retries=1, interval=0.2, source=None, transport="udp"):
    attempts = []
    for attempt in range(retries + 1):
        request = dns.message.make_query(domain, qtype, use_edns=0, want_dnssec=True)
        started = time.monotonic()
        result = {"time": utcnow(), "attempt": attempt + 1, "endpoint": endpoint,
                  "query_flags": dns.flags.to_text(request.flags), "dnssec_do_requested": True,
                  "query_wire_base64": base64.b64encode(request.to_wire()).decode("ascii")}
        try:
            if transport == "tcp":
                response = dns.query.tcp(request, endpoint, timeout=timeout, source=source)
                used_tcp = True
            else:
                response, used_tcp = dns.query.udp_with_fallback(request, endpoint, timeout=timeout, source=source)
            result.update(summarize_response(response))
            result.update({"error": None, "transport": "tcp" if used_tcp else "udp"})
        except (dns.exception.DNSException, OSError) as exc:
            result.update({"error": type(exc).__name__, "error_detail": str(exc), "rcode": None,
                           "addresses": [], "cnames": [], "ede": [], "transport": transport})
        result["elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
        attempts.append(result)
        # Una respuesta DNS negativa es evidencia; no se elimina reintentando hasta obtener éxito.
        if not result["error"]:
            time.sleep(interval)
            break
        time.sleep(interval * (attempt + 1))
    return {"attempts": attempts, "final": attempts[-1]}


def classify(target, before, after, profile):
    """La señal de política es evidencia declarada; no una categoría de contenido."""
    if target.get("error"):
        return "error_red", target["error"]
    if any(e["code"] in BLOCK_EDE for e in target.get("ede", [])):
        return "bloqueo_senalizado", "ede_politica"
    fingerprints = profile.get("fingerprint_ips", [])
    if profile.get("fingerprint_source") and set(target.get("addresses", [])) & set(fingerprints):
        return "bloqueo_senalizado", "ip_sumidero_documentada"
    addresses = target.get("addresses", [])
    if any(ipaddress.ip_address(ip).is_loopback or ipaddress.ip_address(ip).is_unspecified for ip in addresses):
        return "anomalia", "direccion_especial_sin_huella_documentada"
    if target.get("rcode") == "NOERROR" and addresses:
        # Direcciones diferentes a los controles pueden ser CDN; no prueban alteración.
        return "resolucion_observada", "respuesta_con_direcciones"
    controls = (before, after)
    controls_resolve = all(r and not r.get("error") and r.get("rcode") == "NOERROR" and r.get("addresses") for r in controls)
    if controls_resolve:
        return "anomalia", "respuesta_negativa_con_controles_positivos"
    return "indeterminado", "sin_senal_de_politica_o_controles_concluyentes"
