"""Compara un origen HTTP local con dos reglas de un proxy de laboratorio."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import argparse
import http.client
import json

from pdns_lab.http_probe import probe_http

CASES = {"educativo": False, "adulto": True, "apuestas": True, "armas": True}
FINGERPRINT = {
    "text": "PDNS_LAB_REGLA_DE_CATEGORIA",
    "source": "Regla explícita del proxy local de laboratorio",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class Origin(Handler):
    def do_GET(self):
        category = self.path.removeprefix("/")
        if category not in CASES:
            return self.reply(404, b"Caso desconocido")
        self.reply(200, f"Control sintetico {category}".encode())


def proxy_handler(origin_port, filtering):
    class Proxy(Handler):
        def do_GET(self):
            target = urlsplit(self.path)
            origin = f"127.0.0.1:{origin_port}"
            category = target.path.removeprefix("/")
            if target.scheme != "http" or target.netloc != origin or category not in CASES:
                return self.reply(400, b"El proxy solo admite el origen local del experimento")
            if filtering and CASES[category]:
                return self.reply(403, FINGERPRINT["text"].encode())
            connection = http.client.HTTPConnection("127.0.0.1", origin_port, timeout=2)
            try:
                connection.request("GET", target.path)
                response = connection.getresponse()
                self.reply(response.status, response.read(1024))
            finally:
                connection.close()
    return Proxy


@contextmanager
def serve(handler):
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server, ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(server.serve_forever)
        try:
            yield server.server_port
        finally:
            server.shutdown()
            running.result()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output
    with serve(Origin) as origin, serve(proxy_handler(origin, False)) as open_proxy, serve(proxy_handler(origin, True)) as filtered_proxy:
        rows = []
        for mode, port in (("directa", None), ("proxy_sin_filtro", open_proxy), ("proxy_con_filtro", filtered_proxy)):
            for run in range(1, 4):
                for category, restricted in CASES.items():
                    result = probe_http(
                        f"http://127.0.0.1:{origin}/{category}",
                        proxy=f"http://127.0.0.1:{port}" if port else None,
                        fingerprints=[FINGERPRINT],
                        timeout=3,
                    )
                    expected = 403 if mode == "proxy_con_filtro" and restricted else 200
                    expected_state = "bloqueo_senalizado" if expected == 403 else "respuesta_http_observada"
                    rows.append(dict(mode=mode, category=category, round=run, expected_http=expected,
                                     expected_state=expected_state, result=result))
    with output.open("x", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    if any(row["result"].get("http_status") != row["expected_http"] or row["result"]["status"] != row["expected_state"] for row in rows):
        raise SystemExit("Las respuestas no coincidieron con la política de laboratorio")
    print(f"{len(rows)} respuestas coinciden con la política de laboratorio")


if __name__ == "__main__":
    main()
