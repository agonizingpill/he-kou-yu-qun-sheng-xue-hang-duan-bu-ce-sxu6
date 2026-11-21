import hashlib,hmac,os,time
import jwt
from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy import select
from .database import session
from .models import User
security=HTTPBearer()
SECRET=os.getenv('JWT_SECRET','estuary-demo-secret')
def password_hash(value):return hashlib.pbkdf2_hmac('sha256',value.encode(),b'estuary-survey-local',180000).hex()
def issue(user):return jwt.encode({'sub':str(user.id),'exp':int(time.time())+28800},SECRET,algorithm='HS256')
def current(credentials=Depends(security),db=Depends(session)):
    try:
        claims=jwt.decode(credentials.credentials,SECRET,algorithms=['HS256'])
        user=db.get(User,int(claims['sub']))
        if not user:raise ValueError()
        return user
    except Exception:raise HTTPException(401,'登录过期，请重新登录')
def editor(user=Depends(current)):
    if user.role not in ('operator','supervisor'):raise HTTPException(403,'只读员不能修改调查记录')
    return user
def supervisor(user=Depends(current)):
    if user.role!='supervisor':raise HTTPException(403,'需调查主管签批')
    return user
