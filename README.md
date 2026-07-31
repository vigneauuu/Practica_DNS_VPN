# 🛡️ Evaluación Comparativa de Filtrado DNS

*Análisis de consistencia en la categorización de dominios mediante métricas de acuerdo inter-juez.*

![Python](https://img.shields.io/badge/PYTHON-3.10+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLITE-DATABASE-003B57?logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/STATUS-EJECUCIÓN%20DE%20PRUEBAS-brightgreen)

> **Nota:** Proyecto desarrollado en el marco de la **Práctica I** para la carrera de Ingeniería Civil Informática. La herramienta automatizada mide el nivel de consistencia y divergencia en resolutores DNS, servicios VPN y proxies.

---

## 📑 Tabla de Contenidos

1. [🎯 Objetivo del Proyecto](#objetivo-del-proyecto)
2. [📁 Arquitectura del Repositorio](#arquitectura-del-repositorio)
3. [📊 Dataset y Fuentes](#dataset-y-fuentes)
4. [🚀 Instrucciones de Uso](#instrucciones-de-uso)
5. [🎓 Contexto Académico](#contexto-académico)

---

## 🎯 Objetivo del Proyecto

El ecosistema actual de bloqueo de dominios (aplicado por ISPs, controles parentales y redes corporativas) carece de estándares unificados. El objetivo principal es **medir empíricamente el nivel de acuerdo técnico** frente a diversas categorías de contenido utilizando el **coeficiente Kappa de Cohen**, para determinar si depender de un único servicio garantiza un filtrado efectivo.

## 📁 Arquitectura del Repositorio

El proyecto sigue un patrón de diseño limpio, separando la ingesta de datos, la lógica de red y la documentación:

```
Practica_DNS_VPN
├── dataset/         # CSVs depurados (2000 dominios en total)
├── docs/            # Informe técnico en LaTeX y recursos visuales
├── scripts/         # Core del proyecto
│   ├── motor_evaluacion.py   # Script principal de consultas automatizadas
│   └── procesar_*.py         # Scripts de extracción y limpieza de fuentes
├── .gitignore       # Reglas de exclusión (protección de la DB local)
└── README.md        # Documentación del repositorio
```

## 📊 Dataset y Fuentes

Para asegurar rigor y garantizar la vigencia de las pruebas, se construyó un dataset propio estructurado en 5 categorías críticas (400 dominios cada una), extraídas de repositorios internacionales y gubernamentales.

| Categoría | Fuente Principal | Descripción |
|---|---|---|
| Tráfico Benigno | [Tranco List](https://tranco-list.eu/) | Dominios top globales (Grupo de control). |
| Apuestas/Casinos | SCJ Chile & StevenBlack | Sitios de apuestas no autorizados/ilegales. |
| Adultos | UT1 Capitole Blacklists | Filtrado estándar para control parental. |
| Armas/Violencia | UT1 Capitole Blacklists | Venta de armamento y contenido explícito. |
| Phishing/Malware | Phishing.Database | Amenazas volátiles y dominios recientes. |

## 🚀 Instrucciones de Uso

### 1. Clonar e Instalar

Asegúrate de tener Python 3.10 o superior instalado en tu entorno.

```bash
# Clonar el repositorio (si aplica)
git clone https://github.com/tu-usuario/tu-repo.git

# Instalar dependencias de red
pip install dnspython
```

### 2. Ejecutar el Motor de Consultas

El motor está diseñado para ser tolerante a fallos de red (timeouts) y procesar de forma ininterrumpida.

```bash
python scripts/motor_evaluacion.py
```

> ⚠️ **Importante:** Al finalizar la ejecución, los resultados se almacenarán en `resultados.db` (SQLite). Por políticas de seguridad y volumen de datos, este archivo es ignorado por Git de forma predeterminada.

## 🎓 Contexto Académico

- **Autor:** Matías Vigneau Andrades
- **Profesor Guía:** Nicolás Boettcher
- **Institución:** Universidad Diego Portales (UDP)
- **Facultad:** Facultad de Ingeniería y Ciencias (Escuela de Informática y Telecomunicaciones)