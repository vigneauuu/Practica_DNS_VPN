# Criterios permanentes de revisión

Actualización: 28 de octubre de 2026. Base: observaciones de Nicolás Boettcher en los audios 2 y 3 y en el informe impreso. Las marcas de tiempo son aproximadas. Estos criterios resumen las observaciones; no son citas textuales ni una rúbrica institucional inventada.

## Referencias y antecedentes

1. **La referencia debe respaldar la frase concreta.** Identificar autor o institución, documento, fecha y enlace al documento original. Un portal institucional genérico no acredita un decreto, una cifra o una nómina. Audio 2, 05:02–05:46; audio 3, 01:44–02:43.
2. **Explicar la pertinencia del antecedente.** Cuando se mencione una norma, plan o estudio, precisar qué propone o mide y cómo se relaciona con la práctica. Audio 2, 00:06–00:44; audio 3, 00:03. Aplicación reafirmada por Matías el 28-10-2026: no basta con llamar a una publicación «antecedente relacionado»; explicar su objeto, el aporte concreto al diseño y las diferencias que impiden trasladar automáticamente datos o métricas. Esta precisión es editorial, no una nueva cita del profesor.
3. **No convertir una búsqueda incompleta en una afirmación universal.** Distinguir «no se encontró en las fuentes revisadas» de «no existe» o «ningún proveedor lo publica». Audio 2, 01:03–02:12.
4. **Usar fechas y contextos identificables.** Evitar antecedentes atemporales y fuentes secundarias cuando exista el documento primario. No completar datos bibliográficos por suposición.

## Coherencia del diseño

5. **Cada decisión debe tener antecedentes.** El lector debe comprender de dónde salen la cantidad de sitios, las categorías, los servicios y las métricas antes de encontrarlos como objetivos. Audio 2, 02:19–03:58; audio 3, 12:17–13:37 y 17:02–18:00.
6. **Delimitar qué se evalúa.** Diferenciar el protocolo DNS de un servicio de resolución y de la función PDNS; justificar la incorporación de VPN y proxies por su configuración efectiva. Audio 3, 02:43–04:47 y 06:36–11:44.
7. **Mostrar el aporte y la carga real.** Explicar selección, validación, controles y análisis. Evitar describir toda la práctica como un script que consulta una lista. Audio 2, 05:48–06:59; audio 3, 31:35–32:35.
8. **Definir los términos medibles.** Indicar qué significa robustez, consistencia, bloqueo, categoría o amenaza activa y qué evidencia permitirá concluir algo. Audio 2, 04:22–04:53 y 06:59–07:14.

## Escritura y estructura

9. **El estado del arte explica lo existente.** Los procedimientos nuevos se desarrollan en metodología; lo efectivamente implementado y observado, en desarrollo y resultados. Audio 3, 29:55–31:35.
10. **Desarrollar los apartados y evitar fragmentación innecesaria.** Audio 3, 27:26–28:29: el profesor cuestiona los subcapítulos de unas cinco líneas y espera varios párrafos con desarrollo. No establece una prohibición de numerar ni una cantidad máxima de subapartados. Aplicación editorial, reafirmada por Matías el 28-10-2026: reunir puntos breves y relacionados en un relato continuo; conservar subtítulos solo para temas con función propia y desarrollo suficiente. No sustituir cada número por un título sin numeración ni añadir relleno para cumplir una cuota de páginas.
11. **Usar lenguaje técnico preciso y formal.** Definir reescritura de respuestas, campos DNS, TTL, banderas y direcciones especiales. No sustituir una explicación por una sigla. Audio 3, 00:41–01:44, 14:07–16:33 y 32:35–33:10.
12. **Representar el recorrido cuando haya varias capas.** El diagrama debe mostrar cliente, ámbito del navegador o sistema, túnel o proxy y lugar de resolución. Audio 3, 28:29–29:55.

## Datos y herramientas

13. **Validar y justificar el corpus.** La extracción automatizada no acredita que cada sitio pertenezca a la categoría declarada. Conservar evidencia, supervisión y alternativas de fuentes. Audio 3, 24:39–26:31 y 33:38–35:24.
14. **Examinar herramientas y trabajos existentes.** Revisar OONI para mediciones y contraste, y la fuente chilena de phishing mencionada en la reunión. Audio 3, 23:32–25:03 y 34:20. Se identificó probablemente como FINSIN y Ricardo Monreal Llop; esta identificación se documenta con la fuente, sin afirmar una disponibilidad actual de dataset que aún no se comprobó.
15. **Verificar la configuración, no asumirla.** Una VPN limitada al navegador no garantiza que un programa de consola use ese túnel o resolutor. Audio 3, 28:29–29:28.

## Decisiones de implementación adoptadas

Estas reglas operativas responden a las observaciones, pero no se atribuyen como instrucciones literales del profesor:

- Conservar categorías múltiples y un estado de revisión por dominio.
- Usar estados de evidencia separados y controles temporales, con análisis por par y cobertura explícita.
- Mantener Kappa como descriptor complementario sin un umbral universal de eficacia; retirar el índice propio no justificado.
- Usar seis perfiles públicos para contrastar configuraciones; agregar VPN y proxies al cumplir los requisitos de documentación.
- Presentar el corpus heredado como candidatos y los resultados previos como exploratorios.
- Diferenciar DNSSEC de cifrado del transporte según RFC 4033; resolver cualquier ambigüedad técnica de las notas mediante fuentes primarias.

## Indicaciones adicionales de Matías (27 de octubre de 2026)

- Mantener el apartado de conclusiones vacío mientras la práctica esté en curso. Los resultados parciales se describen como avance en desarrollo, sin adelantar conclusiones finales.
- Explicar en antecedentes y motivación de dónde surgen categorías, cantidad de perfiles, tamaño del corpus y métricas, antes de encontrarlos en objetivos o método. Las cantidades actuales son auditadas o decisiones justificadas, no cuotas atribuidas al profesor.
- Solicitud de Matías del 28 de octubre de 2026: conservar la presentación base de la plantilla compartida y la estructura del informe, incluido Resultados Esperados como apartado separado. Las correcciones de contenido no requieren rediseñar la portada, los márgenes ni la bibliografía. Esta regla se registra como decisión de presentación, no como una observación de una reunión nueva.
- Redacción, solicitud de Matías del 28 de octubre de 2026: preferir expresiones directas, como «conexiones mediante VPN o proxy», cuando no se pierde precisión. Definir los términos técnicos necesarios y evitar títulos o frases que añadan complejidad sin explicar una operación, evidencia o límite concreto. Conservar el vocabulario propio de protocolos y métricas cuando sea necesario para describirlos correctamente.

## Seguimiento de nuevas indicaciones (28 de octubre de 2026)

- Solicitud de Matías: revisar en cada intercambio si hay una indicación duradera que incorporar. Registrar fuente y fecha; no convertir consultas, comentarios de estado o decisiones temporales en reglas del profesor.
- Mantener diferenciadas las observaciones docentes, las preferencias del estudiante y las decisiones de implementación. Una síntesis o una interpretación no equivale a una instrucción literal ni a aprobación del informe.
- Antes de una entrega, volver a contrastar texto, referencias y diagramas con las correcciones originales; comprobar que los cambios no introducen conceptos sin antecedentes ni describen funciones o resultados aún pendientes como terminados. Mantener una matriz que relacione observación, lugar del informe, comprobación y estado (aplicado, parcial o pendiente); registrar una regla no basta para darla por cumplida. Revisar también la estructura del índice y la extensión real de cada bloque en el PDF.
- El traslado desde Windows a Linux conserva archivos y registros históricos; las nuevas mediciones deben identificar su entorno y configuración. No mezclar ejecuciones ni presentar la recuperación como validación experimental.
- El cronograma debe separar etapas previstas de avance comprobado y fechas confirmadas. Una prórroga informada o propuesta no acredita por sí sola una nueva fecha de cierre aprobada.

## Actualización después de cada reunión

1. Crear una entrada en `docs/reuniones/` usando la plantilla.
2. Registrar cada observación con su procedencia, sección afectada, cambio y criterio de cierre.
3. Añadir aquí solo criterios que deban repetirse en trabajos futuros.
4. Si una indicación nueva cambia una anterior, anotar ambas fechas y cuál rige; no borrar la historia.
5. Actualizar `docs/correcciones.md` y la documentación de ejecución cuando corresponda.

## Contexto anterior: audios del anteproyecto incorporados el 27-10-2026

Estas grabaciones son anteriores a Audio2 y Audio3, según Matías. Ver `que_quiere_profesor.md` para la matriz completa.

16. **Diferenciar contenido parental de amenazas.** Primer audio 01:18–01:44 y 03:45–04:58: centra contenido adulto, apuestas y armas y pide no ampliar hacia phishing. El segundo, 06:16–06:46, permite estudiar categorías según las funciones encontradas. Se adopta alcance principal parental y amenazas históricas separadas; no inferir revocación solo de una mención posterior de FINSIN.
17. **Medir el bloqueo indebido, además del bloqueo deseado.** Primer audio 08:21–11:43: revisar sitios categorizados y contenido educativo permitido; no convertir una lista popular en verdad de benignidad.
18. **Distinguir práctica y tesis.** Segundo audio 00:57–02:11 y 05:47–06:16: la práctica recopila fuentes, automatiza consultas y analiza comparaciones; diseñar un algoritmo nuevo se plantea como posible trabajo posterior.
19. **Justificar también las herramientas.** Primer audio 14:01–15:22: Python o una heurística no deben aparecer sin razón técnica ni antecedentes. No afirmar popularidad en la literatura sin verificarla.
20. **La latencia no sustituye a la calidad de categorización.** Primer audio 20:18–21:17: TTL y tiempos pueden conservarse como contexto; no usarlos para declarar qué filtro clasifica mejor.
21. **Los ejemplos no son cuotas ni resultados.** Las cifras hipotéticas de los audios no establecen umbrales ni tamaño obligatorio. La meta de 2.000 únicos revisados es preferencia de Matías; su configuración y estado real se documentan en `diseno_estudio.md`.

Las conclusiones permanecen vacías. Los audios antiguos no se presentan como una nueva aprobación del diseño actual.

22. **Describir el alcance de la búsqueda.** Primer audio 27:08: no afirmar revisión exhaustiva sin bases, términos, fechas, criterios de inclusión y exclusión documentados. Segundo 07:12–08:03: distinguir planes y ampliar el inventario y los datos con justificación, sin transformar sus ejemplos en cuotas.

23. **Distinguir el servicio evaluado de la herramienta de medición.** Audio2 00:49–00:58 y primer audio del anteproyecto 12:10–12:37: el servicio de resolución o protección es el objeto evaluado; el programa Python es la herramienta utilizada para observarlo. No atribuir al proveedor características del programa ni presentar el desarrollo del programa como toda la comparación.
