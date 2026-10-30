# Diseño y meta de 2.000 dominios

## Qué se quiere medir

Caracterizar el comportamiento de servicios que filtran categorías de contenido pertinentes para control parental. Diferenciar la política declarada del proveedor, la categoría revisada del dominio y la evidencia de red. Investigar también bloqueo indebido de contenido permitido, por ejemplo educativo revisado.

Los audios del anteproyecto explicitan este foco. Los audios posteriores afinan PDNS, fuentes, categorías, OONI y recorridos. Se conservan en su orden relativo; una sugerencia antigua no se presenta como una exigencia nueva. Phishing se mantiene como inventario histórico separado: una mención posterior de FINSIN no acredita por sí sola que se haya revocado la indicación de no mezclar detección de amenazas con contenido parental.

## La cantidad

`config/estudio.json` establece una **meta operativa de 2.000 dominios únicos revisados**, solicitada por Matías. No se encontró una exigencia inequívoca del profesor de utilizar exactamente 2.000. Su exigencia es justificar selección, categorías, fuentes y carga, sin introducir cifras o métodos sin antecedentes. El número no acredita representatividad de Internet ni un margen de error.

No se rellenará automáticamente con 148 nombres populares para convertir el inventario de 1.852 en 2.000. Eso conservaría las etiquetas cuestionadas, mezclaría phishing con el estudio parental y cambiaría la composición sin una razón de contenido. Tampoco se impondrán 400 por cada categoría heredada.

La auditoría actual distingue:

| Concepto | Cantidad | Significado |
|---|---:|---|
| Inventario histórico normalizado | 1.852 | Incluye phishing; todas las etiquetas pendientes |
| Base heredada con alguna etiqueta del alcance | 1.466 | Se retiran los exclusivamente de phishing; no son datos validados |
| Contraste universitario incorporado | 534 | Procedencia UT1 liste_bu; etiqueta referencia_biblioteca, pendiente de revisión |
| Conjunto parental candidato | 2.000 | Nombres únicos en archivo separado, no corpus final validado |
| Dominios revisados en alcance | 0 | No se ha simulado la revisión humana |
| Meta de selección final | 2.000 | Únicos y con evidencia de categoría |
| Nuevos candidatos necesarios para completar el inventario | 0 | Ya hay 2.000 candidatos; habrá que sustituir los descartados |

Las 14 entradas con etiquetas adulto y phishing se cuentan una vez dentro del inventario en alcance por su etiqueta candidata de adulto. Esta regla no valida esa etiqueta. La categoría heredada de armas contiene indicios de odio/violencia; debe comprobarse su fuente y clasificación antes de admitirla. Popularidad tampoco acredita contenido permitido. Falta validar el contraste educativo; las referencias universitarias no se dan por educativas automáticamente.

## Puertas de avance

1. Identificar fuentes pertinentes y su taxonomía, versión, fecha y método de categorización. Comparar fuentes alternativas; buscar el corpus previo del trabajo de Nicolás Rojas si está disponible, sin afirmar que ya se recuperó.
2. Normalizar y deduplicar; conservar etiquetas múltiples, desacuerdos y procedencia. Revisar evidencia con responsable y fecha, separando actividad de categoría.
3. Consultar `pdns-lab study-plan`. El resultado reproducible está en `docs/evidencia/plan-corpus-2000.json`.
4. Al reunir suficientes revisados, usar `pdns-lab corpus-select --output results/corpus-parental-2000.csv`. Selecciona exactamente 2.000 sin reemplazo y guarda semilla, composición y SHA-256. Si faltan revisados, falla sin crear un archivo final incompleto. La selección no impone balance por categoría; la composición y cualquier necesidad de ajuste se revisan antes de medir.
5. Construir una matriz por servicio: categoría ofrecida, plan, configuración, transporte, referencia, condiciones y evidencia. Los seis perfiles instrumentados no constituyen el inventario definitivo ni cubren necesariamente armas/apuestas. Un filtro de amenazas no se juzga como filtro parental universal.
6. Calibrar y medir con controles; informar indeterminados. Estimar aciertos o errores solo respecto de categorías y decisiones esperadas revisadas. Acuerdo, Kappa y similitud siguen siendo descriptores de acuerdo, no verdad de referencia.

## Tamaño y carga

Con 2.000 dominios, seis perfiles, A y AAAA y tres rondas se planifican 72.000 observaciones del perfil; con cuatro perfiles que requieren dos controles, son 168.000 grupos de consulta antes de reintentos. Estas cantidades dimensionan la carga; no autorizan una ejecución completa sin calibración ni justifican un nivel de confianza estadístico. Si cambia el inventario de perfiles, debe recalcularse el plan.

## Trabajo que no se presenta como completado

La adquisición y validación semántica faltantes, la cobertura final de categorías/servicios y la calibración no se resuelven añadiendo filas. No se ha implementado un algoritmo nuevo de categorización, un resolutor propio con respuestas explicables ni ingeniería inversa del algoritmo de un proveedor. Las ideas de transparencia del anteproyecto son posibles líneas posteriores; los EDE recibidos se conservan como evidencia del servicio.

## Construcción reproducible del conjunto candidato de 2.000

Se descargó el archivo oficial `https://dsi.ut-capitole.fr/blacklists/download/liste_bu.tar.gz`. La descripción UT1 identifica una lista de uso universitario local; no es una garantía de benignidad ni equivalencia con un dataset educativo. Del snapshot se seleccionaron sin reemplazo 534 nombres válidos que no estaban en la base parental, con semilla 20261027. Esta cantidad completa la meta de inventario y añade un contraste de procedencia distinta; no es una cuota estadística óptima ni impuesta por el profesor. Su composición deberá revisarse antes de la medición final.

`dataset/corpus-parental-candidatos.csv` contiene exactamente 2.000 candidatos únicos. `dataset/corpus-parental-candidatos.build.json` conserva rechazos, hashes y cantidades; cada fila nueva registra línea y fuente. El snapshot reproducible está en `dataset/fuentes/` y el archivo comprimido original queda fuera del repositorio. El inventario histórico `dataset/corpus.csv` permanece intacto. Reconstruir a otra salida con `pdns-lab corpus-parental-build --output results/parental-reconstruido.csv`.

## Revisión de fuentes y etiquetas antes de medir

Precisión del procedimiento, 29-10-2026; todavía pendiente de ejecución. Para cada fuente registrar definiciones de categoría, copia y fecha, método publicado de asignación y actualización de etiquetas, y fuentes que reutiliza. Si no hay descripción del método, señalar información no disponible. Dos listas derivadas de una misma fuente no constituyen confirmaciones independientes.

En la evidencia de cada revisión conservar URL o documento, fecha, descripción del contenido observado o reportado y razón de la decisión; acompañarla de responsable y fecha en los campos del corpus. No inferir contenido por el nombre del dominio, popularidad, resolución o acuerdo entre servicios. Conservar discrepancias como pendientes y excluir de la selección final las entradas sin evidencia suficiente. Actividad y categoría se registran por separado. Antes de medir, comprobar composición por categoría y reemplazar descartados manteniendo su historial. Esto concreta la revisión prevista; no convierte los 2.000 candidatos en dominios validados.


## Piloto del 30 de octubre de 2026

Se preparó una selección separada de 50 dominios con evidencia documental preliminar para probar el proceso de medición y análisis. Las filas permanecen pendientes de validación final y se utiliza explícitamente el modo exploratorio. El piloto no utiliza el selector de 2.000 revisados ni acredita el cierre de esa meta. Su composición intencional y límites están en `piloto_2026-10-30.md`; no constituye una muestra representativa. Los conjuntos de 2.000 candidatos y de 1.852 históricos permanecen intactos.

## Requisito de cobertura por categoría (30-10-2026)

Antes de medir acierto de adulto, apuestas o armas, registrar un perfil que declare tratar esa categoría, su plan y configuración activa, evidencia de la categoría del dominio y calibración de controles. La configuración actual solo incluye una política de contenido adulto. Apuestas y armas siguen pendientes de perfiles comparables; las respuestas del piloto para esas categorías son observaciones de resolución. Ver `inventario_servicios.md` para el candidato CleanBrowsing configurable y sus límites de acceso. No reducir el alcance parental por conveniencia de los seis perfiles iniciales ni presentar al candidato como implementado.
