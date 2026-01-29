# Automation Tasks API

API backend desarrollada con **FastAPI** para automatizar tareas repetitivas, comenzando por la monitorización de URLs a partir de archivos CSV.  
El sistema permite subir listas de URLs, ejecutar comprobaciones HTTP, guardar resultados y consultar el histórico de ejecuciones de forma persistente en **PostgreSQL**.

Este proyecto está orientado a demostrar automatización backend real, diseño de APIs y persistencia de datos.

---

## 🚀 Funcionalidades actuales

### 📄 Gestión de listas de URLs (CSV)
- Subida de archivos CSV con URLs.
- Validación de formato y columnas obligatorias (`name`, `url`).
- Persistencia de listas de URLs en base de datos.
- Cada CSV subido se almacena como una **URL List** identificada por un `list_id`.

### ⚙️ Ejecución de tareas (Runs)
- Ejecución manual de comprobaciones HTTP sobre una lista de URLs.
- Medición de:
  - Código de estado HTTP
  - Tiempo de respuesta (ms)
  - Errores de conexión
- Almacenamiento de cada ejecución como un **Run** con ID único.
- Persistencia de resultados individuales por URL.

### 📊 Consulta de resultados
- Listado de todas las listas de URLs cargadas.
- Listado de todas las ejecuciones realizadas.
- Consulta del detalle completo de una ejecución (resultados por URL).

---

## 🧱 Arquitectura actual

CSV -> FastAPI -> PostgreSQL
↓
HTTP checks
↓
Runs + Results


### Modelos principales
- **URLList**: representa un CSV subido.
- **URL**: URLs asociadas a una lista.
- **Run**: una ejecución de comprobación.
- **RunResult**: resultado individual por URL en una ejecución.

---

## 🛠️ Stack tecnológico

- **Python**
- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**
- **Docker / Docker Compose**
- **HTTPX** (peticiones HTTP asíncronas)

---

## 📦 Requisitos

- Python 3.10+
- Docker y Docker Compose
- PostgreSQL (vía Docker)

---

## ▶️ Puesta en marcha

### 1. Levantar la base de datos
```bash
docker compose up -d
```

### 2. Crear las tablas
```bash
python create_tables.py
```

### 3. Arrancar la API
```bash

uvicorn main:app --reload
```
Acceder a la documentación interactiva:

http://127.0.0.1:8000/docs


### Endpoints principales


### Listas de URLs

* POST /cargar_urls → Subir CSV

* GET /url-lists → Listar istas

### Ejecuciones

POST /runs?list_id={list_id} → Ejecutar run

GET /runs → Listar runs

GET /runs/{run_id} → Detalle de un run


### 📁 Ejemplo de CSV

name,url
Google,https://google.com
GitHub,https://github.com
FastAPI,https://fastapi.tiangolo.com


### 🎯 Objetivo del proyecto

Este proyecto tiene como objetivo:

Practicar automatización backend real.

Diseñar APIs REST limpias y mantenibles.

Trabajar con persistencia y trazabilidad de ejecuciones.

Simular sistemas de automatización utilizados en entornos profesionales.
