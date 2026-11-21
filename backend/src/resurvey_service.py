from sqlalchemy import select
from .models import MissingInterval,Resurvey,Transect,Echo,BioSample
from .common import get,reject,finish,transect_lock
from .school_service import latest
from .transect_service import length

def gap(db,data,user):
    c,t=transect_lock(db,data.transect_id,True)
    reject(data.end_m<=data.start_m or data.end_m>t.length_m,'缺测区间必须在原航段范围内且正向')
    reject(db.scalar(select(MissingInterval).where(MissingInterval.transect_id==t.id,MissingInterval.start_m<data.end_m,MissingInterval.end_m>data.start_m)) is not None,'缺测区间与已有记录重叠')
    row=MissingInterval(**data.model_dump());db.add(row);db.flush();return finish(db,user,'标记缺测区间',row)
def plan(db,data,user):
    initial=get(db,MissingInterval,data.gap_id);c,parent=transect_lock(db,initial.transect_id,True);g=get(db,MissingInterval,data.gap_id,True)
    reject(g.status!='open','缺测区间已接续')
    reject(db.scalar(select(Resurvey).where(Resurvey.gap_id==g.id,Resurvey.status=='planned')) is not None,'该缺测已有在途补航')
    reject(db.scalar(select(Transect).where(Transect.cruise_id==c.id,Transect.code==data.code)) is not None,'补航航段编号重复')
    a=g.start_m/parent.length_m;b=g.end_m/parent.length_m
    row=Transect(cruise_id=c.id,parent_id=parent.id,code=data.code,start_lon=parent.start_lon+(parent.end_lon-parent.start_lon)*a,start_lat=parent.start_lat+(parent.end_lat-parent.start_lat)*a,end_lon=parent.start_lon+(parent.end_lon-parent.start_lon)*b,end_lat=parent.start_lat+(parent.end_lat-parent.start_lat)*b,length_m=g.end_m-g.start_m,probe_khz=parent.probe_khz,gain_db=parent.gain_db)
    db.add(row);db.flush();res=Resurvey(gap_id=g.id,continuation_id=row.id);db.add(res);db.flush();return finish(db,user,'规划缺测补航',res)
def complete(db,id,data,user):
    initial=get(db,Resurvey,id);c,t=transect_lock(db,initial.continuation_id,True);res=get(db,Resurvey,id,True);g=get(db,MissingInterval,res.gap_id,True)
    reject(res.status!='planned','补航已接续或撤销')
    a=latest(db,t.id,True);reject(not a,'补航回波群落尚未复核')
    reject(not db.scalar(select(BioSample).where(BioSample.transect_id==t.id,BioSample.analysis_id==a.id)),'补航缺少对应群落的网具抽样')
    reject(db.scalar(select(MissingInterval).where(MissingInterval.transect_id==t.id,MissingInterval.status=='open')) is not None,'补航自身仍存在缺测')
    res.status='completed';res.evidence=data.evidence;g.status='covered';return finish(db,user,'确认缺测补航接续',res)
def cancel(db,id,user):
    initial=get(db,Resurvey,id);c,t=transect_lock(db,initial.continuation_id,True);row=get(db,Resurvey,id,True)
    reject(row.status!='planned' or db.scalar(select(Echo).where(Echo.transect_id==t.id)) is not None,'已采集回波或已结束的补航不能撤销')
    row.status='cancelled';t.status='cancelled';return finish(db,user,'撤销空补航并重新安排',row)
