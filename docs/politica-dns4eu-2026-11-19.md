# Evaluación de la política infantil de DNS4EU

El 19 de noviembre de 2026 se repitió la comparación con los 42 nombres de la nómina de Subtel y los 46 nombres de adulto, armas y educativos de la revisión documental del piloto. Se conservaron los subdominios publicados y se omitieron las rutas de las URL. Se obtuvo el mismo SHA-256 de los 42 nombres, en orden de publicación, que en el cotejo anterior. Los tres fabricantes se documentaron por separado del lote heredado rotulado como armas. [Nómina de Subtel](https://www.subtel.gob.cl/subtel-ordena-bloqueo-de-42-sitios-de-apuestas-online/) · [Cotejo anterior](evidencia/contraste-apuestas-subtel-2026-11-18.json) · [Revisión documental del piloto](evidencia/piloto-50-revision-documental.json)

Se esperaba una señal de restricción para apuestas, adulto y armas, según la política del perfil infantil. Los portales educativos se usaron como controles de resolución frente al filtro adicional de contenido. El perfil protector mantiene la capa de amenazas del operador. Para interpretar un dominio, los perfiles protector y sin filtro debían devolver direcciones ordinarias en las dos rondas del mismo tipo DNS. En el perfil infantil se exigieron dos respuestas ordinarias o dos respuestas con las direcciones calibradas de la página de aviso. Se registraron aparte las respuestas inestables, otras señales y los casos sin referencia. [Política de DNS4EU](https://legal-documents-dns4eu.s3.fr-par.scw.cloud/DNS4EU-Public-DNS-Resolver-policy-2025.pdf) · [Dominios y decisiones esperadas](../dataset/referencia-politica-dns4eu-2026-11-19.csv)

Se recibieron 1.116 de 1.116 respuestas mediante DoH sobre HTTP/2, con verificación TLS. Corresponden a 88 dominios y cinco controles, tres perfiles, dos tipos y dos rondas. La primera consulta comenzó a las 20:09:23 y la última a las 20:12:33, hora de Santiago.

| Tipo | Grupo | Dominios | Aviso infantil | Dirección ordinaria infantil | Sin referencia |
|---|---|---:|---:|---:|---:|
| A | Apuestas | 42 | 38 | 2 | 2 |
| A | Adulto | 4 | 4 | 0 | 0 |
| A | Armas | 3 | 3 | 0 | 0 |
| A | Educativo | 39 | 0 | 39 | 0 |
| AAAA | Apuestas | 42 | 19 | 2 | 21 |
| AAAA | Adulto | 4 | 1 | 0 | 3 |
| AAAA | Armas | 3 | 1 | 0 | 2 |
| AAAA | Educativo | 39 | 0 | 9 | 30 |

En A hubo señal de restricción en 45 de 47 dominios restringidos interpretables. Las dos omisiones observadas también se repitieron en AAAA. Ninguno de los 39 controles educativos interpretables en A devolvió el aviso. Los resultados describen la selección documental y la ventana de medición. Comprobar el acceso web y estimar el desempeño en otros sitios requiere mediciones adicionales. [Evidencia por dominio, tipo, perfil y ronda](evidencia/politica-dns4eu-2026-11-19.json)

## Repetición

Desde la raíz del repositorio, usar un directorio nuevo y el entorno de Python de la práctica con `httpx[http2]`.

```bash
mkdir -p results/repeticion-politica
python scripts/contrastar_doh.py --dns4eu --todos-educativos \
    --control-adicional warning.joindns4.eu \
    --corpus dataset/referencia-politica-dns4eu-2026-11-19.csv \
    results/repeticion-politica/respuestas.json
python scripts/evaluar_politica_dns4eu.py \
    dataset/referencia-politica-dns4eu-2026-11-19.csv \
    results/repeticion-politica/respuestas.json results/repeticion-politica/resumen.json
```
