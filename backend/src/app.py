import os,logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from .database import Base,engine
from .routes import router
from .middlewares import RequestTrace,BurstLimit
logging.basicConfig(level=logging.INFO)
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
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
