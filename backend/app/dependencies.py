from fastapi import HTTPException
from sqlalchemy import select
from .models import Job,Quote,Document

def own_job(db,job_id,user):
    job=db.scalar(select(Job).where(Job.id==job_id,Job.owner_id==user.id))
    if not job:raise HTTPException(404,'Job not found')
    return job

def own_quote(db,quote_id,user):
    q=db.scalar(select(Quote).join(Job,Quote.job_id==Job.id).where(Quote.id==quote_id,Job.owner_id==user.id))
    if not q:raise HTTPException(404,'Quotation not found')
    return q

def own_document(db,doc_id,user):
    d=db.scalar(select(Document).join(Job,Document.job_id==Job.id).where(Document.id==doc_id,Job.owner_id==user.id))
    if not d:raise HTTPException(404,'Document not found')
    return d
