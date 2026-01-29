from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from models import URLList, URL, Run, RunResult
from db import SessionLocal
import csv
from io import StringIO
import time
import httpx
from datetime import datetime
from uuid import uuid4
from APScheduler import start_scheduler, shutdown_scheduler
from services import ejecutar_run_para_lista


app = FastAPI(title="Automation Tasks API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Endpoint para cargar un archivo CSV con URLs
@app.post("/cargar_urls")
async def cargar_urls(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Primero valido que el archivo realmente sea un CSV
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="El archivo tiene que ser csv")

    # Leo el contenido del archivo de manera asíncrona
    content = await file.read()

    # Decodifico los bytes a texto UTF-8 para poder procesarlo
    decoded = content.decode("utf-8")

    # Uso DictReader para convertir cada fila del CSV en un diccionario
    reader = csv.DictReader(StringIO(decoded))

    # Defino las columnas obligatorias que debe tener el CSV
    required_columns = {"name", "url"}

    # Verifico que el CSV incluya las columnas necesarias
    if not required_columns.issubset(reader.fieldnames):
        raise HTTPException(
            status_code=400,
            detail="CSV debe de tener las columnas: name,url"
        )   
   # 1) Creo una lista (representa “este CSV subido”)
    url_list = URLList(
        id=str(uuid4()),
        name=file.filename,
        created_at=datetime.utcnow(),
    )
    db.add(url_list)

    # 2) Inserto todas las URLs asociadas
    count = 0
    for row in reader:
        db.add(URL(
            id=str(uuid4()),
            url_list_id=url_list.id,
            name=row["name"].strip(),
            url=row["url"].strip()
        ))
        count += 1
    
    db.commit()

    return {
        "message": "CSV guardado en base de datos",
        "list_id": url_list.id,
        "count": count
    }


# Endpoint para listar todas las URLs almacenadas

@app.get("/url-lists")
def listar_url_lists(db: Session = Depends(get_db)):
    lists = db.query(URLList).order_by(URLList.created_at.desc()).all()
    return [{"id": l.id, "name": l.name, "created_at": l.created_at.isoformat() + "Z"} for l in lists]


@app.post("/runs")
async def crear_run(list_id: str, timeout_seconds: float = 5.0, db: Session = Depends(get_db)):
    run = await ejecutar_run_para_lista(db=db, list_id=list_id, timeout_seconds=timeout_seconds)
    return {
        "id": run.id,
        "created_at": run.created_at.isoformat() + "Z",
        "count": run.count,
        "list_id": run.url_list_id
    }


@app.get("/runs")
def lista_runs(db: Session = Depends(get_db)):
    """Lista todos los runs ejecutados"""
    runs = db.query(Run).order_by(Run.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat() + "Z",
            "count": r.count,
            "list_id": r.url_list_id
        }
        for r in runs
    ]


@app.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    """Obtiene el detalle completo de un run específico"""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")

    results = db.query(RunResult).filter(RunResult.run_id == run_id).all()

    return {
        "id": run.id,
        "created_at": run.created_at.isoformat() + "Z",
        "count": run.count,
        "list_id": run.url_list_id,
        "resultado": [
            {
                "name": r.name,
                "url": r.url,
                "ok": r.ok,
                "status_code": r.status_code,
                "time_ms": r.time_ms,
                "error": r.error
            }
            for r in results
        ]
    }


@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    shutdown_scheduler()