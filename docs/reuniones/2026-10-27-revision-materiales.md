# Revisión de materiales y decisiones de trabajo

Fecha de revisión: 27 de octubre de 2026. No corresponde a una nueva reunión celebrada en esta fecha: sintetiza los audios 2 y 3 y el PDF recibidos. La fecha original de esas conversaciones no está confirmada.

## Observaciones del profesor

Consultar `../criterios_profesor.md` para el detalle y las marcas de tiempo: fundamentar cantidades, categorías y métricas antes de objetivos; precisar PDNS y recorridos VPN/proxy; validar el corpus; revisar OONI y fuentes alternativas; conservar evidencia; separar acuerdo de eficacia. No se identificó una cuota de páginas ni un tamaño definitivo prescrito. Las transcripciones automáticas requieren contraste con el audio si surge una ambigüedad.

## Decisiones de implementación

- Núcleo de seis perfiles por contraste de políticas, ampliable después de calibración; no se atribuye esta cifra al profesor.
- Corpus heredado auditado: 1.960 filas, 94 inválidas, 1.866 membresías y 1.852 dominios únicos. Todos pendientes de validación semántica. No se establece una cuota de 400 por categoría.
- Paquete Python con mensajes completos, controles, errores separados y análisis con cobertura; código anterior conservado en legacy.
- Dos diagramas y antecedentes desarrollados antes de los objetivos.

## Indicaciones de Matías en esta revisión

Cambiar estructura, arquitectura y nombres cuando lo requiera la coherencia. Dejar conclusiones vacías mientras la práctica no termine.

## Verificación y pendientes

21 pruebas automatizadas aprobadas. Calibración limitada de ocho observaciones: cuatro errores de red del perfil familiar, sin inferir bloqueo. Faltan validación semántica, conectividad de todos los perfiles, VPN/proxies reales y contraste OONI.
