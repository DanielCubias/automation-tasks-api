from fastapi import FastAPI

app = FastAPI(title="Automation Tasks API")

@app.get("/health")
def health():
    return {"status": "ok"}
