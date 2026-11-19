# Comparación con RiseupVPN y un proxy SOCKS5 de Tor

El 19 de noviembre de 2026 se repitió una selección de consultas por ruta directa y con un túnel externo de RiseupVPN. Se hicieron también solicitudes HTTPS por ruta directa y por el proxy SOCKS5 de Tor. Las dos pruebas permiten comprobar si cambiar el transporte cambia el resultado para una configuración y un grupo de controles determinados. [RiseupVPN](https://riseup.net/en/vpn) · [Especificación SOCKS de Tor](https://spec.torproject.org/socks-extensions.html)

## Consultas DNS por ruta directa y por VPN

Para ambas rutas se mantuvieron los mismos perfiles de DNS4EU, los mismos dominios, los tipos A y AAAA y dos rondas. El perfil infantil declara filtrado parental para contenido adulto, apuestas y armas. El perfil sin filtro de contenido se usó como referencia. Se añadió el resolutor interno de Riseup para comprobar cómo respondía la configuración entregada por el túnel. Los metadatos de Riseup para el servidor elegido indicaban `filter_dns=false`. [Perfiles públicos de DNS4EU](https://joindns4.eu/for-public) · [Política de DNS4EU](https://legal-documents-dns4eu.s3.fr-par.scw.cloud/DNS4EU-Public-DNS-Resolver-policy-2025.pdf) · [Metadatos de Riseup](https://api.black.riseup.net/3/config/eip-service.json)

Se consultaron 26 nombres. Se repitieron los 19 nombres de la [comparación de WARP](warp-2026-11-18.md), se añadieron seis de apuestas que coinciden con nombres de la nómina de Subtel y se usó `warning.joindns4.eu` para comprobar las direcciones de aviso. En total se incluyeron cuatro nombres de contenido adulto, diez de apuestas, tres de fabricantes de armas, cuatro educativos y cinco controles técnicos. La clasificación documental se conserva en los archivos de origen. [Muestra inicial](../dataset/piloto-50-2026-10-30.csv) · [Nombres de apuestas de la nómina](../dataset/doh-apuestas-subtel-2026-11-18.csv)

Se estableció el túnel con OpenVPN 2.7.9 por UDP/1194, cifrado AES-256-GCM y el servidor `vpn02-par.riseup.net`, que publicó el proveedor para París. El cliente usó certificado de acceso anónimo, verificó la CA publicada mediante el SHA-256 del descriptor oficial y comprobó el nombre `vpn02-par` del certificado de servidor. Cada ruta se ejecutó en un espacio de red separado en Linux. Antes y después de cada ronda se verificó la interfaz para los destinos y la salida pública mediante un diagnóstico HTTPS. En la ruta directa la interfaz fue `eth0` y la salida se identificó en Chile. En Riseup la interfaz fue `tun0`, con otra salida identificada en Francia, y el resolutor interno anunciado fue `10.42.0.1`. Se consultó ese resolutor de forma explícita. [Descriptor oficial de Riseup](https://black.riseup.net/provider.json) · [Manual de OpenVPN](https://openvpn.net/community-docs/community-articles/openvpn-2-6-manual/)

Entre las 20:11 y las 20:13 de Santiago se recibieron 520 respuestas válidas. DNS4EU respondió 416 consultas mediante HTTPS sobre HTTP/2 con validación TLS. El resolutor de Riseup respondió 104 consultas UDP. Cada columna incluye dos rondas por tipo, por lo que hay dos consultas A por nombre y dos AAAA. La tabla muestra únicamente A.

| Grupo | Consultas A por configuración | Directa sin filtro | Directa infantil | Riseup sin filtro | Riseup infantil | DNS de Riseup |
|---|---:|---|---|---|---|---|
| Adulto | 8 | 8 ordinarias | 8 con aviso | 8 ordinarias | 8 con aviso | 8 ordinarias |
| Apuestas | 20 | 20 ordinarias | 20 con aviso | 20 ordinarias | 20 con aviso | 20 ordinarias |
| Armas | 6 | 6 ordinarias | 6 con aviso | 6 ordinarias | 6 con aviso | 6 ordinarias |
| Educativos | 8 | 8 ordinarias | 8 ordinarias | 8 ordinarias | 8 ordinarias | 8 ordinarias |

«Con aviso» indica que el perfil devolvió únicamente la dirección de `warning.joindns4.eu` para ese tipo. Las direcciones comprobadas en ambas rutas fueron `51.15.69.11` (A) y `2001:bc8:1640:3ffd:dc00:ff:fe4a:3ec9` (AAAA). Los 17 nombres de adulto, apuestas y armas presentaron el aviso con el perfil infantil también en AAAA. En A los 17 recibieron direcciones ordinarias con el DNS nativo de Riseup. En el grupo educativo, cuatro respuestas AAAA por configuración fueron NOERROR sin dirección.

Se emparejaron por nombre, tipo y ronda las respuestas a los 21 sitios, dejando fuera los controles. En cada perfil DNS4EU los 84 pares conservaron el mismo estado de respuesta al cambiar de ruta. El conjunto exacto de direcciones coincidió en 84 de 84 pares con el perfil infantil y en 80 de 84 con el perfil sin filtro. Las cuatro diferencias de este último correspondieron a direcciones A de apuestas. El resultado describe el filtro configurado de DNS4EU y las rutas de esta sesión. Las respuestas DNS por sí solas no indican si se podía cargar una página. [Totales y comprobaciones por ruta](evidencia/riseup-2026-11-19.json)

## Solicitudes HTTPS por ruta directa y por Tor

En un espacio de red aislado se levantó Tor 0.4.9.17 en modo cliente con un proxy local que recibió nombres mediante SOCKS5. Se utilizó `socks5h` en curl 8.23.0 para entregar el nombre al proxy. Se conservaron los mismos cuatro controles técnicos de WARP. Las solicitudes fueron HEAD, con verificación TLS y sin seguir redirecciones. El diagnóstico oficial devolvió `IsTor=false` por ruta directa y `IsTor=true` por el proxy antes y después de cada ronda. [Diagnóstico de Tor](https://check.torproject.org/api/ip) · [Resolución remota mediante SOCKS](https://support.torproject.org/little-t-tor/troubleshooting/check-for-leaks/)

| Control | Directa | Proxy Tor |
|---|---|---|
| `example.com` | 2 HTTP 200 | 2 HTTP 200 |
| `nudity.testcategory.com` | 2 HTTP 200 | 2 HTTP 200 |
| `malware.testcategory.com` | 2 HTTP 200 | 2 HTTP 200 |
| `no-existe-pdns-lab.invalid` | 2 sin HTTP, curl 6 | 2 sin HTTP, curl 97 |

Las 16 solicitudes se realizaron a las 20:13 de Santiago. El código 6 indica que el cliente no pudo resolver el nombre y el 97 indica un error de SOCKS antes de obtener respuesta HTTP. Los dos sitios de prueba de categorías provienen de Cloudflare y se usaron como controles reproducibles de acceso HTTPS. El proxy Tor se usó como referencia de transporte, sin una política parental en la prueba. Los resultados no se comparan como medidas de eficacia de filtrado. [Totales del proxy](evidencia/tor-proxy-2026-11-19.json)

## Repetición

1. Preparar dos espacios de red dedicados con salida a Internet. Mantener la ruta directa en uno. En el otro, obtener los metadatos oficiales de Riseup y usar un cliente OpenVPN con la CA verificada y el certificado anónimo vigente. Al repetir, confirmar el servidor, certificado, protocolo y resolutor anunciados. No incluir la clave del cliente en los resultados.
2. Ejecutar `scripts/comparar_rutas_dns.py` desde la raíz del repositorio en cada espacio de red. Los argumentos de interfaz y resolutor indican la configuración observada. Ajustarlos si cambian en otra sesión. Los nombres DoH conservan validación de certificado aunque se indique una dirección IPv4 publicada mediante curl.
3. En el espacio de red directo, iniciar Tor en modo cliente con `SocksPort 127.0.0.1:19050`, `SafeSocks 1` y `TestSocks 1`. Confirmar que completó su inicio. Ejecutar la comparación de proxy en ese mismo espacio.
4. Conservar los archivos originales de cada sesión y ejecutar los resúmenes desde la raíz del repositorio. Los agregados contienen los SHA-256 de los registros y omiten las IP públicas de salida del cliente.

```bash
python scripts/comparar_rutas_dns.py medir directa eth0 results/directa.json
python scripts/comparar_rutas_dns.py medir riseup tun0 results/riseup.json --riseup-dns 10.42.0.1
python scripts/comparar_proxy_tor.py --port 19050 results/tor.json
python scripts/comparar_rutas_dns.py resumir results/directa.json results/riseup.json /tmp/resumen-rutas.json
python scripts/comparar_proxy_tor.py --tor-version 0.4.9.17 --summarize results/tor.json /tmp/resumen-tor.json
```
