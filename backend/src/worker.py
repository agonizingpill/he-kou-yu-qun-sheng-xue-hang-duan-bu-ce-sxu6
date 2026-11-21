import logging,time,json
from pathlib import Path
from sqlalchemy import select
from .database import Session
from .models import SchoolAnalysis,Transect,Echo
from .school_service import queue
from .algorithm import analyze
from .common import dump
logging.basicConfig(level=logging.INFO)
while True:
    Path('/tmp/worker-heartbeat').touch()
    try:
        item=queue.blpop('estuary:schools',timeout=2)
        if not item:continue
        with Session() as db:
            row=db.get(SchoolAnalysis,int(item[1]))
            if not row or row.status!='queued':continue
            row.status='running';db.commit()
            try:
                t=db.get(Transect,row.transect_id)
                if row.data_version!=t.data_version:raise ValueError('回波已更新，请重新提交最新版本')
                points=[dump(p) for p in db.scalars(select(Echo).where(Echo.transect_id==t.id).order_by(Echo.id))]
                row.assignments,row.metrics=analyze(points,row.eps,row.min_samples);row.status='done'
                Path('/artifacts').mkdir(exist_ok=True);Path(f'/artifacts/school-{row.id}.json').write_text(json.dumps(row.metrics,ensure_ascii=False))
            except Exception as e:row.status='failed';row.error=str(e)[:200]
            db.commit()
    except Exception:logging.exception('echo worker');time.sleep(1)
