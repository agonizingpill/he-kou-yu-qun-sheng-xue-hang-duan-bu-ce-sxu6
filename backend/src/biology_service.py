from sqlalchemy import select
from zoneinfo import ZoneInfo
from .models import Net,NetCalibration,BioSample
from .common import get,reject,finish,transect_lock
from .school_service import latest

def calibrate(db,data,user):
    net=get(db,Net,data.net_id,True);passed=abs(data.measured_mm-net.mesh_mm)<=net.mesh_mm*.1
    row=NetCalibration(**data.model_dump(),passed=passed);db.add(row);db.flush();return finish(db,user,'网具尺度校验',row)
def sample(db,data,user):
    c,t=transect_lock(db,data.transect_id);reject(c.status not in ('sailing','surveyed'),'航次尚未开航');cal=get(db,NetCalibration,data.calibration_id)
    get(db,Net,cal.net_id,True)
    current=db.scalar(select(NetCalibration).where(NetCalibration.net_id==cal.net_id).order_by(NetCalibration.id.desc()))
    reject(not cal.passed or current.id!=cal.id,'网具未通过最新校验，重新校验后再关联生物样')
    reject(cal.valid_until<c.arrive.astimezone(ZoneInfo('Asia/Shanghai')).date(),'网具校验有效期未覆盖航次日期')
    analysis=latest(db,t.id,True);reject(not analysis,'最新回波群落需主管复核后才能关联生物样')
    reject(data.cluster_label not in {p['label'] for p in analysis.assignments if p['label']>=0},'未找到该鱼群聚类，不能把噪点作为生物样')
    row=BioSample(**data.model_dump(),analysis_id=analysis.id);db.add(row);db.flush();return finish(db,user,'记录网具生物抽样',row)
