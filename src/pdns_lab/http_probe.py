"""Prueba HTTP opcional: un 403 o timeout no prueba filtrado del proxy."""
import hashlib
import time
from urllib.parse import urlsplit
import httpx
from .dnsprobe import utcnow


def probe_http(url, *, proxy=None, fingerprints=(), timeout=10, byte_limit=65536):
    if urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).hostname:
        raise ValueError("Se requiere una URL HTTP(S)")
    started = time.monotonic()
    result = {"time": utcnow(), "url": url, "proxy_used": bool(proxy), "redirects_followed": False}
    if proxy:
        endpoint = urlsplit(proxy)
        result["proxy_endpoint"] = {"scheme": endpoint.scheme, "host": endpoint.hostname, "port": endpoint.port}
    try:
        # Sin cookies, proxy del entorno ni ejecución de contenido. TLS se verifica.
        with httpx.Client(proxy=proxy, timeout=timeout, trust_env=False, follow_redirects=False) as client:
            with client.stream("GET", url, headers={"User-Agent": "PDNS-Lab/0.2 research"}) as response:
                body = bytearray()
                for chunk in response.iter_bytes(chunk_size=4096):
                    body.extend(chunk[:max(0, byte_limit-len(body))])
                    if len(body) >= byte_limit:
                        break
                text = bytes(body).decode("utf-8", errors="replace")
                matches = [s for s in fingerprints if s["text"] in text]
                result.update({"http_status": response.status_code, "bytes_examined": len(body),
                               "body_prefix_sha256": hashlib.sha256(body).hexdigest(),
                               "content_type": response.headers.get("content-type"),
                               "status": "bloqueo_senalizado" if matches else "respuesta_http_observada",
                               "matched_fingerprints": matches})
    except httpx.HTTPError as exc:
        result.update({"status": "error_http", "error": type(exc).__name__})
    result["elapsed_ms"] = round((time.monotonic()-started)*1000, 3)
    return result
