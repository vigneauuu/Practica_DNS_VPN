# Correcciones aplicadas y trabajo experimental pendiente

Actualización: 27 de octubre de 2026. Esta matriz distingue cambios de diseño e implementación de evidencia que todavía debe obtenerse. Las observaciones de las reuniones se resumen en [criterios_profesor.md](criterios_profesor.md).

| Observación | Cambio aplicado | Comprobación / estado |
|---|---|---|
| Objetivos sin antecedentes suficientes | Pregunta descriptiva sobre PDNS, objetivos alineados y alcances por perfil | Reescritura del informe y bibliografía específica |
| Confusión entre DNS, VPN y proxies | Definiciones, límites de cada capa y diagrama de recorridos | Dos diagramas TikZ incorporados; condiciones VPN/proxy documentadas |
| Hipótesis Kappa < 0,60 no fundamentada | Retirada; acuerdo, prevalencias y cobertura como descriptores separados de eficacia | Kappa no definido cuando corresponde; pruebas de casos degenerados |
| Índice propio sin justificación | Retirado de los objetivos y sustituido por descriptores explícitos | Tabla de contingencia, acuerdo y Jaccard con denominadores |
| Referencias genéricas y afirmaciones universales | Documentos identificables; eliminadas cifras y aseveraciones judiciales sin documento primario verificado | Las referencias no localizadas no se presentan como respaldo |
| DNSSEC confundido con cifrado | Distinción entre autenticidad/integridad y DoH/DoT | RFC 4033, RFC 8484 y RFC 7858 |
| Tamaño de muestra y exclusividad incorrectos | Auditoría de 1.960 filas, 94 rechazos y 14 solapamientos; 1.852 candidatos únicos | `dataset/corpus.audit.json`; categorías múltiples y procedencia por fila |
| Automatización presentada como validación | Estados pending/validated/excluded y evidencia con responsable y fecha | **Pendiente:** revisión semántica de 1.852 candidatos |
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

Las correcciones documentadas de los audios 2 y 3 están incorporadas en este avance; nuevas indicaciones se registrarán como una revisión posterior.

## Ajustes adicionales solicitados por Matías

Se desarrolló en antecedentes la razón de categorías, cantidades, perfiles y métricas antes de objetivos. Conclusiones queda vacío hasta finalizar la práctica. No hay una cuota de páginas ni un tamaño final de corpus acreditado por los audios revisados.

## Revisión de los audios antiguos del anteproyecto

Se añadió el foco parental y la separación de phishing, el contraste de contenido educativo permitido, la justificación de Python y la distinción práctica/tesis. Los perfiles instrumentados son iniciales: falta ampliar el inventario y acreditar cobertura por categoría. Ver `que_quiere_profesor.md`.

Meta de 2.000 únicos revisados en `config/estudio.json`, planificador y selector reproducible con bloqueo ante datos insuficientes. El inventario histórico conserva 1.852 candidatos. Se construyó un conjunto parental separado de 2.000: 1.466 heredados y 534 referencias universitarias UT1. Revisados: cero. La lista llamada armas requiere revisión de su significado; también las referencias de biblioteca requieren comprobar contenido y política esperada. Ver `diseno_estudio.md`.

Construcción final del inventario parental: `dataset/corpus-parental-candidatos.csv` contiene 2.000 únicos sin phishing; 534 son `referencia_biblioteca`, etiqueta de procedencia que no acredita benignidad ni educación. El corpus definitivo validado sigue pendiente. Ver `diseno_estudio.md`.
