import os,logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from .database import Base,engine
from .routes import router
from .middlewares import RequestTrace,BurstLimit
logging.basicConfig(level=logging.INFO)
def upgrade_schema():
    """无迁移链：为既有演示库补上网具校验版本与样本交付状态列。"""
    with engine.begin() as conn:
        if conn.dialect.name=='sqlite':
            cols={r[1] for r in conn.execute(text('PRAGMA table_info(net_calibrations)'))}
            if 'version' not in cols:conn.execute(text('ALTER TABLE net_calibrations ADD COLUMN version INTEGER NOT NULL DEFAULT 1'))
            cols={r[1] for r in conn.execute(text('PRAGMA table_info(bio_samples)'))}
            if 'status' not in cols:conn.execute(text("ALTER TABLE bio_samples ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'valid'"))
        else:
            conn.execute(text("ALTER TABLE net_calibrations ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1"))
            conn.execute(text("ALTER TABLE bio_samples ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'valid'"))
        # 既有库的旧校验按网具内 id 顺序补成递增版本；一旦该网具出现新版本就不再改写，避免覆盖已有版本。
        conn.execute(text('UPDATE net_calibrations SET version=(SELECT COUNT(*) FROM net_calibrations p WHERE p.net_id=net_calibrations.net_id AND p.id<=net_calibrations.id) WHERE version=1 AND (SELECT COUNT(*) FROM net_calibrations p WHERE p.net_id=net_calibrations.net_id)>1 AND NOT EXISTS (SELECT 1 FROM net_calibrations q WHERE q.net_id=net_calibrations.net_id AND q.version>1)'))
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    upgrade_schema()
    if os.getenv('SEED_DEMO','true')=='true':
        try:
            from .seed import seed
            seed()
        except Exception:logging.exception('seed failed')
    yield
app=FastAPI(title='潮汐渔研站 · 河口声学调查',lifespan=lifespan)
app.add_middleware(RequestTrace);app.add_middleware(BurstLimit)
@app.exception_handler(IntegrityError)
async def integrity(request,exc):return JSONResponse({'detail':'记录存在冲突或违反约束，请刷新重试'},status_code=409)
@app.get('/health')
def health():
    from sqlalchemy import text
    from .school_service import queue
    with engine.connect() as conn:conn.execute(text('SELECT 1'))
    queue.ping();return {'status':'ok'}
app.include_router(router)
