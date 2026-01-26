# API de Tareas Automatizadas

Sistema backend construido con FastAPI para automatizar tareas repetitivas utilizando procesos en segundo plano.

## 🚀 Características (MVP)
- Subida de archivos CSV con URLs  
- Comprobaciones HTTP automatizadas  
- Ejecución de tareas en segundo plano  
- Registros de ejecución y resultados  

## 🛠️ Stack Tecnológico
- Python  
- FastAPI  
- HTTPX  
- *(Próximamente)* Celery + Redis  
- *(Próximamente)* PostgreSQL  

## ▶️ Cómo ejecutarlo
```bash
uvicorn main:app --reload
