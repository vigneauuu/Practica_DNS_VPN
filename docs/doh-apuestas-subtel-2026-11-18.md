# Respuestas DNS de seis candidatos de apuestas de la nómina de Subtel

El 18 de noviembre de 2026, entre las 23:00:41 y las 23:01:00 de Santiago, se iniciaron 112 consultas DNS sobre HTTPS a dos direcciones de servicio publicadas por Mullvad. Se probó si el perfil familiar devolvía la misma respuesta que el perfil sin filtro para seis nombres de apuestas. Son los seis nombres de los 400 candidatos que coincidieron exactamente con la nómina de Subtel. Ninguno formó parte de los cuatro casos de apuestas del piloto de octubre. La comparación se hizo por nombre de servidor, incluida la URL de la nómina que contiene la ruta `/cl`. El DNS no distingue rutas web. [Cotejo con la nómina](evidencia/contraste-apuestas-subtel-2026-11-18.json)

## Método y resultados

Se reutilizaron los cuatro primeros nombres educativos del piloto por orden alfabético y los cuatro controles técnicos de la medición anterior. Cada uno de los 14 nombres se consultó por registros A y AAAA en dos rondas, en los dos perfiles a la vez, con 0,08 segundos de pausa después de cada consulta por perfil. Las 112 solicitudes devolvieron un mensaje DNS válido mediante HTTP/2 con verificación TLS. El cliente usó las URL de los resolutores y solo les envió mensajes DNS. [Nombres consultados](../dataset/doh-apuestas-subtel-2026-11-18.csv) · [Recuentos por nombre, tipo y perfil](evidencia/doh-apuestas-subtel-2026-11-18.json)

| Grupo y tipo | Consultas por perfil | Sin filtro | Familiar |
|---|---:|---|---|
| Apuestas, A | 12 | 12 con dirección | 12 NXDOMAIN |
| Apuestas, AAAA | 12 | 6 con dirección, 6 NOERROR sin AAAA | 12 NXDOMAIN |
| Educativo, A | 8 | 8 con dirección | 8 con dirección |
| Educativo, AAAA | 8 | 4 con dirección, 4 NOERROR sin AAAA | 4 con dirección, 4 NOERROR sin AAAA |
| Controles técnicos, A | 8 | 6 con dirección, 2 NXDOMAIN | 6 con dirección, 2 NXDOMAIN |
| Controles técnicos, AAAA | 8 | 6 con dirección, 2 NXDOMAIN | 6 con dirección, 2 NXDOMAIN |

La forma de respuesta de cada nombre se repitió en ambas rondas. En A, los seis nombres de apuestas devolvieron direcciones con el perfil sin filtro y NXDOMAIN con el familiar. En AAAA solo tres devolvieron una dirección con la referencia sin filtro. En ambos perfiles, los cuatro nombres educativos devolvieron una dirección A y dos devolvieron una dirección AAAA. Las respuestas NXDOMAIN en los controles técnicos correspondieron al nombre reservado bajo `.invalid`. Los nombres de prueba de Cloudflare se incluyeron por continuidad con la medición anterior. Su comportamiento en Mullvad solo describe cómo respondieron esos nombres.

La guía de Mullvad identifica el perfil familiar con filtrado de apuestas. También anuncia el retiro del DNS público para el 2 de noviembre de 2026. El 19 de noviembre, en una comprobación adicional de `example.com`, se obtuvo respuesta por HTTP/2 en ambas direcciones IP publicadas, con TLS 1.3 y un certificado de Let's Encrypt válido para ambos nombres de servidor. El registro de esa comprobación se conserva por separado. La disponibilidad futura del servicio y el cumplimiento de la instrucción chilena por los proveedores de acceso quedan fuera del alcance de estas consultas. [Guía del proveedor](https://mullvad.net/en/help/dns-over-https-and-dns-over-tls) · [Anuncio de retiro](https://mullvad.net/en/blog/2026/9/3/shutting-down-our-public-encrypted-dns-servers-and-sponsoring-quad9-instead)

## Repetir y revisar la medición

Desde la raíz del repositorio, con las dependencias de desarrollo instaladas, este comando intenta el mismo contraste y registra los fallos de conexión si ya no se puede alcanzar un servicio. Usar una ruta de salida nueva para cada ejecución. La medición se ejecutó con la [versión del programa del 18 de noviembre](https://github.com/vigneauuu/Practica_DNS_VPN/blob/79a831aea2bb1d8f5e2cef69604baa9918fb11b8/scripts/contrastar_doh.py).

```bash
mkdir -p results/repeticion-subtel
python scripts/contrastar_doh.py --mullvad \
  --corpus dataset/doh-apuestas-subtel-2026-11-18.csv \
  results/repeticion-subtel/respuestas.json
```

En cada fila del registro local se conservan perfil, nombre consultado, tipo, ronda, hora UTC, campos de respuesta y mensaje DNS serializado. Para comprobar los recuentos se agrupa por categoría, perfil y tipo. Se cuentan NXDOMAIN por código de respuesta y, dentro de NOERROR, se comprueba si la sección de respuesta contiene una dirección del tipo consultado. El archivo de evidencia pública incluye las huellas SHA-256 del programa, la lista y el registro local de esta ejecución.

La figura del informe compara estas respuestas A con la medición de DNS4EU. Se genera desde los dos resúmenes públicos, sin emitir consultas de red.

```bash
python scripts/graficar_contraste_categorias.py \
  docs/evidencia/doh-apuestas-subtel-2026-11-18.json \
  docs/evidencia/doh-dns4eu-2026-11-19.json \
  results/contraste-categorias.pdf
```
