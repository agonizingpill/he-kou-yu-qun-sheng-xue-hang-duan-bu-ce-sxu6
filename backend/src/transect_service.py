import math
import numpy as np
from sqlalchemy import select
from .models import Transect,Echo
from .common import get,reject,finish,cruise_lock,transect_lock

def length(lon1,lat1,lon2,lat2):return math.hypot(math.radians(lon2-lon1)*6371000*math.cos(math.radians((lat1+lat2)/2)),math.radians(lat2-lat1)*6371000)
def create(db,data,user):
    c=cruise_lock(db,data.cruise_id);reject(c.status not in ('planned','sailing'),'现场调查已结束，不能增加航段')
    reject(data.probe_khz not in (38,120,200),'探头频率只支持38/120/200kHz')
    distance=length(data.start_lon,data.start_lat,data.end_lon,data.end_lat)
    reject(distance<80 or distance>20000,'航段长度需80米至20公里')
    reject(db.scalar(select(Transect).where(Transect.cruise_id==c.id,Transect.code==data.code)) is not None,'航次内航段编号重复')
    row=Transect(**data.model_dump(),length_m=distance);db.add(row);db.flush();return finish(db,user,'规划声学航段',row)
def record(db,id,points,user,source='manual'):
    c,t=transect_lock(db,id,True)
    for p in points:
        reject(p['along_m']>t.length_m,'回波距离超出航段范围')
        f=p['along_m']/t.length_m;expected_lon=t.start_lon+(t.end_lon-t.start_lon)*f;expected_lat=t.start_lat+(t.end_lat-t.start_lat)*f
        reject(length(expected_lon,expected_lat,p['lon'],p['lat'])>100,'回波坐标偏离航段超过100米')
        db.add(Echo(transect_id=id,**p,source=source))
    t.data_version+=1;t.status='acquired';return finish(db,user,'记录探头回波',t)
def synthetic_points(t):
    rng=np.random.default_rng(37+t.id);points=[]
    for center,depth,strength in [(.18,7,-46),(.51,14,-39),(.83,21,-52)]:
        for _ in range(24):
            along=float(np.clip(rng.normal(center*t.length_m,min(12,t.length_m*.018)),0,t.length_m));f=along/t.length_m
            points.append({'along_m':along,'lon':t.start_lon+(t.end_lon-t.start_lon)*f,'lat':t.start_lat+(t.end_lat-t.start_lat)*f,'depth_m':float(rng.normal(depth,.45)),'strength_db':float(rng.normal(strength,1.1))})
    for _ in range(8):
        along=float(rng.uniform(0,t.length_m));f=along/t.length_m
        points.append({'along_m':along,'lon':t.start_lon+(t.end_lon-t.start_lon)*f,'lat':t.start_lat+(t.end_lat-t.start_lat)*f,'depth_m':float(rng.uniform(3,28)),'strength_db':float(rng.uniform(-85,-25))})
    return points
def simulate(db,id,user):
    c,t=transect_lock(db,id,True)
    reject(db.scalar(select(Echo).where(Echo.transect_id==id)) is not None,'该航段已有回波；模拟导入只适用于空航段')
    return record(db,id,synthetic_points(t),user,'synthetic-probe-seed37')
