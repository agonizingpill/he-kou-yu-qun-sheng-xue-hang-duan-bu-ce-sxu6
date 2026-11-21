from sqlalchemy import select
from .models import Station,Boat,Cruise,NavigationClosure,Transect
from .common import get,reject,finish

def create(db,data,user):
    get(db,Station,1,True);get(db,Boat,data.boat_id,True)
    reject(db.scalar(select(Cruise).where(Cruise.code==data.code)) is not None,'航次号重复')
    row=Cruise(**data.model_dump());db.add(row);db.flush();return finish(db,user,'申请调查航次',row)
def change(db,id,data,user):
    get(db,Station,1,True);initial=get(db,Cruise,id);get(db,Boat,initial.boat_id,True);row=get(db,Cruise,id,True)
    reject(row.status!='planned','仅未开航航次可改航窗')
    row.depart=data.depart;row.arrive=data.arrive;return finish(db,user,'调整调查航窗',row)
def closure(db,data,user):
    get(db,Station,1,True)
    reject(db.scalar(select(NavigationClosure).where(NavigationClosure.code==data.code)) is not None,'禁航编号重复')
    reject(db.scalar(select(Cruise).where(Cruise.status=='sailing',Cruise.depart<data.end_at,Cruise.arrive>data.start_at)) is not None,'已有调查中航次冲突，需先协调返航')
    row=NavigationClosure(**data.model_dump());db.add(row);db.flush();return finish(db,user,'登记禁航时段',row)
def launch(db,id,user):
    get(db,Station,1,True);initial=get(db,Cruise,id);get(db,Boat,initial.boat_id,True);row=get(db,Cruise,id,True)
    reject(row.status!='planned','该航次已开航或已封存')
    reject(db.scalar(select(NavigationClosure).where(NavigationClosure.start_at<row.arrive,NavigationClosure.end_at>row.depart)) is not None,'航窗与潮汐禁航冲突，修改时段后再开航')
    reject(db.scalar(select(Cruise).where(Cruise.id!=id,Cruise.boat_id==row.boat_id,Cruise.status!='planned',Cruise.depart<row.arrive,Cruise.arrive>row.depart)) is not None,'调查船同期已有航次，调整航窗或另选调查船')
    reject(not db.scalar(select(Transect).where(Transect.cruise_id==id,Transect.status!='cancelled')),'先规划至少一条声学航段')
    row.status='sailing';return finish(db,user,'核准开航',row)
def return_port(db,id,user):
    from .common import cruise_lock
    from .models import Echo,Resurvey,MissingInterval
    from sqlalchemy import func
    row=cruise_lock(db,id,True)
    transects=list(db.scalars(select(Transect).where(Transect.cruise_id==id,Transect.status!='cancelled')))
    reject(any(db.scalar(select(func.count()).select_from(Echo).where(Echo.transect_id==t.id))<8 for t in transects),'仍有航段未完成至少8个回波点')
    reject(db.scalar(select(MissingInterval).join(Transect).where(Transect.cruise_id==id,MissingInterval.status=='open')) is not None,'缺测仍未补齐，先完成补航接续再结束调查')
    row.status='surveyed';return finish(db,user,'结束现场调查',row)
