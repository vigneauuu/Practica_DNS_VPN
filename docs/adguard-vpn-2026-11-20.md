# Contraste con AdGuard VPN en modo túnel y proxy SOCKS5

El 19 y 20 de noviembre de 2026 se evaluó AdGuard VPN para Linux como segunda VPN externa con opción de filtrado DNS familiar. La prueba comprobó si el cambio entre el perfil sin filtro y el perfil familiar de AdGuard DNS se reproducía dentro del túnel de AdGuard VPN sobre una ubicación fija, y qué ocurría al consultar controles HTTPS por su modo proxy SOCKS5. [AdGuard VPN para Linux](https://adguard-vpn.com/en/linux/overview.html) · [Configuración TUN y SOCKS5](https://adguard-vpn.com/kb/adguard-vpn-for-linux/settings/) · [Perfiles públicos de AdGuard DNS](https://adguard-dns.io/en/public-dns.html)

## Referencia por DoH y consultas DNS en el túnel

Se utilizaron los 25 nombres de la selección común de rutas externas (cuatro de contenido adulto, cuatro de apuestas del piloto, seis de apuestas de la nómina de Subtel, tres fabricantes de armas, cuatro portales educativos y cuatro controles técnicos), sin incluir el dominio de aviso propio de DNS4EU. En cada condición se consultaron los registros A y AAAA en dos rondas, 100 consultas por condición.

Primero se obtuvo una referencia directa por DoH sobre HTTP/2 con verificación TLS desde Chile (`wlan0`) contra los perfiles sin filtro (`unfiltered.adguard-dns.com`) y familiar (`family.adguard-dns.com`) de AdGuard DNS, entre las 21:50 y las 21:51 de Santiago del 19 de noviembre (200 respuestas de 200 consultas).

A continuación se ejecutó la imagen oficial `adguard/adguardvpn-cli:latest` (`sha256:577d338aa698b5e5aa53fec11d7749560a0355c2c11440b75db861c9e2b7e188`, `AdGuard VPN CLI v1.7.12`) en un contenedor descartable en Linux con red puente propia, capacidad `NET_ADMIN`, dispositivo `/dev/net/tun` y sin montajes del equipo anfitrión. Se utilizó el plan gratuito y la ubicación fija `Dallas`, en modo `TUN`, con enrutamiento automático (`auto`), cambio de DNS activado y tráfico IPv4 (`--ipv4only`). El cliente guardó la configuración DNS del túnel (`46.243.231.30`) en `/root/.local/share/adguardvpn-cli/resolv.conf`, que se aplicó a `/etc/resolv.conf` dentro del contenedor al no poder actualizarlo automáticamente. Se alternó el servidor ascendente configurado en el cliente entre `94.140.14.140` (sin filtro) y `94.140.14.15` (familiar), manteniendo la misma ubicación.

Entre las 01:17 y las 01:19 de Santiago del 20 de noviembre se ejecutaron las dos condiciones dentro del túnel. Antes y después de cada ronda se verificó que la ruta tanto hacia el resolutor del contenedor (`46.243.231.30`) como hacia el diagnóstico HTTPS (`104.16.123.96`) utilizaba la interfaz `tun0`. La salida pública se mantuvo en la misma dirección de Estados Unidos en ambas condiciones del túnel y fue distinta de la salida chilena de referencia. Se recibieron 199 respuestas UDP de 200 consultas; el único fallo fue una espera agotada en la primera ronda de una consulta A de armas (`smith-wesson.com`) con el filtro desactivado.

| Grupo | Consultas A por condición | DoH sin filtro | DoH familiar | Túnel sin filtro | Túnel familiar |
|---|---:|---|---|---|---|
| Adulto | 8 | 8 ordinarias | 8 con aviso | 8 ordinarias | 8 con aviso |
| Apuestas (piloto y Subtel) | 20 | 20 ordinarias | 20 ordinarias | 20 ordinarias | 20 ordinarias |
| Armas | 6 | 6 ordinarias | 6 ordinarias | 5 ordinarias, 1 error | 6 ordinarias |
| Educativos | 8 | 8 ordinarias | 8 ordinarias | 8 ordinarias | 8 ordinarias |

En la tabla, «con aviso» corresponde a la dirección IPv4 de la página de bloqueo documentada por AdGuard (`94.140.14.35`). En AAAA, los cuatro dominios de adulto devolvieron EDE 17 (`Filtered`) en las dos rondas tanto en DoH familiar como en túnel familiar (8/8 en ambos casos), frente a dos respuestas con dirección y seis `NOERROR` sin dirección en las condiciones sin filtro. Los diez dominios de apuestas y los tres de armas resolvieron con direcciones ordinarias en A con el filtro familiar, lo que concuerda con la política pública del perfil familiar de AdGuard (que declara bloquear contenido adulto, publicidad y rastreadores, no apuestas ni armas). Los cuatro portales educativos devolvieron direcciones A ordinarias en las cuatro condiciones. En los controles técnicos, `example.com`, `nudity.testcategory.com` y `malware.testcategory.com` resolvieron en las cuatro condiciones (los dos controles de categoría pertenecen a Cloudflare y aquí comprueban resolución, no la política de AdGuard) y `no-existe-pdns-lab.invalid` devolvió `NXDOMAIN` en A y AAAA. [Señal de AdGuard](https://github.com/AdguardTeam/AdGuardHome/issues/5028)

## Solicitudes HTTPS por el proxy SOCKS5

Tras desconectar el túnel, el mismo cliente se configuró en modo `SOCKS` escuchando en `127.0.0.1:19080` con la misma ubicación `Dallas`. Según la documentación oficial de AdGuard VPN para Linux, la opción de DNS del modo `TUN` no se aplica en el modo `SOCKS`. Entre las 01:26 y las 01:27 de Santiago del 20 de noviembre se realizaron 16 solicitudes HTTPS HEAD con curl 8.23.0, validación TLS y sin redirecciones: cuatro controles técnicos, dos rutas (directa y `socks5h://127.0.0.1:19080`) y dos rondas. Antes y después de cada ronda se comprobó la salida pública: Chile por ruta directa y Estados Unidos por el proxy, con direcciones distintas en las cuatro comprobaciones.

| Control | Directa | Proxy SOCKS5 de AdGuard VPN |
|---|---|---|
| `example.com` | 2 HTTP 200 | 2 HTTP 200 |
| `nudity.testcategory.com` | 2 HTTP 200 | 2 HTTP 200 |
| `malware.testcategory.com` | 2 HTTP 200 | 2 HTTP 200 |
| `no-existe-pdns-lab.invalid` | 2 sin HTTP, curl 6 | 2 sin HTTP, curl 97 |

Al igual que en WARP y Tor, los tres controles con nombre válido devolvieron HTTP 200 por ambas rutas y `no-existe-pdns-lab.invalid` falló antes de recibir una respuesta HTTP (`curl 6` al resolver localmente por ruta directa y `curl 97` en el canal SOCKS5). Al finalizar se eliminó el contenedor descartable y los archivos temporales de autenticación. [Totales y comprobaciones](evidencia/adguard-vpn-2026-11-20.json)

## Repetición y verificación

1. Ejecutar primero la referencia directa por DoH desde la raíz del repositorio en un directorio de salida nuevo:

```bash
mkdir -p results/repeticion-adguard
python scripts/comparar_adguard_vpn.py referencia_doh results/repeticion-adguard/referencia-sin-filtro.json --policy sin_filtro
python scripts/comparar_adguard_vpn.py referencia_doh results/repeticion-adguard/referencia-familiar.json --policy familiar
```

2. En un contenedor descartable basado en `adguard/adguardvpn-cli:latest` con `--device /dev/net/tun` y `--cap-add NET_ADMIN` (sin puertos publicados ni montajes del usuario), iniciar sesión con una cuenta de AdGuard, fijar la ubicación y alternar `config set-dns 94.140.14.140` y `config set-dns 94.140.14.15` en modo `TUN`. Si el contenedor no actualiza `/etc/resolv.conf`, aplicar `/root/.local/share/adguardvpn-cli/resolv.conf` dentro del contenedor y ejecutar `scripts/comparar_adguard_vpn.py tun` dentro de su espacio de red indicando el resolutor y la interfaz `tun0`.
3. Desconectar el túnel, pasar a modo `SOCKS` en `127.0.0.1:19080` sobre la misma ubicación y ejecutar `scripts/comparar_adguard_vpn.py socks` dentro del espacio de red del contenedor.
4. Resumir las cinco fases y verificar el agregado (que conserva los SHA-256 de los archivos crudos y omite las direcciones IP públicas de salida):

```bash
python scripts/comparar_adguard_vpn.py resumir /tmp/resumen-adguard.json --datos results/repeticion-adguard
```
