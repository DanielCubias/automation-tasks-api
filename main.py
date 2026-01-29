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
async def crear_run(list_id: str,timeout_seconds: float = 5.0,db: Session = Depends(get_db)
):
    """Ejecuta un chequeo HTTP sobre una lista de URLs y guarda el resultado en BD"""
    
    # Verifico que la lista exista
    url_list = db.query(URLList).filter(URLList.id == list_id).first()
    if not url_list:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    
    # Obtengo todas las URLs de esa lista
    urls = db.query(URL).filter(URL.url_list_id == list_id).all()
    if not urls:
        raise HTTPException(status_code=400, detail="No hay URLs en esta lista")

    # Creo el registro del Run
    run = Run(
        id=str(uuid4()),
        url_list_id=list_id,
        created_at=datetime.utcnow(),
        count=len(urls)
    )
    db.add(run)
    
    # Ejecuto el chequeo HTTP
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_seconds) as client:
        for url_obj in urls:
            start = time.perf_counter()
            try:
                resp = await client.get(url_obj.url)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                result = RunResult(
                    id=str(uuid4()),
                    run_id=run.id,
                    name=url_obj.name,
                    url=url_obj.url,
                    ok=200 <= resp.status_code < 400,
                    status_code=resp.status_code,
                    time_ms=elapsed_ms,
                )
                db.add(result)
                
            except httpx.RequestError as e:
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                result = RunResult(
                    id=str(uuid4()),
                    run_id=run.id,
                    name=url_obj.name,
                    url=url_obj.url,
                    ok=False,
                    status_code=None,
                    time_ms=elapsed_ms,
                    error=str(e)
                )
                db.add(result)
    
    db.commit()
    
    return {
        "id": run.id,
        "created_at": run.created_at.isoformat() + "Z",
        "count": run.count,
        "list_id": list_id
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