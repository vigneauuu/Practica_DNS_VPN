# Evaluación Comparativa de Filtrado DNS, VPN y Proxies 🛡️

Proyecto desarrollado en el marco de la **Práctica I** para la carrera de Ingeniería Civil Informática (Universidad Diego Portales). 

Este repositorio contiene la herramienta automatizada encargada de medir el nivel de consistencia y divergencia en la categorización de dominios entre distintos resolutores DNS, servicios VPN y proxies.

## 🎯 Objetivo del Proyecto
Medir empíricamente el nivel de acuerdo técnico frente a diversas categorías de contenido (ej. Tráfico Benigno, Apuestas, Contenido para Adultos, Phishing) utilizando el **coeficiente Kappa de Cohen**.

## 📂 Arquitectura del Repositorio

El proyecto está estructurado lógicamente para separar la ingesta de datos, la lógica de automatización y la documentación:

- `dataset/`: Contiene los archivos CSV depurados con los 2000 dominios de prueba (400 por categoría), extraídos de fuentes primarias como Tranco, SCJ, StevenBlack y UT1 Capitole.
- `scripts/`: Ejecutables en Python.
  - `procesar_*.py`: Scripts de recolección y limpieza de datos.
  - `motor_evaluacion.py`: Motor principal automatizado basado en `dnspython` e integración con base de datos.
- `docs/`: Documentación técnica e informe LaTeX del proyecto.

## ⚙️ Tecnologías Utilizadas
- **Lenguaje:** Python 3.10+
- **Librerías Core:** `dnspython`, `csv`, `os`
- **Base de Datos:** SQLite (`resultados.db` - Ignorada en el control de versiones por seguridad)
- **Documentación:** LaTeX

## 🚀 Ejecución del Motor de Consultas
Para iniciar la batería masiva de pruebas y generar la base de datos local:

1. Instalar dependencias requeridas:
   pip install dnspython

2. Ejecutar el motor de evaluación:
   python scripts/motor_evaluacion.py


*Nota: La base de datos resultante (`resultados.db`) es gestionada localmente y excluida del repositorio mediante `.gitignore` para mantener la integridad de los datos masivos.*

---
**Autor:** Matías Vigneau Andrades  
**Profesor Guía:** Nicolás Boettcher  
**Universidad Diego Portales - EIT**