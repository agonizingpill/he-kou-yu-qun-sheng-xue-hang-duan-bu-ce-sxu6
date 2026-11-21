from datetime import datetime,date
from pydantic import BaseModel,Field,model_validator
class Login(BaseModel):
    username:str
    password:str
class Schedule(BaseModel):
    depart:datetime
    arrive:datetime
    @model_validator(mode='after')
    def ordered(self):
        if self.depart.tzinfo is None or self.arrive.tzinfo is None or self.arrive<=self.depart:raise ValueError('需带时区且结束晚于开始')
        return self
class CruiseInput(Schedule):
    code:str=Field(min_length=3,max_length=40)
    boat_id:int
    purpose:str=Field(min_length=4,max_length=160)
class ClosureInput(BaseModel):
    code:str=Field(min_length=3,max_length=40)
    start_at:datetime
    end_at:datetime
    reason:str=Field(min_length=4,max_length=160)
    @model_validator(mode='after')
    def ordered(self):
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None or self.end_at<=self.start_at:raise ValueError('禁航结束需晚于开始且带时区')
        return self
class TransectInput(BaseModel):
    cruise_id:int
    code:str=Field(min_length=2,max_length=40)
    start_lon:float=Field(ge=-180,le=180)
    start_lat:float=Field(ge=-85,le=85)
    end_lon:float=Field(ge=-180,le=180)
    end_lat:float=Field(ge=-85,le=85)
    probe_khz:int
    gain_db:float=Field(ge=10,le=80)
class EchoPoint(BaseModel):
    along_m:float=Field(ge=0)
    lon:float=Field(ge=-180,le=180)
    lat:float=Field(ge=-85,le=85)
    depth_m:float=Field(gt=0,le=300)
    strength_db:float=Field(ge=-120,le=0)
class EchoInput(BaseModel):
    points:list[EchoPoint]=Field(min_length=1,max_length=1000)
class AnalysisInput(BaseModel):
    transect_id:int
    eps:float=Field(ge=.3,le=3)
    min_samples:int=Field(ge=3,le=12)
class ReviewInput(BaseModel):
    noise_note:str=Field(min_length=1,max_length=240)
    decision:str=Field(min_length=4,max_length=120)
class CalibrationInput(BaseModel):
    net_id:int
    measured_mm:float=Field(gt=0,le=100)
    valid_until:date
    certificate:str=Field(min_length=4,max_length=100)
class SampleInput(BaseModel):
    transect_id:int
    calibration_id:int
    cluster_label:int=Field(ge=0)
    species:str=Field(min_length=2,max_length=60)
    count:int=Field(gt=0,le=10000)
    mean_length_mm:float=Field(gt=0,le=3000)
class GapInput(BaseModel):
    transect_id:int
    start_m:float=Field(ge=0)
    end_m:float=Field(gt=0)
    reason:str=Field(min_length=4,max_length=160)
class ResurveyInput(BaseModel):
    gap_id:int
    code:str=Field(min_length=2,max_length=40)
class CompletionInput(BaseModel):
    evidence:str=Field(min_length=8,max_length=200)
class ReleaseInput(BaseModel):
    cruise_id:int
    recipient:str=Field(min_length=3,max_length=100)
