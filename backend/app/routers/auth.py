import hashlib
from datetime import timedelta
from fastapi import APIRouter,Depends,HTTPException,Request,Response
from sqlalchemy import select,delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User,SessionToken,LoginAttempt,now
from ..schemas import Register,Login
from ..security import current_user,password_hasher,create_session,hash_token,COOKIE
from ..config import settings
router=APIRouter(prefix='/auth',tags=['Authentication'])
def user_out(u):return {'id':u.id,'name':u.name,'email':u.email}
def limit(db,request,email):
    ip=request.client.host if request.client else 'unknown';key=hashlib.sha256((ip+email.casefold()).encode()).hexdigest();attempt=db.get(LoginAttempt,key)
    if attempt and attempt.window_start>now()-timedelta(minutes=15):
        if attempt.count>=10:raise HTTPException(429,'Too many attempts. Try again in 15 minutes.')
        attempt.count+=1
    else:
        if attempt:db.delete(attempt);db.flush()
        db.add(LoginAttempt(key=key,count=1))
    db.execute(delete(LoginAttempt).where(LoginAttempt.window_start<now()-timedelta(days=1)));db.commit();return key
@router.post('/register',status_code=201)
def register(data:Register,request:Request,response:Response,db:Session=Depends(get_db)):
    if not settings().allow_registration:raise HTTPException(403,'Registration is closed')
    limit(db,request,data.email);u=User(name=data.name,email=data.email.casefold(),password_hash=password_hasher.hash(data.password));db.add(u)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'An account with this email already exists')
    create_session(db,u,response);return user_out(u)
@router.post('/login')
def login(data:Login,request:Request,response:Response,db:Session=Depends(get_db)):
    key=limit(db,request,data.email);u=db.scalar(select(User).where(User.email==data.email.casefold()));check=u.password_hash if u else password_hasher.hash('no-account-placeholder');good=password_hasher.verify(data.password,check)
    if not u or not good:raise HTTPException(401,'Email or password is incorrect')
    db.execute(delete(LoginAttempt).where(LoginAttempt.key==key));db.commit();create_session(db,u,response);return user_out(u)
@router.get('/me')
def me(user:User=Depends(current_user)):return user_out(user)
@router.post('/logout',status_code=204)
def logout(request:Request,response:Response,db:Session=Depends(get_db)):
    db.execute(delete(SessionToken).where(SessionToken.token_hash==hash_token(request.cookies.get(COOKIE,''))));db.commit();response.delete_cookie(COOKIE,path='/api');response.status_code=204;return response
