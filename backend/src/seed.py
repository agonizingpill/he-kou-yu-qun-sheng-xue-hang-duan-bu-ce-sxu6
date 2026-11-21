from datetime import datetime,date
from sqlalchemy import select
from .database import Session
from .models import *
from .auth import password_hash
from .constants import Role
from .transect_service import length

def seed():
    with Session() as db:
        if not db.get(Station,1):db.add(Station(id=1,name='潮汐渔研站'))
        for role in Role:
            if not db.scalar(select(User).where(User.username==role.value)):db.add(User(username=role.value,password=password_hash('Estuary@2026'),role=role.value))
        for code,name in [('T1','潮研一号'),('T2','潮研二号')]:
            if not db.scalar(select(Boat).where(Boat.code==code)):db.add(Boat(code=code,name=name))
        if not db.scalar(select(NavigationClosure).where(NavigationClosure.code=='TIDE-1118')):db.add(NavigationClosure(code='TIDE-1118',start_at=datetime.fromisoformat('2026-11-18T12:00:00+08:00'),end_at=datetime.fromisoformat('2026-11-18T14:00:00+08:00'),reason='河口潮汐禁航'))
        db.flush()
        if not db.scalar(select(Cruise).where(Cruise.code=='CY031')):
            boat=db.scalar(select(Boat).where(Boat.code=='T1'));c=Cruise(code='CY031',boat_id=boat.id,depart=datetime.fromisoformat('2026-11-18T11:00:00+08:00'),arrive=datetime.fromisoformat('2026-11-18T13:00:00+08:00'),purpose='河口鱼群声学航段与补测');db.add(c);db.flush()
            for code,lat in [('E1',30.1),('E2',30.103)]:
                t=Transect(cruise_id=c.id,code=code,start_lon=120.1,start_lat=lat,end_lon=120.113,end_lat=lat,length_m=length(120.1,lat,120.113,lat),probe_khz=120,gain_db=36);db.add(t);db.flush()
                if code=='E1':db.add(MissingInterval(transect_id=t.id,start_m=300,end_m=600,reason='探头断续缺测300米'))
        if not db.scalar(select(Net).where(Net.code=='N31')):
            net=Net(code='N31',mesh_mm=10);db.add(net);db.flush();db.add(NetCalibration(net_id=net.id,measured_mm=11.6,valid_until=date(2026,12,31),certificate='N31-初校超差',passed=False))
        db.commit()
if __name__=='__main__':seed()
