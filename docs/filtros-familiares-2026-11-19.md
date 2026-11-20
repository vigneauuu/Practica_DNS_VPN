# Comparación de los perfiles familiares de Cloudflare y AdGuard

El 19 de noviembre de 2026 se consultaron por DNS sobre HTTPS los perfiles familiar y dos perfiles de referencia de cada operador. En Cloudflare se usaron estándar y protección contra amenazas. En AdGuard se usaron sin filtro y predeterminado. El ensayo incluye los cuatro dominios de adulto y los 39 portales educativos documentados para el piloto. Una segunda ejecución añadió 18 nombres exactos publicados en la decisión de Ofcom sobre AVS Group (§§ 3.2 y 3.40), dos portales educativos del primer conjunto y los mismos controles técnicos. Los dominios se consultaron mediante DNS. [Cloudflare](https://developers.cloudflare.com/1.1.1.1/setup/#1111-for-families) · [AdGuard](https://adguard-dns.io/en/public-dns.html) · [Decisión de Ofcom](https://www.ofcom.org.uk/siteassets/resources/documents/about-ofcom/bulletins/enforcement-bulletin/avs-group-ltd/avs-group-ltd-final-confirmation-decision.pdf?v=410812)

Se consultaron A y AAAA en dos rondas por perfil. Se esperaba una señal de restricción para adulto y resolución para los portales educativos respecto de la política adicional del filtro familiar. Se exigió dirección ordinaria en ambas referencias y rondas para interpretar una comparación. La señal se identificó mediante EDE 15–17 o la dirección de la página de bloqueo documentada por el equipo de AdGuard en IPv4. Los fallos de transporte y las respuestas sin referencia se informaron aparte. El control sintético de contenido adulto de Cloudflare activó su perfil familiar. Para AdGuard ese nombre solo comprobó resolución. [Señal de AdGuard](https://github.com/AdguardTeam/AdGuardHome/issues/5028)

La primera ejecución recibió 1.124 respuestas de 1.128 consultas. Los cuatro errores fueron esperas agotadas en Cloudflare al consultar el mismo portal educativo. La segunda recibió sus 576 respuestas. Todas las respuestas válidas se obtuvieron con HTTP/2 y verificación TLS.

| Tipo | Grupo | Cloudflare familiar | AdGuard familiar |
|---|---|---:|---:|
| A | Adulto, 22 dominios | 22/22 con señal | 22/22 con señal |
| A | Educativos, 39 dominios | 38/38 resolvieron | 39/39 resolvieron |
| AAAA | Adulto, 22 dominios | 1/1 con señal | 1/1 con señal |
| AAAA | Educativos, 39 dominios | 9/9 resolvieron | 9/9 resolvieron |

Los cocientes usan los dominios comparables por operador, categoría y tipo. Para el recuento educativo se usó la primera ejecución. Los dos portales de la segunda sirvieron como comprobación adicional. La menor cobertura en AAAA se debe a la falta de una dirección IPv6 ordinaria estable en las referencias. Los 18 nombres de Ofcom pertenecen al mismo operador según esa fuente. Los resultados describen las selecciones consultadas. [Evidencia del primer conjunto](evidencia/filtros-familiares-2026-11-19.json) · [Evidencia del conjunto de Ofcom](evidencia/filtros-familiares-ofcom-2026-11-19.json)

## Repetición

Desde la raíz del repositorio, usar el entorno de Python de la práctica con `httpx[http2]` y un directorio de salida nuevo.

```bash
mkdir -p results/repeticion-familiar
for grupo in educativo ofcom; do
  corpus="dataset/referencia-adulto-${grupo}-2026-11-19.csv"
  salida="results/repeticion-familiar/${grupo}"
  python scripts/contrastar_doh.py --familia --todos-educativos --corpus "$corpus" "$salida.json"
  python scripts/evaluar_filtros_familiares.py "$corpus" "$salida.json" "$salida-resumen.json"
done
```
