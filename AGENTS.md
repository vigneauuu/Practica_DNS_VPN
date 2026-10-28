# Reglas de trabajo de la práctica

Este repositorio corresponde a la práctica de Matías Vigneau Andrades, dirigida por Nicolás Boettcher. Antes de editar el informe, la metodología o el código, leer `docs/criterios_profesor.md` y la entrada más reciente de `docs/reuniones/`.

## Autoría y versiones

- El autor del informe es Matías Vigneau Andrades. No agregar coautores, agradecimientos de asistencia, marcas de generación ni trailers `Co-authored-by` sin una instrucción explícita del usuario.
- Publicar los cambios autorizados en la cuenta y repositorio de Matías: `vigneauuu/Practica_DNS_VPN`. Verificar autor y contenido del commit antes de publicar. No modificar la autoría de commits históricos.
- Mantener las fuentes del informe en `docs/informe/` coherentes con el proyecto de Overleaf. Comprobar compilación y revisar el PDF después de cambios de contenido o diagramas.
- Conservar la trazabilidad de las correcciones. No sobrescribir ni recodificar los resultados históricos como si procedieran del diseño nuevo.

## Criterios académicos permanentes

- Toda afirmación externa verificable requiere una fuente pertinente; preferir el documento original. Comprobar que la fuente respalda la afirmación concreta.
- Justificar decisiones antes de utilizarlas: antecedentes → problema → objetivos → método → evidencia → conclusiones.
- Diferenciar resolución DNS, protección PDNS, transporte VPN, intermediación proxy, categorización y decisión de bloqueo.
- No inferir filtrado a partir de NXDOMAIN, REFUSED, NODATA, timeout o HTTP 403 sin evidencia suficiente. Mostrar errores, incertidumbre y cobertura.
- No confundir acuerdo entre servicios con eficacia ni popularidad con benignidad. No inventar umbrales, tamaños muestrales o márgenes de error.
- Documentar perfil, configuración, recorrido de las consultas, corpus, parámetros y condiciones de cada ejecución.
- No presentar candidatos como categorías validadas ni funciones previstas como ya implementadas o probadas.
- Las nuevas indicaciones del profesor se registran con fecha y procedencia. Distinguirlas de interpretaciones y decisiones propias. Verificar técnicamente cualquier formulación ambigua.

## Continuidad y comprobación

- Registrar cada reunión con la plantilla de `docs/reuniones/`. Actualizar los criterios cuando una indicación tenga alcance permanente; registrar cambios y excepciones sin borrar el historial.
- Ejecutar las pruebas pertinentes del proyecto tras modificar medición, clasificación o análisis. Usar controles técnicos documentados para calibrar la red; no ejecutar el corpus completo de forma implícita.
- Los audios, fotografías originales, credenciales, contextos privados y mediciones detalladas permanecen fuera del contenido público salvo autorización específica. Publicar solo documentación y extractos adecuados a su finalidad.
- Pendientes de contexto: la grabación originalmente llamada Audio1 fue subida por error y falta su reemplazo; el contenido de Gemini aún no pudo recuperarse. Esto no impide aplicar las correcciones ya documentadas de los audios 2 y 3.

- Para traspasar entre herramientas, leer y actualizar `docs/CONTINUIDAD.md`. El contexto privado de la carpeta superior se describe en `EMPEZAR_AQUI.md`. Mantener conclusiones vacías mientras la práctica esté en curso, según instrucción de Matías del 27 de octubre de 2026.

- Leer también `docs/que_quiere_profesor.md` y `docs/diseno_estudio.md`: meta de 2.000 únicos revisados, amenazas separadas del alcance parental y distinción entre práctica y tesis. No inflar el corpus para anunciar esa meta como cumplida.
