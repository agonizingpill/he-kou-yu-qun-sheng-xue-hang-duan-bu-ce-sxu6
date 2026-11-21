import os,redis
from fastapi import HTTPException
from sqlalchemy import select,func
from .models import SchoolAnalysis,SchoolReview,Transect,Echo
from .common import get,reject,finish,transect_lock
queue=redis.Redis.from_url(os.getenv('REDIS_URL','redis://redis:6379/0'),decode_responses=True)
def latest(db,transect_id,reviewed=False):
    t=get(db,Transect,transect_id)
    row=db.scalar(select(SchoolAnalysis).where(SchoolAnalysis.transect_id==transect_id,SchoolAnalysis.data_version==t.data_version).order_by(SchoolAnalysis.id.desc()))
    if row is None or row.status not in (('reviewed',) if reviewed else ('done','reviewed')):return None
    return row
def enqueue(db,data,user):
    c,t=transect_lock(db,data.transect_id)
    reject(db.scalar(select(func.count()).select_from(Echo).where(Echo.transect_id==t.id))<8,'至少8个回波点才可识别群落')
    reject(db.scalar(select(SchoolAnalysis).where(SchoolAnalysis.transect_id==t.id,SchoolAnalysis.data_version==t.data_version,SchoolAnalysis.status.in_(['queued','running']))) is not None,'当前版本正在识别')
    row=SchoolAnalysis(**data.model_dump(),data_version=t.data_version);db.add(row);db.flush();result=finish(db,user,'提交回波群落识别',row)
    try:queue.rpush('estuary:schools',row.id)
    except redis.RedisError:
        row.status='failed';row.error='队列暂不可用，恢复后可重新识别';db.commit();raise HTTPException(503,row.error)
    return result
def review(db,id,data,user):
    initial=get(db,SchoolAnalysis,id);c,t=transect_lock(db,initial.transect_id);row=get(db,SchoolAnalysis,id,True)
    reject(row.status!='done' or row.data_version!=t.data_version,'仅最新回波版本的已完成识别可复核')
    reject(row.metrics.get('noise_count',0)>0 and len(data.noise_note.strip())<8,'存在噪点，请补充至少8字现场解释')
    row.status='reviewed';t.status='reviewed';review=SchoolReview(analysis_id=row.id,**data.model_dump());db.add(review);db.flush();return finish(db,user,'群落与噪点复核',review)
