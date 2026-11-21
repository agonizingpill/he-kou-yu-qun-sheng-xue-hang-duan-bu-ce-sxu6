from sqlalchemy import select,func
from zoneinfo import ZoneInfo
from .models import Net,NetCalibration,BioSample,Transect,Cruise
from .common import get,reject,finish,transect_lock
from .school_service import latest

SHANGHAI=ZoneInfo('Asia/Shanghai')

def return_date(c):return c.arrive.astimezone(SHANGHAI).date()
def latest_calibration(db,net_id):
    return db.scalar(select(NetCalibration).where(NetCalibration.net_id==net_id).order_by(NetCalibration.version.desc(),NetCalibration.id.desc()))
def deliverability(db,s):
    """判断一份生物样能否随返航日交付；只读，不改关联。"""
    cal=get(db,NetCalibration,s.calibration_id);t=get(db,Transect,s.transect_id);c=get(db,Cruise,t.cruise_id)
    latest_cal=latest_calibration(db,cal.net_id);reasons=[]
    if s.status!='valid':reasons.append('复校后待复核' if s.status=='pending' else '已由新关联替代')
    if not cal.passed:reasons.append('该次校验不合格')
    if latest_cal and latest_cal.id!=cal.id and c.status!='frozen':reasons.append('网具已复校至v%d，原关联失效'%latest_cal.version)
    if cal.valid_until<return_date(c):reasons.append('校验有效期未覆盖返航日')
    current=latest(db,t.id,True)
    if not current:reasons.append('最新回波群落尚未复核')
    elif current.id!=s.analysis_id:reasons.append('非当前已复核群落')
    return {'sample_id':s.id,'calibration_id':cal.id,'calibration_version':cal.version,'deliverable':not reasons,'reason':'；'.join(reasons) if reasons else '可交付'}
def net_state(db,net):
    cal=latest_calibration(db,net.id)
    return {'net_id':net.id,'latest_calibration_id':cal.id if cal else None,'version':cal.version if cal else None,'certificate':cal.certificate if cal else None,'passed':cal.passed if cal else None,'valid_until':cal.valid_until if cal else None}
def layer_ready(db,transect_id,analysis_id):
    """航段可交付：当前已复核群落至少有1份可交付样本，且没有复校后待复核的样本未处理。"""
    samples=list(db.scalars(select(BioSample).where(BioSample.transect_id==transect_id,BioSample.analysis_id==analysis_id)))
    pending=[s for s in samples if s.status=='pending']
    deliverable=[s for s in samples if s.status=='valid' and deliverability(db,s)['deliverable']]
    if pending:return False,'有复校后待复核样本，请按当前已复核群落重新关联'
    if not deliverable:return False,'缺少可按返航日有效最新校验交付的生物样，请按当前已复核群落重新关联'
    return True,''

def calibrate(db,data,user):
    net=get(db,Net,data.net_id)
    # 先按升序锁涉及航次根，再锁网具，避免与“先锁航次后锁网具”的关联流程互锁。
    impacted=sorted({get(db,Transect,s.transect_id).cruise_id for s in db.scalars(select(BioSample).join(NetCalibration,BioSample.calibration_id==NetCalibration.id).where(NetCalibration.net_id==net.id))})
    for cid in impacted:get(db,Cruise,cid,True)
    net=get(db,Net,data.net_id,True);passed=abs(data.measured_mm-net.mesh_mm)<=net.mesh_mm*.1
    version=(db.scalar(select(func.max(NetCalibration.version)).where(NetCalibration.net_id==net.id)) or 0)+1
    row=NetCalibration(**data.model_dump(),passed=passed,version=version);db.add(row);db.flush()
    # 复校后旧关联失效：保留原样本及其原校验凭据，只把待处理样本退回待复核；已封存航次快照不动。
    samples=db.scalars(select(BioSample).join(NetCalibration,BioSample.calibration_id==NetCalibration.id).where(NetCalibration.net_id==net.id)).all()
    for s in samples:
        if s.status=='valid' and get(db,Cruise,get(db,Transect,s.transect_id).cruise_id).status!='frozen':s.status='pending'
    db.flush();return finish(db,user,'网具尺度复校' if version>1 else '网具尺度校验',row)
def sample(db,data,user):
    c,t=transect_lock(db,data.transect_id);reject(c.status not in ('sailing','surveyed'),'航次尚未开航');cal=get(db,NetCalibration,data.calibration_id)
    net=get(db,Net,cal.net_id,True)
    current=latest_calibration(db,net.id)
    reject(not cal.passed or current.id!=cal.id,'网具未通过最新校验，重新校验后再关联生物样')
    reject(cal.valid_until<return_date(c),'网具校验有效期未覆盖航次日期')
    analysis=latest(db,t.id,True);reject(not analysis,'最新回波群落需主管复核后才能关联生物样')
    reject(data.cluster_label not in {p['label'] for p in analysis.assignments if p['label']>=0},'未找到该鱼群聚类，不能把噪点作为生物样')
    existing=db.scalar(select(BioSample).where(BioSample.transect_id==t.id,BioSample.analysis_id==analysis.id,BioSample.calibration_id==cal.id,BioSample.cluster_label==data.cluster_label,BioSample.status=='valid'))
    if existing:return finish(db,user,'生物样关联已存在，未重复生成',existing)
    # 同一网具对当前群落编号的旧关联（含复校后退回的待复核）保留凭据但由本次新关联替代，绝不改写原证书。
    for old in db.scalars(select(BioSample).join(NetCalibration,BioSample.calibration_id==NetCalibration.id).where(BioSample.transect_id==t.id,BioSample.analysis_id==analysis.id,BioSample.cluster_label==data.cluster_label,BioSample.status.in_(['valid','pending']),NetCalibration.net_id==net.id)):
        old.status='superseded'
    row=BioSample(**data.model_dump(),analysis_id=analysis.id,status='valid');db.add(row);db.flush();return finish(db,user,'记录网具生物抽样',row)
