from datetime import datetime,timezone,date
from sqlalchemy import String,Integer,Float,ForeignKey,UniqueConstraint,CheckConstraint,DateTime,Date,JSON,Boolean,Text
from sqlalchemy.orm import Mapped,mapped_column
from .database import Base
from .constants import CruiseState,AnalysisState
def now():return datetime.now(timezone.utc)
class User(Base):
    __tablename__='users'
    id:Mapped[int]=mapped_column(primary_key=True)
    username:Mapped[str]=mapped_column(String(40),unique=True)
    password:Mapped[str]=mapped_column(String(128))
    role:Mapped[str]=mapped_column(String(20))
class Station(Base):
    __tablename__='stations'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(80))
class Boat(Base):
    __tablename__='boats'
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(30),unique=True)
    name:Mapped[str]=mapped_column(String(60))
class Cruise(Base):
    __tablename__='cruises'
    __table_args__=(CheckConstraint('arrive > depart'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(40),unique=True)
    boat_id:Mapped[int]=mapped_column(ForeignKey('boats.id'))
    depart:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    arrive:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    purpose:Mapped[str]=mapped_column(String(160))
    status:Mapped[str]=mapped_column(String(20),default=CruiseState.planned.value)
class NavigationClosure(Base):
    __tablename__='navigation_closures'
    __table_args__=(CheckConstraint('end_at > start_at'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(40),unique=True)
    start_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    end_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    reason:Mapped[str]=mapped_column(String(160))
class Transect(Base):
    __tablename__='transects'
    __table_args__=(UniqueConstraint('cruise_id','code'),CheckConstraint('length_m > 0'))
    id:Mapped[int]=mapped_column(primary_key=True)
    cruise_id:Mapped[int]=mapped_column(ForeignKey('cruises.id'))
    parent_id:Mapped[int|None]=mapped_column(ForeignKey('transects.id'),nullable=True)
    code:Mapped[str]=mapped_column(String(40))
    start_lon:Mapped[float]=mapped_column(Float)
    start_lat:Mapped[float]=mapped_column(Float)
    end_lon:Mapped[float]=mapped_column(Float)
    end_lat:Mapped[float]=mapped_column(Float)
    length_m:Mapped[float]=mapped_column(Float)
    probe_khz:Mapped[int]=mapped_column(Integer)
    gain_db:Mapped[float]=mapped_column(Float)
    data_version:Mapped[int]=mapped_column(Integer,default=0)
    status:Mapped[str]=mapped_column(String(20),default='planned')
class Echo(Base):
    __tablename__='echoes'
    __table_args__=(CheckConstraint('depth_m > 0'),CheckConstraint('along_m >= 0'))
    id:Mapped[int]=mapped_column(primary_key=True)
    transect_id:Mapped[int]=mapped_column(ForeignKey('transects.id'))
    along_m:Mapped[float]=mapped_column(Float)
    lon:Mapped[float]=mapped_column(Float)
    lat:Mapped[float]=mapped_column(Float)
    depth_m:Mapped[float]=mapped_column(Float)
    strength_db:Mapped[float]=mapped_column(Float)
    source:Mapped[str]=mapped_column(String(50),default='manual')
class SchoolAnalysis(Base):
    __tablename__='school_analyses'
    id:Mapped[int]=mapped_column(primary_key=True)
    transect_id:Mapped[int]=mapped_column(ForeignKey('transects.id'))
    data_version:Mapped[int]=mapped_column(Integer)
    eps:Mapped[float]=mapped_column(Float)
    min_samples:Mapped[int]=mapped_column(Integer)
    status:Mapped[str]=mapped_column(String(20),default=AnalysisState.queued.value)
    metrics:Mapped[dict]=mapped_column(JSON,default=dict)
    assignments:Mapped[list]=mapped_column(JSON,default=list)
    error:Mapped[str]=mapped_column(String(200),default='')
class SchoolReview(Base):
    __tablename__='school_reviews'
    id:Mapped[int]=mapped_column(primary_key=True)
    analysis_id:Mapped[int]=mapped_column(ForeignKey('school_analyses.id'),unique=True)
    noise_note:Mapped[str]=mapped_column(String(240))
    decision:Mapped[str]=mapped_column(String(120))
class Net(Base):
    __tablename__='nets'
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(30),unique=True)
    mesh_mm:Mapped[float]=mapped_column(Float)
class NetCalibration(Base):
    __tablename__='net_calibrations'
    id:Mapped[int]=mapped_column(primary_key=True)
    net_id:Mapped[int]=mapped_column(ForeignKey('nets.id'))
    measured_mm:Mapped[float]=mapped_column(Float)
    valid_until:Mapped[date]=mapped_column(Date)
    certificate:Mapped[str]=mapped_column(String(100))
    passed:Mapped[bool]=mapped_column(Boolean)
class BioSample(Base):
    __tablename__='bio_samples'
    id:Mapped[int]=mapped_column(primary_key=True)
    transect_id:Mapped[int]=mapped_column(ForeignKey('transects.id'))
    analysis_id:Mapped[int]=mapped_column(ForeignKey('school_analyses.id'))
    calibration_id:Mapped[int]=mapped_column(ForeignKey('net_calibrations.id'))
    cluster_label:Mapped[int]=mapped_column(Integer)
    species:Mapped[str]=mapped_column(String(60))
    count:Mapped[int]=mapped_column(Integer)
    mean_length_mm:Mapped[float]=mapped_column(Float)
class MissingInterval(Base):
    __tablename__='missing_intervals'
    __table_args__=(CheckConstraint('end_m > start_m AND start_m >= 0'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    transect_id:Mapped[int]=mapped_column(ForeignKey('transects.id'))
    start_m:Mapped[float]=mapped_column(Float)
    end_m:Mapped[float]=mapped_column(Float)
    reason:Mapped[str]=mapped_column(String(160))
    status:Mapped[str]=mapped_column(String(20),default='open')
class Resurvey(Base):
    __tablename__='resurveys'
    id:Mapped[int]=mapped_column(primary_key=True)
    gap_id:Mapped[int]=mapped_column(ForeignKey('missing_intervals.id'))
    continuation_id:Mapped[int]=mapped_column(ForeignKey('transects.id'),unique=True)
    status:Mapped[str]=mapped_column(String(20),default='planned')
    evidence:Mapped[str]=mapped_column(String(200),default='')
class SurveyRelease(Base):
    __tablename__='survey_releases'
    id:Mapped[int]=mapped_column(primary_key=True)
    cruise_id:Mapped[int]=mapped_column(ForeignKey('cruises.id'),unique=True)
    recipient:Mapped[str]=mapped_column(String(100))
    snapshot:Mapped[dict]=mapped_column(JSON)
    canonical_json:Mapped[str]=mapped_column(Text)
    sha256:Mapped[str]=mapped_column(String(64))
    at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Audit(Base):
    __tablename__='audit'
    id:Mapped[int]=mapped_column(primary_key=True)
    actor:Mapped[str]=mapped_column(String(40))
    action:Mapped[str]=mapped_column(String(100))
    detail:Mapped[str]=mapped_column(String(300))
    at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
