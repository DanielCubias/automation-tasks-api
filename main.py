from fastapi import FastAPI , UploadFile, File, HTTPException
import csv
from io import StringIO
import time
import httpx
from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4

app = FastAPI(title="Automation Tasks API")

guardar_urls = []
runs = []  # historial de ejecuciones

@app.get("/health")
def health():
    return {"status": "ok"}


# Endpoint para cargar un archivo CSV con URLs
@app.post("/cargar_urls")
async def cargar_urls(file: UploadFile = File(...)):
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

    # Recorro cada fila del CSV y guardo solo los campos que necesito
    for row in reader:
        guardar_urls.append({
            "name": row["name"],
            "url": row["url"]
        })

    # Devuelvo un mensaje de éxito y la cantidad de URLs cargadas
    return {
        "message": "URLs uploaded successfully",
        "count": len(guardar_urls )
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
    resultado = await run_check(tiempo_segundos= 5.0)

    run = {
        "id": str(uuid4()),
        "created_at": datetime.utcnow().isoformat() + "Z", 
        "count": len(resultado) ,
        "resultado": resultado
    }

    runs.append(run)
    return run