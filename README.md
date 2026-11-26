# Evaluación reproducible de Protective DNS (PDNS) para control parental

Práctica I de **Matías Vigneau Andrades**, Universidad Diego Portales. Profesor guía: Nicolás Boettcher.

El proyecto evalúa comparativamente respuestas de servicios de *Protective DNS* (PDNS), VPN y proxies para control parental ante un corpus documentado. El inventario de phishing se conserva como antecedente separado, sin incorporarlo al estudio parental principal. Distingue señales de bloqueo, resolución observada, anomalías y errores de red. El acuerdo entre perfiles se informa por separado de la eficacia respecto de la política de filtrado declarada por cada proveedor.

## Resumen del estudio y resultados

- Informe final (`docs/informe/Practica1.tex`, 11 tablas, 11 figuras unificadas, 64 referencias) con resumen y nueve secciones: antecedentes y motivación, objetivos, alcances y limitaciones, resultados esperados y productos entregables, estado del arte, metodología de trabajo, desarrollo y resultados, conclusiones y trabajo futuro.
- Corpus auditable: auditoría sintáctica de **1.960 filas** iniciales (94 entradas inválidas, 14 solapamientos, **1.852 dominios únicos**), exclusión verificada por SHA-256 de UT1 `agressif` (266 entradas de incitación al odio), reposición a **2.000 candidatos documentados** (`dataset/corpus-parental-repuesto-2026-11-19.csv`), verificación HTTPS de 199 portales educativos CRUCH/IPEDS (166 verificados) y conjunto común de evaluación de **448 nombres** (`dataset/benchmark-pdns-2026-11-25.csv`: 42 apuestas Subtel, 22 adultos UE/Ofcom, 13 fabricantes oficiales de armas, 166 universidades verificadas, 200 candidatos comunitarios estratificados y 5 controles técnicos). [Reposición del corpus](docs/reposicion-corpus-2026-11-19.md) · [Diseño del estudio](docs/diseno_estudio.md)
- Paquete `pdns-lab` (UDP/TCP/53, controles temporales, SQLite y 30/30 pruebas unitarias aprobadas) más scripts reproducibles para DoH HTTP/2, DoT/853, VPN/proxy, reclasificación con huellas verificadas y consultas a la API pública de OONI.
- Mediciones TCP/53: estudio base (50 dominios, 600 observaciones) y ampliación de 14 perfiles de 7 proveedores (4.200 observaciones, 9.600 consultas, 2 errores en Control D Sin filtro), reclasificados en solo lectura con huellas verificadas por operador (`docs/evidencia/reclasificacion-ampliacion-tcp-2026-11-25.json`, 0/39 falsos positivos educativos en los 14 perfiles).
- Evaluación unificada DoH HTTP/2 (25-11-2026): **35.840 consultas** sobre los **20 perfiles lógicos de los 9 proveedores DNS** frente a los 448 nombres (`docs/evidencia/benchmark-pdns-2026-11-25.json`, 99,96 % recepción, 0/166 falsos positivos educativos, 13/13 armas en DNS4EU Infantil, discrepancia en `estelarbet.cl` y 90 dominios en candidatos adultos de UT1, matrices de Kappa y Jaccard por categoría).
- Experimento pareado de 4 transportes (`docs/evidencia/transportes-udp-tcp-doh-dot-2026-11-25.json`): UDP/53 (subconjunto de 12 dominios en A) y TCP/53 al mismo umbral (`2,5 s`), DoH y DoT/853 (`3,5 s`) sobre 24 dominios del conjunto de evaluación, con **100 % de paridad exacta** (`72/72` UDP/TCP, `960/960` TCP/DoH, `960/960` TCP/DoT, `1.152/1.152` DoH/DoT) y verificación de DoT/853 operativo en los 9 proveedores (incluido Cisco OpenDNS FamilyShield en `208.67.222.123` con SNI `dns.opendns.com`).
- Intermediarios VPN y proxy: controles causales de laboratorio (OpenVPN y proxy HTTP), Cloudflare WARP (túnel y SOCKS5), RiseupVPN (2 perfiles DoH de DNS4EU + DNS interno UDP), Tor SOCKS5 y AdGuard VPN (túnel UDP y SOCKS5). [WARP](docs/warp-2026-11-18.md) · [Riseup y Tor](docs/riseup-tor-2026-11-19.md) · [AdGuard VPN](docs/adguard-vpn-2026-11-20.md)
- Contraste externo OONI Chile (`docs/evidencia/ooni-chile-2026-11-25.json`): 194 mediciones recientes en 7 ASN chilenos (`limit=50` por URL; `juegalo.com` con 37/44 anomalías = 84,1 % frente a 146/150 accesos normales = 97,3 % en `pornhub.com`, `xnxx.com` y `xvideos.com`).

## Trabajar en Linux

La carpeta del repositorio es el espacio de trabajo. El entorno virtual contiene las dependencias; el editor es opcional. El intérprete del proyecto es `.venv/bin/python`.

```bash
git clone https://github.com/vigneauuu/Practica_DNS_VPN.git
cd Practica_DNS_VPN
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```

Se requiere Python 3.11 o posterior. El entorno instalado en este equipo utiliza Python 3.14. Las versiones verificadas están en `requirements-dev.lock`. Para recrearlas: `python -m pip install -r requirements-dev.lock` y luego `python -m pip install -e . --no-deps`.

## Corpus y validación

```bash
pdns-lab corpus-audit
# Generar otra copia desde los snapshots heredados, sin sobrescribir revisiones:
pdns-lab corpus-build --output results/corpus-reconstruido.csv
```

`dataset/corpus.csv` tiene una fila por nombre, categorías separadas por `|`, procedencia y estado de revisión. No usa la palabra «reciente» como sinónimo de phishing. El generador conserva los rechazos en un informe de auditoría y no sobrescribe un corpus existente.

Después de revisar un caso con evidencia suficiente se registra, por ejemplo:

```bash
pdns-lab corpus-review --corpus dataset/corpus-parental-repuesto-2026-11-19.csv \
  --domain DOMINIO_REVISADO --categories CATEGORIA \
  --evidence 'DOCUMENTO_O_EVIDENCIA_REVISADA' --reviewer 'Matías Vigneau'
```

Las categorías admitidas son `popular`, `adultos`, `apuestas`, `armas`, `educativo`, `referencia_biblioteca`, `phishing` y `control_tecnico`. El programa exige evidencia, responsable y fecha para el estado validado; no sustituye la revisión del contenido. Usar `--exclude` para registrar una exclusión.

## Planificar y medir

```bash
# Solo calcula y muestra el plan; no transmite consultas:
pdns-lab run --include-unreviewed --limit 10 --dry-run

# Calibración técnica, usando dominios de ejemplo y prueba documentados:
pdns-lab run --corpus dataset/calibracion.csv \
  --select cloudflare_standard,cloudflare_family --rounds 1 --qtypes A

# Consultar avance hacia la meta, sin red:
pdns-lab study-plan
# Auditar el conjunto parental de 2.000 candidatos:
pdns-lab corpus-audit --corpus dataset/corpus-parental-repuesto-2026-11-19.csv
# Reconstruir el inventario anterior, antes de reponer candidatos:
pdns-lab corpus-parental-build --output results/parental-reconstruido.csv

# Solo cuando existan al menos 2.000 revisados en alcance:
pdns-lab corpus-select --output results/corpus-parental-2000.csv
# Después de comprobar composición, política de perfiles y calibración:
pdns-lab run --corpus results/corpus-parental-2000.csv --rounds 3
```

La ejecución normal selecciona únicamente entradas validadas. `--include-unreviewed` es una opción explícita para exploración; la ejecución queda identificada como tal. Los intervalos, límites, rondas, tipos, semilla, tiempo de espera y reintentos son configurables. Cada muestra conserva las consultas de control antes y después, cuando el perfil tiene referencia. No se infiere la edad de la caché a partir de un TTL aislado.

```bash
pdns-lab analyze --run-id IDENTIFICADOR_IMPRESO --output results/resumen.json
```

El análisis informa estados y denominadores, consistencia ante consultas repetidas, cobertura y acuerdo por pares. Kappa puede ser no definido. Una resolución observada no garantiza acceso web y una anomalía no equivale a bloqueo confirmado. La base nueva está en `results/mediciones.sqlite3`; el identificador evita mezclar rondas de ejecuciones diferentes.

## VPN, proxy y OONI

Para incorporar una VPN, copiar y completar los ejemplos de `config/` en una ubicación local, declarar su resolutor y registrar la configuración real. El programa verifica que la interfaz esté activa y la ruta al resolutor use esa interfaz. No inicia túneles ni cambia el DNS del sistema. Una extensión de navegador requiere comprobar su propio ámbito; una consulta en consola no demuestra que la atraviese.

```bash
pdns-lab run --profiles results/vpn-profiles.json --select PERFIL \
  --context results/vpn-context.json --corpus dataset/calibracion.csv --limit 1

# Proxy opcional: la URL y credenciales se toman de una variable local, no del repositorio.
pdns-lab http-probe --url https://example.com --proxy-env PDNS_PROXY_URL \
  --output results/proxy-prueba.json

# Lista de destinos validados e importación de mediciones ya disponibles:
pdns-lab ooni-export --output results/ooni-urls.txt
pdns-lab ooni-import RUTA_A_MEDICIONES_JSON_O_JSONL --output results/ooni-resumen.json
```

La prueba HTTP verifica TLS, limita la lectura, no sigue redirecciones ni ejecuta contenido. Un 403 no se etiqueta como bloqueo; las huellas se proporcionan en un JSON local con `--fingerprints`, como `[{"text": "HUELLA", "source": "EVIDENCIA_DE_CALIBRACION"}]`, después de verificarlas. OONI tiene su propio diseño y puede publicar resultados según la configuración: la herramienta de este repositorio solo intercambia archivos locales. Consultar su [documentación de interpretación](https://ooni.org/support/interpreting-ooni-data/).

## Informe, diseño y estructura

- [Fuentes del informe](docs/informe/Practica1.tex) y [bibliografía](docs/informe/referencias.bib).
- [Evaluación de la política infantil de DNS4EU](docs/politica-dns4eu-2026-11-19.md), [pruebas con Riseup y Tor](docs/riseup-tor-2026-11-19.md) y [contraste del control con OONI](docs/ooni-control-2026-11-19.md).
- [Comparación de los perfiles familiares de Cloudflare y AdGuard](docs/filtros-familiares-2026-11-19.md) y [contraste con AdGuard VPN](docs/adguard-vpn-2026-11-20.md).
- [Diseño del estudio](docs/diseno_estudio.md) e [inventario de servicios](docs/inventario_servicios.md).
- [Auditoría del corpus](dataset/corpus.audit.json) y [calibración limitada](docs/evidencia/calibracion-resumen.json).

`src/pdns_lab/` contiene la implementación actual; `tests/`, sus pruebas; `config/`, los perfiles públicos; `dataset/`, los candidatos y controles. `legacy/` conserva los scripts anteriores. `resultados.db` es la base histórica ya versionada: no se modifica ni se interpreta con las reglas nuevas. Los resultados detallados nuevos, el entorno virtual, credenciales y archivos privados quedan fuera de Git.
