from fastapi import FastAPI , UploadFile, File, HTTPException
import csv
from io import StringIO
import time
import httpx
from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4
from fastapi import Depends
from sqlalchemy.orm import Session
from db import SessionLocal

app = FastAPI(title="Automation Tasks API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

guardar_urls = []
runs = []  # historial de ejecuciones

@app.get("/health")
def health():
    return {"status": "ok"}


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


    # Limpio la lista global antes de cargar nuevos datos
    guardar_urls.clear()

   
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
@app.get("/urls")
def list_urls():
    return guardar_urls 


# Endpoint para ejecutar el chequeo HTTP de las URLs
@app.post("/run-check")
async def run_check(timeout_seconds: float = 5.0) -> List[Dict[str, Any]]:
    """
    Aquí ejecuto un chequeo HTTP sobre todas las URLs que he cargado previamente con el CSV.
    La idea es devolver para cada URL:
    - si responde bien (ok)
    - el status_code
    - el tiempo que tarda en responder (time_ms)
    - y si falla, el error correspondiente
    """

    # Si el usuario no ha subido todavía un CSV, no tiene sentido ejecutar nada,
    # así que corto aquí y devuelvo un error .
    if not guardar_urls:
        raise HTTPException(
            status_code=400,
            detail="No hay URLs cargadas. Primero sube un CSV."
        )

    # Aquí iré guardando el resultado de cada URL en forma de lista de diccionarios
    results: List[Dict[str, Any]] = []

    # Creo un cliente HTTP asíncrono para hacer las peticiones sin bloquear el servidor
    # follow_redirects=True -> por si una URL redirige (por ejemplo http -> https)
    # timeout=timeout_seconds -> para no quedarme esperando si la URL está mal
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout_seconds
    ) as client:

        # Recorro todas las URLs que tengo cargadas en memoria
        for item in guardar_urls:
            # Saco el nombre y la url, y les hago strip para limpiar espacios
            name = item.get("name", "").strip()
            url = item.get("url", "").strip()

            # Empiezo a medir el tiempo antes de lanzar la petición
            start = time.perf_counter()
            try:
                # Hago la petición GET a la URL
                resp = await client.get(url)

                # Calculo el tiempo total en milisegundos
                elapsed_ms = int((time.perf_counter() - start) * 1000)

                # Guardo el resultado si la petición fue correcta
                # Considero ok cualquier status entre 200 y 399
                results.append({
                    "name": name,
                    "url": url,
                    "ok": 200 <= resp.status_code < 400,
                    "status_code": resp.status_code,
                    "time_ms": elapsed_ms,
                })

            except httpx.RequestError as e:
                # Si hay un fallo de red (DNS, timeout, conexión, etc.)
                # también mido el tiempo y guardo el error para saber qué pasó
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                results.append({
                    "name": name,
                    "url": url,
                    "ok": False,
                    "status_code": None,
                    "time_ms": elapsed_ms,
                    "error": str(e),
                })

    # Devuelvo la lista final con los resultados de todas las URLs
    return results


@app.post("/runs")
async def crear_run():
    resultado = await run_check(timeout_seconds=5.0)

    run = {
        "id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat() + "Z", 
        "count": len(resultado) ,
        "resultado": resultado
    }

    runs.append(run)
    return run


@app.get("/runs")
def lista_runs():
    return [
        {"id": r["id"], "created_at": r["created_at"], "count": r["count"]}
        for r in runs
    ]


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    for r in runs:
        if r["id"] == run_id:
            return r
    raise HTTPException(status_code=404, detail="Run no encontrado")