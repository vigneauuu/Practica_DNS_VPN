# Incorporación de dos audios anteriores del anteproyecto

Fecha de revisión: 27 de octubre de 2026. No es una reunión celebrada hoy. Matías indicó que las grabaciones son las primeras, anteriores al inicio de la práctica y a las correcciones Audio2/Audio3. La fecha original no está confirmada.

## Fuentes revisadas

- Primer audio de todos: 31 min 5 s; transcripción automática completa, con marcas de tiempo.
- Segundo audio de todos: 9 min 47 s; transcripción automática completa, con marcas de tiempo.
- Se contrastaron con los criterios de Audio2/Audio3 y el informe actual. Las transcripciones contienen errores y algunas repeticiones espurias; no se citan literalmente ni se infiere identidad de cada hablante mediante reconocimiento automático.

## Observaciones y decisiones

La matriz `../que_quiere_profesor.md` recoge fuente, criterio y aplicación. El primer audio centra control parental, pide retirar phishing, justificar referencias y herramientas, estudiar errores sobre contenido educativo y no presentar latencia como calidad. En el segundo, la comparación de fuentes y servicios y la automatización constituyen la práctica; proponer un algoritmo se orienta a una tesis posterior. La sugerencia inicial de estudiar algoritmos se interpreta con esta delimitación posterior, sin inventar un requisito de desarrollar uno.

Se pide un inventario amplio y justificado de datasets y puntos de filtrado, no limitarse a seis resolutores por conveniencia. El segundo audio 07:12–08:03 advierte que una versión gratuita puede no ofrecer los filtros de pago y que 500 dominios podrían ser pocos; ello no prescribe exactamente 2.000. El primero 27:08 requiere describir cómo se buscará antes de llamar exhaustiva a la revisión; 28:04–28:31 propone examinar sitios de apuestas identificados por medidas chilenas, cuya fuente concreta sigue pendiente. No se transforman las formulaciones legales del audio en hechos normativos sin comprobar el documento primario.

## Cambios aplicados

- Informe: foco parental, distinción de amenazas, contraste educativo, antecedentes de herramientas y referencia institucional relacionada con el equipo; límites de perfiles y carga de 2.000.
- `config/estudio.json`: meta 2.000 únicos revisados por preferencia de Matías, categorías de alcance y exclusiones.
- Planificador/selector: inventario, candidatos y revisados separados; selección exacta solo si hay datos suficientes. Pruebas con datos sintéticos claramente limitadas al software.
- Fuentes históricas conservadas; no rellenar 148 entradas ni alterar la cifra auditada.
- Reglas y continuidad actualizadas; conclusiones vacías.

## Verificación y pendientes

24 pruebas locales aprobadas. Plan real: 1.852 en inventario histórico; se construyeron 2.000 candidatos parentales (1.466 heredados y 534 de contraste UT1 liste_bu), cero revisados. Faltan validación y reemplazos de los descartados. La etiqueta armas es sospechosa de mezclar odio/violencia. Falta recuperar la tesis/corpus exactos, completar inventario y cobertura de servicios, validar categorías y medir. GitHub sigue sin acceso de escritura; autorización del usuario confirmada, integración 403 y navegador sin sesión. No se presenta publicación remota como realizada.

Construcción final del inventario parental: `dataset/corpus-parental-candidatos.csv` contiene 2.000 únicos sin phishing; 534 son `referencia_biblioteca`, etiqueta de procedencia que no acredita benignidad ni educación. El corpus definitivo validado sigue pendiente. Ver `diseno_estudio.md`.
