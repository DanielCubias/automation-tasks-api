from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.db.db import SessionLocal
from app.db.models import URLList

from app.services.services import ejecutar_run_para_lista

scheduler = AsyncIOScheduler()


async def job_ejecutar_runs_automaticos():
    db: Session = SessionLocal()
    try:
        listas = db.query(URLList).all()
        for l in listas:
            try:
                await ejecutar_run_para_lista(db=db, list_id=l.id, timeout_seconds=5.0)
            except Exception as e:
                print(f"[SCHEDULER] Error en lista {l.id}: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        job_ejecutar_runs_automaticos,
        IntervalTrigger(seconds=30),  # prueba rápida
        id="auto_runs",
        replace_existing=True
    )
    scheduler.start()
    print("[SCHEDULER] Iniciado (cada 30s)")


def shutdown_scheduler():
    scheduler.shutdown()
    print("[SCHEDULER] Parado")
