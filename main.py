from fastapi import FastAPI , UploadFile, File, HTTPException
import csv
from io import StringIO

app = FastAPI(title="Automation Tasks API")

guardar_urls = []

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
