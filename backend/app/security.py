import hashlib,secrets
from datetime import timedelta
from fastapi import Depends,HTTPException,Request,Response
from pwdlib import PasswordHash
from sqlalchemy import select,delete
from sqlalchemy.orm import Session
from .models import User,SessionToken,now
from .database import get_db
from .config import settings
password_hasher=PasswordHash.recommended()
COOKIE='qc_session'

def hash_token(token:str): return hashlib.sha256(token.encode()).hexdigest()
def create_session(db:Session,user:User,response:Response):
    token=secrets.token_urlsafe(48)
    db.execute(delete(SessionToken).where(SessionToken.expires_at<now()))
    db.add(SessionToken(token_hash=hash_token(token),user_id=user.id,expires_at=now()+timedelta(days=settings().session_days)))
    db.commit()
    response.set_cookie(COOKIE,token,max_age=settings().session_days*86400,httponly=True,secure=settings().cookie_secure,samesite='lax',path='/api')

def current_user(request:Request,db:Session=Depends(get_db))->User:
    token=request.cookies.get(COOKIE,'')
    if not token: raise HTTPException(401,'Sign in to continue')
    session=db.get(SessionToken,hash_token(token))
    if not session or session.expires_at<now(): raise HTTPException(401,'Your session expired. Please sign in again.')
    user=db.get(User,session.user_id)
    if not user: raise HTTPException(401,'Account not found')
    return user
