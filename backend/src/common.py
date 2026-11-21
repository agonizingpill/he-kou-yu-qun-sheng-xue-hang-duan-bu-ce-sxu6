from fastapi import HTTPException
from sqlalchemy import select
from .models import Cruise,Transect,Audit

def get(db,model,id,lock=False):
    stmt=select(model).where(model.id==id)
    if lock:stmt=stmt.with_for_update().execution_options(populate_existing=True)
    row=db.scalar(stmt)
    if not row:raise HTTPException(404,'航次或关联记录不存在')
    return row
def reject(condition,message):
    if condition:raise HTTPException(409,message)
def dump(row):return {c.name:getattr(row,c.name) for c in row.__table__.columns}
def finish(db,user,action,row):
    db.add(Audit(actor=user.username,action=action,detail=str(row.id)));db.commit();return dump(row)
def cruise_lock(db,id,sailing=False):
    c=get(db,Cruise,id,True);reject(c.status=='frozen','调查图层已封存，业务记录不可修改')
    if sailing:reject(c.status!='sailing','该操作需航次处于调查中')
    return c
def transect_lock(db,id,sailing=False):
    initial=get(db,Transect,id);c=cruise_lock(db,initial.cruise_id,sailing);t=get(db,Transect,id,True);reject(t.status=='cancelled','补航已撤销');return c,t
