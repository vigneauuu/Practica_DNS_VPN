# Comparación de perfiles DNS, VPN y proxy

El 18 de noviembre de 2026 se amplió la medición inicial de dos perfiles Cloudflare a **14 perfiles TCP de siete proveedores**. Los 50 dominios del piloto se mantuvieron para comparar el mismo conjunto. Son 39 sitios educativos o de investigación, cuatro de contenido adulto, cuatro de apuestas y tres de armas con documentación preliminar. Las categorías siguen pendientes de validación final. El conjunto candidato de 2.000 dominios se mantiene separado.

## DNS público

Los endpoints, referencias y fuentes del proveedor se conservan en [la configuración TCP](../config/ampliacion-dns-2026-11-18.json). Se midieron A y AAAA, tres rondas, espera máxima de 2,5 s, intervalo de 0,09 s y cero reintentos. El orden del corpus se fija con la semilla 20261118. Las ejecuciones de perfiles se guardan en bases independientes y corren con un máximo de siete procesos. Nueve perfiles reciben controles DNS antes y después de cada consulta objetivo. Los perfiles de CleanBrowsing comparten una referencia de otro proveedor. Esa diferencia limita la atribución de resultados discordantes.

| Ejecución | Consultas | Alcance |
|---|---:|---|
| TCP/53 | 9.600 | 4.200 observaciones objetivo y 5.400 controles temporales |
| Calibración TCP inicial | 112 | Cuatro nombres técnicos por perfil, A y AAAA |
| Contraste adicional Cisco | 8 | Nombre permitido y control de adulto en OpenDNS estándar y FamilyShield |
| DoH con TLS verificado | 608 | Ocho perfiles de cuatro proveedores, dos rondas y 19 nombres, A y AAAA |
| DoH de Mullvad sobre HTTP/2 | 152 | Dos perfiles públicos, mismos 19 nombres, dos rondas, A y AAAA |
| DNS en laboratorio OpenVPN | 72 | Tres condiciones, cuatro nombres sintéticos, A/AAAA y tres rondas |
| HTTP en laboratorio de proxy | 36 | Tres condiciones, cuatro casos sintéticos y tres rondas |

El contraste DoH incluye los 11 candidatos de adulto, apuestas y armas, los cuatro primeros educativos por orden alfabético y cuatro controles técnicos. Recibió 608 respuestas. Usa mensajes DNS por HTTPS, verifica TLS, y reporta códigos, direcciones y EDE directamente. No aplica los controles temporales de TCP. Tampoco compara exactamente el mismo conjunto, número de rondas ni ventana temporal, por lo que no aísla el efecto del transporte.

En los 91 pares por tipo hubo de 45 a 50 dominios estables y comparables en A y de 10 a 14 en AAAA. La cobertura forma parte de la interpretación del acuerdo. Entre los dominios con etiqueta documental de adulto se observaron EDE de política, direcciones coherentes con bloqueo documentado y respuestas NXDOMAIN. Las gráficas conservan la regla común y el [resumen](evidencia/ampliacion-2026-11-18.json) incluye los patrones de respuesta para una lectura por proveedor.

- AdGuard familiar devolvió en A la dirección que identifica su equipo de mantenimiento como página de bloqueo. [Caso oficial 5028](https://github.com/AdguardTeam/AdGuardHome/issues/5028).
- Control D familiar devolvió direcciones especiales coherentes con su [documentación de respuestas de bloqueo](https://docs.controld.com/docs/blocked-query-response).
- CleanBrowsing devolvió NXDOMAIN, forma de respuesta descrita en su [guía de comprobación](https://cleanbrowsing.org/learn/verify-dns-configuration). Los controles positivos de A dan más evidencia que los AAAA sin dirección.
- OpenDNS FamilyShield devolvió las direcciones que Cisco identifica para su página de bloqueo por categoría. También se observaron en el control `exampleadultsite.com`, a diferencia del perfil estándar. [Direcciones de bloqueo](https://www.cisco.com/c/en/us/support/docs/security/umbrella/224799-learn-the-umbrella-block-page-ip.html) y [destinos de prueba](https://www.cisco.com/c/en/us/support/docs/security/umbrella/224911-understand-umbrella-test-destinations.pdf).

## VPN y proxy

En OpenVPN se usaron dos espacios de red aislados, certificados efímeros, un enlace virtual y un resolutor local. Se verificó la ruta por `tun0`. Tanto el enlace directo como el túnel con la regla desactivada resolvieron los 24 casos. Al configurar el filtro se observaron 18 señales de bloqueo en adulto, apuestas y armas y seis resoluciones del control educativo. En el proxy HTTP se remitió a un origen local. Con la regla desactivada respondieron 12 casos HTTP 200, igual que en la conexión directa. Al activarla se observaron nueve 403 con una huella explícita de política y tres respuestas 200. Las unidades DNS y HTTP se reportan en paneles distintos. Son configuraciones controladas con casos sintéticos. La [prueba externa de Cloudflare WARP](warp-2026-11-18.md) midió por separado el túnel y el modo proxy del cliente. La comparación entre operadores externos independientes sigue pendiente.

El [DNS público de Mullvad](https://mullvad.net/en/help/dns-over-https-and-dns-over-tls) se probó por separado, sin activar su VPN. El perfil familiar devolvió NXDOMAIN en las ocho consultas por tipo de cada categoría documental, adulto y apuestas. El perfil sin filtro devolvió direcciones en los ocho casos de A de cada categoría. En AAAA devolvió direcciones en dos consultas de adulto y ninguna de apuestas. Una primera corrida por HTTP/1.1 no obtuvo mensajes DNS. La corrida por HTTP/2 sí recibió las 152 respuestas y es la que se resume en `doh_mullvad`. Los registros de ambas corridas se conservan por separado.

Para extender las pruebas por conexión, [Windscribe](https://windscribe.com/features/robert) documenta categorías que dependen del plan. El [SOCKS5 de Mullvad](https://mullvad.net/en/help/socks5-proxy) requiere conectarse a su VPN. En ambos casos falta habilitar el servicio y comprobar ruta, resolutor y política en el cliente real.

## Reproducción

Activar `.venv` desde la raíz del repositorio. Los experimentos públicos consultan únicamente DNS. Para la VPN de laboratorio se requiere Linux con disponibilidad de TUN, iproute2, OpenSSL, OpenVPN, dnsmasq y privilegios locales para crear espacios de red. El script abre interfaces temporales aisladas y las retira al finalizar. Para regenerar las figuras se instala Matplotlib junto con las dependencias de desarrollo.

```bash
work=results/nueva-ampliacion
python scripts/medir_ampliacion_dns.py "$work"
python scripts/contrastar_doh.py "$work/doh.json"
python scripts/contrastar_doh.py --mullvad "$work/doh-mullvad.json"
bash scripts/comparar_vpn_local.sh "$work/vpn-verificada"
python scripts/comparar_proxy_local.py "$work/proxy.json"
python scripts/resumir_ampliacion.py "$work" "$work/resumen.json" --mullvad "$work/doh-mullvad.json"
python scripts/graficar_ampliacion.py "$work/resumen.json" "$work/figuras"
```

El resumen registra identificadores, huellas y denominadores. Las bases con las respuestas completas se quedan en almacenamiento local. Los resultados de octubre conservan sus identificadores y su interpretación histórica. El informe contiene conclusiones para lo medido y trabajo futuro para la validación del corpus, cobertura de apuestas y armas, VPN y proxies externos y repetición en otras redes.
