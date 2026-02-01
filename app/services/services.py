import time
import httpx
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import URLList, URL, Run, RunResult


def limitando_runs(db: Session, url_list_id: str, max_runs: int = 200):
    total = db.query(Run).filter(Run.url_list_id == url_list_id).count()
    if total <= max_runs:
        return

    to_delete = total - max_runs

    old_run_ids = (
        db.query(Run.id)
        .filter(Run.url_list_id == url_list_id)
        .order_by(Run.created_at.asc())
        .limit(to_delete)
        .all()
    )
    old_ids = [row[0] for row in old_run_ids]

    if old_ids:
        db.query(Run).filter(Run.id.in_(old_ids)).delete(synchronize_session=False)
        db.commit()


def limitando_run_results(db: Session, max_rows: int = 1000):
    total = db.query(RunResult).count()
    if total <= max_rows:
        return

    to_delete = total - max_rows

    old_result_ids = (
        db.query(RunResult.id)
        .join(Run, Run.id == RunResult.run_id)
        .order_by(Run.created_at.asc())
        .limit(to_delete)
        .all()
    )
    old_ids = [row[0] for row in old_result_ids]

    if old_ids:
        db.query(RunResult).filter(RunResult.id.in_(old_ids)).delete(synchronize_session=False)
        db.commit()


async def ejecutar_run_para_lista(db: Session, list_id: str, timeout_seconds: float = 5.0) -> Run:
    # Verifico que la lista exista
    url_list = db.query(URLList).filter(URLList.id == list_id).first()
    if not url_list:
        raise HTTPException(status_code=404, detail="Lista no encontrada")

    # Obtengo las URLs
    urls = db.query(URL).filter(URL.url_list_id == list_id).all()
    if not urls:
        raise HTTPException(status_code=400, detail="No hay URLs en esta lista")

    # Creo el Run
    run = Run(
        id=str(uuid4()),
        url_list_id=list_id,
        created_at=datetime.utcnow(),
        count=len(urls)
    )
    db.add(run)

    # Ejecuto chequeos y guardo resultados
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_seconds) as client:
        for url_obj in urls:
            start = time.perf_counter()
            try:
                resp = await client.get(url_obj.url)
                elapsed_ms = int((time.perf_counter() - start) * 1000)

                db.add(RunResult(
                    id=str(uuid4()),
                    run_id=run.id,
                    name=url_obj.name,
                    url=url_obj.url,
                    ok=200 <= resp.status_code < 400,
                    status_code=resp.status_code,
                    time_ms=elapsed_ms,
                ))
            except httpx.RequestError as e:
                elapsed_ms = int((time.perf_counter() - start) * 1000)

                db.add(RunResult(
                    id=str(uuid4()),
                    run_id=run.id,
                    name=url_obj.name,
                    url=url_obj.url,
                    ok=False,
                    status_code=None,
                    time_ms=elapsed_ms,
                    error=str(e)
                ))

    db.commit()


    limitando_runs(db, url_list_id=list_id, max_runs=200)
    limitando_run_results(db, max_rows=1000)

    return run
