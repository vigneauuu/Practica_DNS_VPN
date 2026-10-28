# Continuar el proyecto desde cualquier herramienta

Esta guía es compartible en el repositorio. Los materiales de trabajo privados se conservan en la carpeta superior y no deben subirse al repositorio público.

## Lectura inicial obligatoria

1. `AGENTS.md` y `docs/criterios_profesor.md`.
2. El registro más reciente de `docs/reuniones/`.
3. `docs/correcciones.md`, `README.md` y `docs/informe/Practica1.tex`.
4. `git status`, historial reciente y diferencias locales, antes de editar.

## Estado de la versión del 27 de octubre de 2026

Informe reorganizado en antecedentes y motivación, fundamentos y trabajos, problema y objetivos, alcances, método, implementación, plan y conclusiones. El último apartado está intencionadamente vacío. Las decisiones de tamaño, categorías, perfiles y medidas se motivan antes de objetivos. Dos diagramas representan recorridos y flujo de evidencia.

Python se organiza en `src/pdns_lab/`; CLI `pdns-lab`; dependencias en `pyproject.toml` y versiones probadas en `requirements-dev.lock`; pruebas en `tests/`. El entorno local es `.venv/`. El código anterior está en `legacy/`; `resultados.db` es histórico y exploratorio.

La auditoría registra 1.960 filas originales, 94 rechazadas y 14 solapamientos: 1.852 candidatos únicos, **no un corpus validado**. Los seis perfiles son un contraste experimental documentado, no una cuota del profesor. La calibración no permite comparar eficacia. Hay 21 pruebas locales aprobadas; ello no acredita rendimiento de los servicios ni ejecución de CI remota.

## Siguiente trabajo

1. Revisar la matriz de correcciones y completar fuentes y criterios de revisión de categorías. Determinar con evidencia qué categorías y cantidades se conservan; excluir lo que no pueda justificarse.
2. Resolver y documentar conectividad/calibración de perfiles sin modificar la red o instalar VPN implícitamente. No ejecutar el corpus completo por defecto.
3. Documentar configuraciones reales de VPN/proxy y condiciones de OONI antes de mediciones comparables.
4. Ejecutar el corpus revisado, informar cobertura y estabilidad y analizar por política. Completar conclusiones solo al finalizar.
5. Registrar nuevas reuniones y actualizar criterios y esta guía con cambios comprobados.

Para publicar: comprobar identidad de Matías, cambios y estado remoto; obtener acceso normal a su cuenta y publicar los commits pendientes. No agregar coautorías, no reescribir historia ni forzar push. El acceso de escritura estaba bloqueado y Matías pospuso el inicio de sesión hasta estar en el computador.

## Cierre de cada sesión

Actualizar estado, pruebas realmente ejecutadas, archivos modificados, pendientes y bloqueos. Mantener sincronizadas las fuentes locales y Overleaf, verificando diferencias antes de sobrescribir cambios externos. No presentar decisiones de implementación como instrucciones literales ni aprobación del profesor.

## Actualización por audios del anteproyecto

Antes de continuar leer `docs/que_quiere_profesor.md`, `docs/diseno_estudio.md` y el registro de incorporación de audios antiguos. El alcance principal es parental; phishing queda como inventario histórico separado. Meta en `config/estudio.json`: 2.000 únicos revisados; no son 2.000 ya obtenidos. `pdns-lab study-plan` distingue inventario, candidatos en alcance y revisados; `corpus-select` no produce el corpus final si faltan validados. Estado: 1.852 en inventario histórico; 2.000 candidatos parentales en archivo separado, de ellos 1.466 heredados y 534 referencias de biblioteca UT1; cero validados. Faltan revisión y sustitutos de los que se descarten. Tres pruebas nuevas verifican construcción, selección, cantidad, trazabilidad y rechazo ante insuficiencia; total 24 aprobadas. No diseñar un algoritmo nuevo ni presentar ejemplos de los audios como resultados. Mantener conclusiones vacías.

Construcción final del inventario parental: `dataset/corpus-parental-candidatos.csv` contiene 2.000 únicos sin phishing; 534 son `referencia_biblioteca`, etiqueta de procedencia que no acredita benignidad ni educación. El corpus definitivo validado sigue pendiente. Ver `diseno_estudio.md`.
