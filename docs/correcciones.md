# Correcciones aplicadas y trabajo experimental pendiente

Actualización: 29 de octubre de 2026. Esta matriz distingue cambios de diseño e implementación de evidencia que todavía debe obtenerse. Las observaciones de las reuniones se resumen en [criterios_profesor.md](criterios_profesor.md).

| Observación | Cambio aplicado | Comprobación / estado |
|---|---|---|
| Objetivos sin antecedentes suficientes | Pregunta descriptiva sobre PDNS, objetivos alineados y alcances por perfil | Reescritura del informe y bibliografía específica |
| Confusión entre DNS, VPN y proxies | Definiciones, límites de cada capa y diagrama de recorridos | Dos diagramas TikZ incorporados; condiciones VPN/proxy documentadas |
| Hipótesis Kappa < 0,60 no fundamentada | Retirada; acuerdo, prevalencias y cobertura como descriptores separados de eficacia | Kappa no definido cuando corresponde; pruebas de casos degenerados |
| Índice propio sin justificación | Retirado de los objetivos y sustituido por descriptores explícitos | Tabla de contingencia, acuerdo y Jaccard con denominadores |
| Referencias genéricas y afirmaciones universales | Documentos identificables; eliminadas cifras y aseveraciones judiciales sin documento primario verificado | Las referencias no localizadas no se presentan como respaldo |
| DNSSEC confundido con cifrado | Distinción entre autenticidad/integridad y DoH/DoT | RFC 4033, RFC 8484 y RFC 7858 |
| Tamaño de muestra y exclusividad incorrectos | Auditoría de 1.960 filas, 94 rechazos y 14 solapamientos; 1.852 candidatos únicos | `dataset/corpus.audit.json`; categorías múltiples y procedencia por fila |
| Automatización presentada como validación | Estados pending/validated/excluded y evidencia con responsable y fecha | **Pendiente:** revisión semántica del conjunto parental de 2.000 candidatos; inventario histórico de 1.852 conservado |
| Phishing equiparado a dominio reciente | Etiqueta conceptual phishing; fecha y actividad son evidencias diferentes | El nombre del CSV original se conserva únicamente por procedencia |
| NXDOMAIN y errores tratados como bloqueo | Estados de evidencia y controles antes/después; huellas documentadas y EDE | Pruebas sobre NXDOMAIN, controles, sinkholes, EDE y errores |
| Registro incompleto y falta de reintentos | Mensajes completos, direcciones, TTL, banderas, intentos, tiempos y contexto | Pruebas de múltiples respuestas y reintentos; esquema nuevo por ejecución |
| Datos faltantes y duplicados ambiguos | Rondas explícitas, clave de observación y exclusión por par | Pruebas de inestabilidad, ejecución parcial y tercer perfil sin datos |
| Uso de OONI | Exportación de listas validadas e importación local de JSON/JSONL | **Pendiente:** ejecución y contraste OONI bajo condiciones documentadas |
| Fuentes alternativas locales | FINSIN identificado y citado como antecedente histórico | **Pendiente:** disponibilidad actual, condiciones de acceso y comparación de fuentes |
| Configuración VPN asumida | Plantillas locales; comprobación de interfaz activa y ruta al resolutor | **Pendiente:** perfiles reales y estado de protección verificable |
| Proxy tratado como respuesta DNS | Componente HTTP separado, TLS verificado, límites de lectura y huellas explícitas | Prueba de HTTP 403; **pendiente:** calibración de proxies reales |
| Fechas y resultados presentados como definitivos | Informe fechado como avance; auditoría, calibración y resultados finales diferenciados | Sin cuotas artificiales ni cronograma de entrega vencido |
| Entorno de desarrollo | `.venv`, paquete instalable, pruebas, versiones y guía Linux | Entorno Python documentado |
| Seguimiento de correcciones | Criterios y plantilla de reunión | Actualizar después de cada revisión |

## Calibración realizada

Ocho observaciones A, una ronda, cuatro dominios técnicos, dos perfiles de Cloudflare, timeout de un segundo y sin reintentos. En el perfil estándar se observaron tres resoluciones y un caso negativo indeterminado. El perfil familiar agotó el tiempo de espera en los cuatro casos. Esta comprobación acredita el registro y los estados, no una comparación de eficacia ni la causa de la falta de respuesta.

## Próximo trabajo, en orden

1. Completar o sustituir fuentes del corpus y revisar etiquetas con evidencia; conservar el historial de exclusiones y cambios.
2. Verificar conectividad y huellas de cada perfil antes de ampliar las rondas. Documentar ubicación y condiciones reales.
3. Ejecutar y contrastar OONI cuando esté definida su configuración y el destino de los resultados.
4. Incorporar VPN y proxies que cumplan el protocolo de documentación y calibración.
5. Ejecutar las rondas del corpus revisado, evaluar cobertura y estabilidad y recién entonces interpretar los resultados respecto de cada política.

Los cambios de redacción, diseño e implementación derivados de los audios 2 y 3 se describen en esta matriz. La revisión documental no cierra los pendientes experimentales señalados; las nuevas indicaciones se registrarán como una revisión posterior.

## Ajustes adicionales solicitados por Matías

Se desarrolló en antecedentes la razón de categorías, cantidades, perfiles y métricas antes de objetivos. Conclusiones queda vacío hasta finalizar la práctica. No hay una cuota de páginas ni un tamaño final de corpus acreditado por los audios revisados.

## Revisión de los audios antiguos del anteproyecto

Se añadió el foco parental y la separación de phishing, el contraste de contenido educativo permitido, la justificación de Python y la distinción práctica/tesis. Los perfiles instrumentados son iniciales: falta ampliar el inventario y acreditar cobertura por categoría. Ver `que_quiere_profesor.md`.

Meta de 2.000 únicos revisados en `config/estudio.json`, planificador y selector reproducible con bloqueo ante datos insuficientes. El inventario histórico conserva 1.852 candidatos. Se construyó un conjunto parental separado de 2.000: 1.466 heredados y 534 referencias universitarias UT1. Revisados: cero. La lista llamada armas requiere revisión de su significado; también las referencias de biblioteca requieren comprobar contenido y política esperada. Ver `diseno_estudio.md`.

Construcción final del inventario parental: `dataset/corpus-parental-candidatos.csv` contiene 2.000 únicos sin phishing; 534 son `referencia_biblioteca`, etiqueta de procedencia que no acredita benignidad ni educación. El corpus definitivo validado sigue pendiente. Ver `diseno_estudio.md`.

## Presentación del informe y registros exploratorios (28-10-2026)

Se recuperó la presentación base de la plantilla: portada con reglas horizontales, márgenes de 2 cm, letra de 10 puntos, encabezados y bibliografía IEEE. El informe vuelve a ocho apartados, con Resultados Esperados separado de Desarrollo. Las decisiones metodológicas y los controles se mantienen; el cronograma utiliza etapas relativas y redacción transversal, sin atribuir fechas nuevas a una aprobación del profesor. Este ajuste responde a la solicitud de Matías y a la plantilla conservada; no corresponde a una reunión nueva.

Se comprobaron mediante consultas de solo lectura 13.720 registros históricos, distribuidos en 1.960 por cada uno de cuatro resolutores públicos y tres condiciones VPN gratuitas (ProtonVPN, Windscribe y hide.me). Los recuentos se incorporan como antecedentes exploratorios. Las etiquetas y respuestas antiguas no se consideran validación del contenido ni pruebas de eficacia; faltan controles y evidencia de configuración comparables con el diseño actual. No se ejecutaron nuevas mediciones al realizar este ajuste documental.

## Claridad de redacción y continuidad del entorno

Se simplificaron el objetivo general, algunos títulos y las explicaciones de preparación y análisis. «Configuraciones intermediadas» pasa a «conexiones mediante VPN o proxy»; el diagrama utiliza «lista de dominios» y «copias de las fuentes». Se definen perfil y cobertura, y se explica qué significa registrar los resúmenes SHA-256. Se conservan las ocho secciones, las citas y las reglas de medición.

Los archivos recuperados de Windows se conservan como antecedentes. Las mediciones en Linux se registrarán como ejecuciones nuevas, tras comprobar la configuración, el resolutor y la ruta de la VPN. La recuperación conserva los registros anteriores sin validarlos de nuevo. Esta aclaración no cambia los datos ni constituye una ejecución nueva.

## Comprobación previa a revisión del profesor (28-10-2026)

Se contrastaron las observaciones de Audio3 y las nueve páginas del informe anotado con la versión actual. Se adelantó a antecedentes la razón de incluir VPN y proxies; se añadieron referencias de HTTP/SOCKS y de las fuentes StevenBlack y Phishing.Database. Se explicitó que la herramienta actual consulta DNS por UDP/TCP en el puerto 53 y no mide DoH/DoT; se definieron TTL, RD, RA, TC, DO y AD en su contexto. No se incorporaron resultados ni fechas de término nuevas.

Permanecen pendientes la validación de categorías, la selección final de servicios con sus políticas, la calibración de VPN/proxies, las mediciones comparativas y el contraste OONI. La meta de 2.000 es operativa, no un tamaño estadístico acreditado por la literatura. El cronograma del informe sigue siendo relativo, sin fechas administrativas confirmadas. La revisión documental no constituye aprobación del diseño por el profesor.

## Desarrollo continuo y reducción de subapartados (28-10-2026)

Se reaplicó la observación de Audio3 27:26–28:29 sobre subcapítulos demasiado breves, conforme a la solicitud de Matías. El informe pasa de 23 a 11 subapartados numerados: Antecedentes y Alcances se desarrollan sin divisiones internas; Objetivos conserva general/específicos; Estado del Arte reúne cinco bloques en tres; Metodología reúne siete en cuatro; Desarrollo reúne cuatro en dos. Las comprobaciones iniciales se explican junto a la implementación y los registros históricos junto a su auditoría. Se añadieron transiciones entre los bloques unidos.

Se conservan las ocho secciones principales, las citas, las tablas y los diagramas, el apartado de Resultados Esperados, el cronograma relativo y las conclusiones vacías. La reducción no cambia el método, los datos ni el estado de los pendientes. El criterio permanente aclara que el profesor pidió desarrollar los temas; la elección concreta de agrupación es una decisión editorial, no una cuota prescrita en la reunión.

La segunda pasada de control distingue la incorporación de una observación de su cumplimiento experimental. El informe describe avances, sin dar por cerrados la validación de categorías, el inventario de políticas y servicios, la calibración de conexiones o el contraste OONI. Se refuerza también el uso preciso de «servicio evaluado» frente a «herramienta de medición», según Audio2 00:49–00:58.

## Relación concreta entre antecedentes y práctica (28-10-2026)

Se aclaró el aporte del artículo de Rojas y colaboradores: evalúa funciones de aplicaciones parentales y sirve como antecedente de comprobación de la protección ofrecida; la práctica observa políticas y respuestas de filtrado de dominios con un diseño propio. Se precisó el aporte de Plonka (procedencia y objetivos de listas), Liu (formatos de respuesta PDNS) y FINSIN (posible contraste del inventario histórico de amenazas, fuera del corpus parental). La tabla de antecedentes describe los límites por objeto y tipo de medición.

Se simplificó la justificación de Python y la formulación de la meta operativa de 2.000, cuya procedencia como preferencia de Matías permanece registrada en los criterios y el contexto. Se conservan las ocho secciones y once subapartados, las referencias y los pendientes de validación y medición. No se añadieron resultados ni se modificó el diseño experimental.

La tabla de fuentes distingue las destinadas al corpus parental de las utilizadas o consideradas para revisar el inventario histórico de phishing; FINSIN y Phishing.Database no se presentan como incorporaciones al corpus parental definitivo.

## Revisión conjunta del último audio y del informe anotado (29-10-2026)

Se contrastó la transcripción completa de Audio3 con las nueve páginas anotadas. Se detectó que la similitud de conjuntos ya utilizada carecía de nombre y referencia explícitos en el informe: se identifica como Jaccard, con fuente, denominador y distinción entre la convención matemática para conjuntos vacíos y el valor no definido informado por este estudio cuando no hay señales positivas. No se cambia su implementación ni se añade un índice propio.

Se concretó el procedimiento pendiente de revisión de categorías: método publicado de cada fuente, actualización, dependencia entre listas, evidencia por dominio y tratamiento de discrepancias. El diagrama distingue resolución local o remota del destino y deja de asociar el filtro al túnel VPN. Se simplificó la explicación del intercambio OONI y se retiró del documento de criterios operativos un estado obsoleto de autenticación de GitHub.

Se mantienen la estructura de ocho secciones y once subapartados, las conclusiones vacías y la distinción entre avance documental y trabajo experimental. La validación semántica, inventario definitivo, configuración de VPN/proxies, mediciones y contraste OONI siguen pendientes.


## Redacción directa — 29-10-2026

Se simplificaron el pie de la figura 3, la explicación del plan, la revisión de categorías y varias frases sobre comparación y registro de respuestas. Se reemplazaron expresiones abstractas por acciones concretas, conservando las fuentes, las definiciones técnicas, la estructura y la separación entre lo previsto y lo ejecutado. No se modificaron datos, métodos de cálculo ni resultados.


## Piloto y corrección de EDE 18 — 30-10-2026

Se preparó un piloto separado de 50 dominios, con evidencias documentales preliminares, y se comprobaron UDP y TCP con controles técnicos en seis perfiles. El piloto compara dos perfiles de Cloudflare por TCP, registrando condiciones y límites. Las categorías continúan pendientes de validación final; los 2.000 candidatos no se presentan como revisados.

Se detectó que EDE 18 podía interpretarse como bloqueo aun con direcciones válidas. Se corrigió la regla conforme al RFC 8914 y se añadieron pruebas de regresión, incluida la reclasificación en una base nueva que conserva los mensajes originales. No se atribuyen estas observaciones a una nueva reunión del profesor.

## Precisión del diseño y del piloto — 30-10-2026

Se explicita que los perfiles activos no cubren apuestas ni armas y se exige política, plan, configuración y controles antes de evaluar acierto por categoría. CleanBrowsing configurable figura como candidato documental, sin contratación ni mediciones. Se identifican los resolutores de referencia y los cuatro dominios técnicos de calibración. Se distingue documentación del proveedor de evidencia reproducible de una huella local; `::` conserva su alcance exclusivo del piloto.

Se corrige la interpretación de Kappa/Jaccard frente a un perfil sin bloqueos y se añade la contingencia por dominio estable (A: 46/4; AAAA: 9/1, con 40 excluidos). No se modifican las medidas ni sus mensajes. Se verifican los 14 solapamientos adulto/phishing del inventario. Se aclara Cisco_Umbrella como etiqueta histórica, se reduce FINSIN en antecedentes, se adelanta la pregunta del estudio y se retiran alusiones a cuotas y márgenes de versiones previas. Referencias se incorpora al índice; se corrige la fecha duplicada y la etiqueta del diagrama. El plan queda como secuencia sin fechas confirmadas, con numeración coherente; las conclusiones siguen vacías y comparten página con el cierre del desarrollo.
