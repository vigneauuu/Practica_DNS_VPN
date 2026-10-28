# Caracterización reproducible de DNS protector

Práctica I de **Matías Vigneau Andrades**, Universidad Diego Portales. Profesor guía: Nicolás Boettcher.

El proyecto caracteriza respuestas de perfiles de protección para control parental ante un corpus documentado. El inventario de phishing se conserva como antecedente separado, sin incorporarlo al estudio parental principal. Distingue señales de bloqueo, resolución observada, anomalías y errores de red. El acuerdo entre perfiles se informa por separado de la eficacia respecto de una política.

## Estado del avance

- Informe con la presentación de la plantilla y ocho apartados: antecedentes y motivación, objetivos, alcances y limitaciones, resultados esperados, estado del arte, metodología de trabajo, desarrollo y conclusiones. Dos diagramas de recorridos y evidencia; conclusiones pendientes hasta finalizar.
- Corpus heredado auditado: **1.960 filas**, 94 entradas inválidas, 14 solapamientos y **1.852 candidatos únicos**. Las categorías están pendientes de revisión semántica.
- Meta operativa: **2.000 dominios únicos revisados**; no se atribuye esta cantidad al profesor. El conjunto parental tiene **2.000 candidatos únicos**, incluidos 534 de contraste de la lista universitaria UT1 `liste_bu`; todos siguen pendientes de revisión. El inventario original de 1.852 se conserva por separado. Ver [diseño del estudio](docs/diseno_estudio.md).
- Motor nuevo con mensajes DNS completos, A/AAAA, EDE, controles temporales, reintentos registrados y ejecuciones independientes.
- Seis perfiles públicos configurados. Su configuración no acredita que se hayan completado pruebas de todos ellos.
- Importación local y exportación de listas para OONI; prueba HTTP opcional para proxies. No se han ejecutado ni publicado mediciones OONI.
- Calibración limitada registrada; no hay todavía una evaluación final de eficacia. Ver [correcciones y pendientes](docs/correcciones.md).
- Base exploratoria histórica: 13.720 registros, 1.960 por cada uno de cuatro resolutores y tres condiciones VPN gratuitas. Se conserva como antecedente; no se incorpora a las mediciones del diseño actual sin comprobar sus condiciones.

## Trabajar en Linux

La carpeta del repositorio es el espacio de trabajo. El entorno virtual contiene las dependencias; el editor es opcional. El intérprete del proyecto es `.venv/bin/python`.

```bash
cd /home/matias/Practica_Laboral/Practica_DNS_VPN
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
pdns-lab corpus-review --domain DOMINIO_REVISADO --categories CATEGORIA \
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
pdns-lab corpus-audit --corpus dataset/corpus-parental-candidatos.csv
# Reconstruirlo a otra salida, sin sobrescribir revisiones:
pdns-lab corpus-parental-build --output results/parental-reconstruido.csv

# Solo cuando existan al menos 2.000 revisados en alcance:
pdns-lab corpus-select --output results/corpus-parental-2000.csv
# Después de comprobar composición, política de perfiles y calibración:
pdns-lab run --corpus results/corpus-parental-2000.csv --rounds 3
```

La ejecución normal selecciona únicamente entradas validadas. `--include-unreviewed` es una opción explícita para exploración; la ejecución queda identificada como tal. Los intervalos, límites, rondas, tipos, semilla, timeout y reintentos son configurables. Cada muestra conserva las consultas de control antes y después, cuando el perfil tiene referencia. No se infiere la edad de la caché a partir de un TTL aislado.

```bash
pdns-lab analyze --run-id IDENTIFICADOR_IMPRESO --output results/resumen.json
```

El análisis informa estados y denominadores, estabilidad, cobertura y acuerdo por pares. Kappa puede ser no definido. Una resolución observada no garantiza acceso web y una anomalía no equivale a bloqueo confirmado. La base nueva está en `results/mediciones.sqlite3`; el identificador evita mezclar rondas de ejecuciones diferentes.

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

## Informe, seguimiento y estructura

- [Fuentes del informe](docs/informe/Practica1.tex) y [bibliografía](docs/informe/referencias.bib).
- [Proyecto de Overleaf](https://www.overleaf.com/project/6a2c499851552daecb5b028d).
- [Criterios permanentes del profesor](docs/criterios_profesor.md) y [plantilla para reuniones](docs/reuniones/plantilla.md).
- [Correcciones aplicadas y pendientes](docs/correcciones.md).
- [Auditoría del corpus](dataset/corpus.audit.json) y [calibración limitada](docs/evidencia/calibracion-resumen.json).

`src/pdns_lab/` contiene la implementación actual; `tests/`, sus pruebas; `config/`, los perfiles públicos; `dataset/`, los candidatos y controles. `legacy/` conserva los scripts anteriores. `resultados.db` es la base histórica ya versionada: no se modifica ni se interpreta con las reglas nuevas. Los resultados detallados nuevos, el entorno virtual, credenciales y archivos privados quedan fuera de Git.
