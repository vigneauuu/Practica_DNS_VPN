# Revisión documental de los 2.000 candidatos

El 19 de noviembre se compararon los nombres del inventario con catálogos publicados. El cotejo se hizo localmente con copias de las fuentes, sin consultar los sitios candidatos. El inventario original conserva sus etiquetas para poder reconstruirlo. [Resultados por dominio y huellas de los archivos](evidencia/cotejo-corpus-2026-11-19.json)

| Grupo de procedencia | Nombres | Resultado del cotejo |
|---|---:|---|
| Adulto | 400 | Ningún nombre coincide con una URL raíz de categoría `PORN` en las listas de Citizen Lab. Sigue pendiente la revisión individual. |
| Apuestas | 400 | 12 nombres con evidencia. Seis figuran en la nómina chilena de Subtel y siete en la categoría `GMB` de Citizen Lab. Un nombre figura en ambas. |
| Antigua etiqueta de armas | 266 | El archivo de origen es una copia de la categoría `agressif` de UT1. Se retira la etiqueta de armas de los 266. |
| Lista de biblioteca UT1 | 534 | 37 nombres aparecen en registros activos de instituciones educativas de ROR. |
| Lista popular | 400 | Otros tres aparecen en registros educativos de ROR. La posición en el ranking no intervino en el cotejo. |

Los 2.000 nombres se distribuyen en **52 con coincidencia documental**, **266 con la etiqueta de origen retirada** y **1.682 sin coincidencia positiva en las fuentes y categorías comparadas**. El archivo conserva su estado de revisión por persona. Ninguna fila recibió aprobación final por este cotejo. Para llegar a 2.000 revisados se necesitan al menos 266 reemplazos. [Plan de selección](evidencia/plan-corpus-2000.json)

## Fuentes y criterios

El archivo heredado `armas_top400.csv` tiene los mismos 5.777 bytes que el miembro `agressif/domains` descargado de UT1. La universidad describe esa categoría como sitios de racismo, antisemitismo e incitación al odio. El archivo contiene 360 filas, de las cuales el constructor conservó 266 nombres únicos válidos. No aporta evidencia para identificar sitios de armas. Al planificar y al medir, el programa omite esa etiqueta cuando su procedencia contiene la huella del archivo. Una revisión individual posterior puede registrar otra categoría o documentar armas con evidencia independiente, responsable y fecha. Los tres fabricantes del piloto proceden de una selección separada. [Descripción de UT1](https://dsi.ut-capitole.fr/blacklists/index.php) · [Archivo de UT1](https://dsi.ut-capitole.fr/blacklists/download/agressif.tar.gz)

Para los grupos de biblioteca y popularidad se usó ROR v2.16, edición del 19 de noviembre de 2026 publicada bajo CC0. Se exigió registro institucional activo, tipo `education` y coincidencia exacta con un nombre del campo `domains` o con el host de una página principal institucional. Se conservó cada identificador ROR para revisar el registro correspondiente. De los 40 nombres encontrados, 29 pertenecen también a los 39 educativos del piloto y 11 quedan fuera de ese panel. La asociación con una institución identifica posibles sitios de contraste. El contenido actual de cada sitio y sus subdominios requiere revisión aparte. [Datos de ROR v2.16](https://doi.org/10.5281/zenodo.24378467) · [Descripción del registro](https://ror.readme.io/docs/data-dump)

Para los grupos adulto y apuestas se compararon las listas geográficas y global de pruebas de censura de Citizen Lab y colaboradores. Se exigió categoría `PORN` o `GMB`, según correspondiera, URL HTTP(S) sin ruta adicional, parámetros ni fragmento y nombre de host idéntico, conservando `www` y otros subdominios. Estas listas se actualizan mediante aportes de la comunidad. La fecha registrada es la de incorporación de la URL. La ausencia de un nombre en ellas deja abierta su categoría. Las coincidencias de apuestas se reunieron con el cotejo previo de la nómina de 42 sitios de Subtel, contando cada nombre una vez. [Citizen Lab and Others, edición consultada y licencia CC BY-NC-SA 4.0](https://github.com/citizenlab/test-lists/tree/fe6ca9beb46e127878b1448005347296787025ec) · [Metodología de las listas](https://ooni.org/get-involved/contribute-test-lists/) · [Cotejo de Subtel](evidencia/contraste-apuestas-subtel-2026-11-18.json)

## Reproducir

Descargar las tres publicaciones y ejecutar desde la raíz del proyecto con el entorno de Python activado. El programa lee las fuentes locales y escribe el resultado en la salida estándar. Comprueba la huella de ROR, las tablas de Citizen Lab y la igualdad del miembro de UT1 con la copia histórica. Si cambia la edición disponible en la URL de UT1, debe utilizarse la copia de la fecha del cotejo.

```bash
mkdir -p results/cotejo
curl --fail --location 'https://zenodo.org/records/24378467/files/v2.16-2026-11-19-ror-data.zip' -o results/cotejo/ror.zip
curl --fail --location 'https://codeload.github.com/citizenlab/test-lists/zip/fe6ca9beb46e127878b1448005347296787025ec' -o results/cotejo/citizenlab.zip
curl --fail --location 'https://dsi.ut-capitole.fr/blacklists/download/agressif.tar.gz' -o results/cotejo/agressif.tar.gz
python scripts/cotejar_inventario.py --ror results/cotejo/ror.zip \
  --citizen results/cotejo/citizenlab.zip --ut1 results/cotejo/agressif.tar.gz \
  > results/cotejo/resultado.json
cmp docs/evidencia/cotejo-corpus-2026-11-19.json results/cotejo/resultado.json
```
