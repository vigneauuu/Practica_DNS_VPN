#!/usr/bin/env bash
# Laboratorio aislado: dos espacios de red unidos por un enlace y un túnel TLS.
set -euo pipefail
umask 077
if [[ "$#" != 1 ]]; then
    echo "Uso: $0 DIRECTORIO_NUEVO_DE_RESULTADOS" >&2
    exit 2
fi
mkdir -- "$1"
out=$(realpath -- "$1")
for name in server.log client.log dnsmasq.log dnsmasq-filtro.log directa.json vpn_sin_filtro.json vpn_con_filtro.json; do
    touch "$out/$name"
done
python=$(realpath -s -- "$(dirname -- "$0")/../.venv/bin/python")
tmp=$(mktemp -d)
server="pdns-s-$$"
client="pdns-c-$$"
link_server="ps$$"
link_client="pc$$"

cleanup() {
    for namespace in "$client" "$server"; do
        while read -r pid; do
            [[ -z "$pid" ]] || sudo -n kill "$pid" 2>/dev/null || true
        done < <(sudo -n ip netns pids "$namespace" 2>/dev/null || true)
        sudo -n ip netns del "$namespace" 2>/dev/null || true
    done
    sudo -n ip link del "$link_server" 2>/dev/null || true
    rm -rf -- "$tmp"
}
trap cleanup EXIT
sudo -n true
sudo -n ip netns add "$server"
sudo -n ip netns add "$client"
sudo -n ip link add "$link_server" type veth peer name "$link_client"
sudo -n ip link set "$link_server" netns "$server"
sudo -n ip link set "$link_client" netns "$client"
server_run() { sudo -n ip netns exec "$server" "$@"; }
client_run() { sudo -n ip netns exec "$client" "$@"; }
server_run ip link set lo up
client_run ip link set lo up
server_run ip addr add 172.30.254.1/30 dev "$link_server"
client_run ip addr add 172.30.254.2/30 dev "$link_client"
server_run ip link set "$link_server" up
client_run ip link set "$link_client" up

# Certificados efímeros, generados localmente y eliminados al terminar.
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=pdns-local-ca -keyout "$tmp/ca.key" -out "$tmp/ca.pem" 2>"$out/openssl.log"
for role in server client; do
    openssl req -new -newkey rsa:2048 -nodes -subj "/CN=pdns-local-$role" -keyout "$tmp/$role.key" -out "$tmp/$role.csr" 2>>"$out/openssl.log"
    printf 'extendedKeyUsage=%sAuth\nkeyUsage=digitalSignature,keyEncipherment\n' "$role" > "$tmp/$role.ext"
    openssl x509 -req -in "$tmp/$role.csr" -CA "$tmp/ca.pem" -CAkey "$tmp/ca.key" -CAcreateserial -days 1 -extfile "$tmp/$role.ext" -out "$tmp/$role.pem" 2>>"$out/openssl.log"
done
openvpn --version > "$out/openvpn-version.txt"
common=(--disable-dco --dev tun0 --proto udp --ca "$tmp/ca.pem" --data-ciphers AES-256-GCM --tls-version-min 1.2 --verb 3)
server_run openvpn "${common[@]}" --mode server --tls-server --dh none --server 10.203.77.0 255.255.255.0 --topology subnet --local 172.30.254.1 --port 27818 --cert "$tmp/server.pem" --key "$tmp/server.key" --remote-cert-tls client --daemon --log "$out/server.log"
client_run openvpn "${common[@]}" --client --nobind --remote 172.30.254.1 27818 --remote-cert-tls server --verify-x509-name pdns-local-server name --cert "$tmp/client.pem" --key "$tmp/client.key" --daemon --log "$out/client.log"
for _ in {1..50}; do
    if rg -q 'Initialization Sequence Completed' "$out/client.log"; then break; fi
    sleep .2
done
rg -q 'Initialization Sequence Completed' "$out/client.log"
client_run ip -j route get 10.203.77.1 > "$out/ruta-vpn.json"
client_run ip -j route get 172.30.254.1 > "$out/ruta-directa.json"
server_run dnsmasq --conf-file=/dev/null --no-resolv --no-hosts --bind-interfaces --listen-address=172.30.254.1 --listen-address=10.203.77.1 --local=/pdns.test/ --address=/pdns.test/192.0.2.10 --address=/pdns.test/2001:db8::10 --pid-file="$tmp/dns.pid" --log-facility="$out/dnsmasq.log"

measure() {
    client_run "$python" - "$1" "$2" <<'PY'
from itertools import product
from pathlib import Path
import json
import sys
from pdns_lab.dnsprobe import probe, classify

mode, path = sys.argv[1:]
endpoint = "172.30.254.1" if mode == "directa" else "10.203.77.1"
profile = {"fingerprint_ips": ["0.0.0.0", "::"], "fingerprint_source": "Regla local explícita de dnsmasq"}
rows = []
for round_number, category, qtype in product(range(1, 4), ["educativo", "adulto", "apuestas", "armas"], ["A", "AAAA"]):
    name = f"{category}.pdns.test"
    evidence = probe(name, qtype, endpoint, transport="tcp", retries=0, timeout=1.5, interval=0.03)
    status, reason = classify(evidence["final"], None, None, profile)
    expected = "bloqueo_senalizado" if mode == "vpn_con_filtro" and category != "educativo" else "resolucion_observada"
    rows.append(dict(mode=mode, category=category, qtype=qtype, round=round_number, expected=expected, status=status, reason=reason, evidence=evidence))
Path(path).write_text(json.dumps(rows, indent=2) + "\n")
if any(row["status"] != row["expected"] for row in rows):
    raise SystemExit(f"Resultados distintos de lo esperado en {mode}; revisar {path}")
PY
}
measure directa "$out/directa.json"
measure vpn_sin_filtro "$out/vpn_sin_filtro.json"
sudo -n kill "$(cat "$tmp/dns.pid")"
server_run dnsmasq --conf-file=/dev/null --no-resolv --no-hosts --bind-interfaces --listen-address=10.203.77.1 --local=/pdns.test/ --address=/pdns.test/192.0.2.10 --address=/pdns.test/2001:db8::10 --address=/adulto.pdns.test/apuestas.pdns.test/armas.pdns.test/# --pid-file="$tmp/dns-filtro.pid" --log-facility="$out/dnsmasq-filtro.log"
measure vpn_con_filtro "$out/vpn_con_filtro.json"
