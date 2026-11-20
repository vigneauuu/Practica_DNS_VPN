# Reposición de candidatos con procedencia documentada

El [cotejo de procedencia](cotejo-corpus-2026-11-19.md) retiró 266 nombres heredados bajo la etiqueta de armas. El inventario repuesto conserva los 1.734 restantes y registra 266 altas. Se mantuvieron los archivos anteriores y se utilizó el nombre DNS exacto. Para seleccionar portales educativos se descartaron además alias con o sin `www` que duplicaran un nombre ya incluido.

| Categoría de las altas | Dominios | Procedencia |
|---|---:|---|
| Adulto | 22 | Cuatro de la revisión documental del piloto y 18 nombres de Ofcom |
| Apuestas | 39 | Tres del piloto y 36 nombres de Subtel |
| Armas | 3 | Tres fabricantes de la revisión documental del piloto |
| Educativo | 202 | Tres del piloto, 22 de CRUCH y 177 de IPEDS. Los de CRUCH e IPEDS coinciden con registros educativos activos de ROR |

Se incorporaron primero los nombres documentados sobre las categorías restringidas y luego los portales de contraste. Se priorizaron los portales chilenos por el lugar del estudio y se completó el grupo educativo con una selección reproducible de IPEDS. Los tamaños describen la selección y dejan tres ejemplos de armas para una primera comparación. La revisión final debe comprobar la categoría y registrar responsable y fecha antes de admitir cada nombre. Popularidad y procedencia de biblioteca siguen como etiquetas de origen. [Inventario repuesto](../dataset/corpus-parental-repuesto-2026-11-19.csv) · [Manifiesto](../dataset/corpus-parental-repuesto-2026-11-19.build.json) · [Plan de selección](evidencia/plan-corpus-repuesto-2026-11-19.json)

El 20 de noviembre se examinaron las portadas HTTPS de los 199 portales con coincidencia de dos catálogos. Se registró el título y hasta dos enlaces del mismo portal a páginas de admisión, carreras u otras secciones académicas. En 166 se observaron el título y al menos uno de esos enlaces. De los 33 restantes, 11 devolvieron HTML sin ambos indicios, 16 devolvieron otra respuesta HTTP, dos redirigieron fuera del portal y cuatro dieron error de lectura. Esta comprobación documenta la portada y deja los demás casos para revisión. [Evidencia por portal](evidencia/portadas-educativas-2026-11-20.json)

## Repetición

Descargar [ROR v2.16](https://doi.org/10.5281/zenodo.24378467) y [IPEDS HD2024](https://nces.ed.gov/ipeds/datacenter/data/HD2024.zip). Usar el [extracto fechado de CRUCH](../dataset/fuentes/directorio_cruch_2026-11-19.csv), cotejado con el [directorio de universidades](https://consejoderectores.cl/el-consejo/universidades-cruch/). Desde la raíz y con el entorno del proyecto activo, indicar archivos de salida nuevos.

```bash
mkdir -p results/repeticion-reposicion
python scripts/reponer_corpus.py --ror RUTA_AL_ZIP_ROR --ipeds RUTA_AL_ZIP_IPEDS \
  --output results/repeticion-reposicion/corpus.csv
cmp dataset/corpus-parental-repuesto-2026-11-19.csv results/repeticion-reposicion/corpus.csv
pdns-lab study-plan --corpus results/repeticion-reposicion/corpus.csv
python scripts/revisar_portadas_educativas.py results/repeticion-reposicion/corpus.csv \
  results/repeticion-reposicion/portadas.json
```
