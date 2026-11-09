from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select,delete
from sqlalchemy.orm import Session
from ..database import get_db
from ..security import current_user
from ..models import User,Job,Quote,LineItem,Expense,Document
from ..schemas import JobIn,QuoteIn,ExpenseIn,Selection
from ..dependencies import own_job,own_quote,own_document
from ..serialize import job_out,quote_out,expense_out
from ..services.comparison import fils
router=APIRouter(tags=['Jobs and quotations'])
@router.get('/jobs')
def list_jobs(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return [job_out(db,j) for j in db.scalars(select(Job).where(Job.owner_id==user.id).order_by(Job.created_at.desc())).all()]
@router.post('/jobs',status_code=201)
def create_job(data:JobIn,db:Session=Depends(get_db),user:User=Depends(current_user)):
    
    if data.status=='Selected':raise HTTPException(400,'Choose a quotation after creating the job')
    j=Job(**data.model_dump(),owner_id=user.id);db.add(j);db.commit();return job_out(db,j,True)
@router.get('/jobs/{job_id}')
def get_job(job_id:str,db:Session=Depends(get_db),user:User=Depends(current_user)):return job_out(db,own_job(db,job_id,user),True)
@router.put('/jobs/{job_id}')
def update_job(job_id:str,data:JobIn,db:Session=Depends(get_db),user:User=Depends(current_user)):
    j=own_job(db,job_id,user)
    if data.status=='Selected' and not j.selected_quote_id:raise HTTPException(400,'Choose a quote before marking this job Selected')
    for k,v in data.model_dump().items():setattr(j,k,v)
    db.commit();return job_out(db,j,True)
@router.delete('/jobs/{job_id}',status_code=204)
def delete_job(job_id:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    from ..config import settings
    j=own_job(db,job_id,user);docs=list(db.scalars(select(Document).where(Document.job_id==j.id)));qids=select(Quote.id).where(Quote.job_id==j.id)
    db.execute(delete(LineItem).where(LineItem.quote_id.in_(qids)));db.execute(delete(Quote).where(Quote.job_id==j.id));db.execute(delete(Expense).where(Expense.job_id==j.id));db.execute(delete(Document).where(Document.job_id==j.id));db.delete(j);db.commit()
    for d in docs:(settings().storage_dir/d.storage_key).unlink(missing_ok=True)
def assign_quote(db,q,data,user):
    if data.document_id:
        d=own_document(db,data.document_id,user)
        if d.job_id!=q.job_id:raise HTTPException(400,'Source document belongs to another job')
    for item in data.items:
        if item.source_page or item.source_excerpt:
            if not data.document_id:raise HTTPException(400,'A source reference requires a document')
            import json
            page=next((p for p in json.loads(d.extracted) if p['page']==item.source_page),None)
            if not page or not item.source_excerpt or item.source_excerpt not in page['text']:raise HTTPException(400,'Source excerpt must match text on the selected document page')
    for k,v in data.model_dump(exclude={'items','tax_rate','valid_until'}).items():setattr(q,k,v)
    q.tax_rate=fils(data.tax_rate);q.valid_until=data.valid_until.isoformat() if data.valid_until else '';db.add(q);db.flush();db.execute(delete(LineItem).where(LineItem.quote_id==q.id))
    for item in data.items:db.add(LineItem(quote_id=q.id,**item.model_dump(exclude={'amount'}),amount=fils(item.amount) if item.amount is not None else None))
@router.post('/jobs/{job_id}/quotes',status_code=201)
def create_quote(job_id:str,data:QuoteIn,db:Session=Depends(get_db),user:User=Depends(current_user)):
    own_job(db,job_id,user);q=Quote(job_id=job_id);assign_quote(db,q,data,user);db.commit();return quote_out(db,q)
@router.put('/quotes/{quote_id}')
def update_quote(quote_id:str,data:QuoteIn,db:Session=Depends(get_db),user:User=Depends(current_user)):
    q=own_quote(db,quote_id,user);assign_quote(db,q,data,user);j=own_job(db,q.job_id,user)
    if j.selected_quote_id==q.id and quote_out(db,q)['analysis']['confirmed_total'] is None:j.selected_quote_id=None;j.status='Comparing'
    db.commit();return quote_out(db,q)
@router.delete('/quotes/{quote_id}',status_code=204)
def delete_quote(quote_id:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    q=own_quote(db,quote_id,user);j=own_job(db,q.job_id,user)
    if j.selected_quote_id==q.id:j.selected_quote_id=None;j.status='Comparing'
    db.execute(delete(LineItem).where(LineItem.quote_id==q.id));db.delete(q);db.commit()
@router.post('/jobs/{job_id}/selection')
def select_quote(job_id:str,data:Selection,db:Session=Depends(get_db),user:User=Depends(current_user)):
    j=own_job(db,job_id,user)
    if data.quote_id:
        q=own_quote(db,data.quote_id,user)
        if q.job_id!=j.id:raise HTTPException(400,'Quote belongs to another job')
        if quote_out(db,q)['analysis']['confirmed_total'] is None:raise HTTPException(400,'Resolve unknown costs, tax treatment and review items before selection')
    j.selected_quote_id=data.quote_id;j.status='Selected' if data.quote_id else 'Comparing';db.commit();return job_out(db,j,True)
@router.post('/jobs/{job_id}/expenses',status_code=201)
def add_expense(job_id:str,data:ExpenseIn,db:Session=Depends(get_db),user:User=Depends(current_user)):
    own_job(db,job_id,user);e=Expense(job_id=job_id,**data.model_dump(exclude={'amount','paid_on'}),amount=fils(data.amount),paid_on=data.paid_on.isoformat());db.add(e);db.commit();return expense_out(e)
@router.delete('/expenses/{expense_id}',status_code=204)
def remove_expense(expense_id:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    e=db.get(Expense,expense_id)
    if not e:raise HTTPException(404,'Expense not found')
    own_job(db,e.job_id,user);db.delete(e);db.commit()
