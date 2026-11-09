import json
from sqlalchemy import select
from .models import Job,Quote,LineItem,Document,Expense
from .services.comparison import analyze,money,clarification

def quote_out(db,q):
    items=db.scalars(select(LineItem).where(LineItem.quote_id==q.id)).all()
    analysis=analyze(q,items)
    return {**{k:getattr(q,k) for k in ('id','job_id','document_id','provider','reference','tax_mode','warranty_days','completion_days','valid_until','exclusions','notes')},'tax_rate':f'{q.tax_rate/100:.2f}','created_at':q.created_at.isoformat(),'items':[{**{k:getattr(i,k) for k in ('id','label','kind','pricing','quantity','reviewed','source_page','source_excerpt')},'amount':money(i.amount) if i.amount is not None else None} for i in items],'analysis':analysis,'clarification':clarification(q.provider,analysis)}

def doc_out(d): return {**{k:getattr(d,k) for k in ('id','job_id','filename','mime','sha256','size','state','error')},'created_at':d.created_at.isoformat(),'pages':json.loads(d.extracted)}
def expense_out(e): return {**{k:getattr(e,k) for k in ('id','job_id','label','paid_on','note')},'amount':money(e.amount)}
def job_out(db,j,detail=False):
    quotes=db.scalars(select(Quote).where(Quote.job_id==j.id).order_by(Quote.created_at)).all()
    expenses=db.scalars(select(Expense).where(Expense.job_id==j.id)).all()
    qdata=[quote_out(db,q) for q in quotes]
    confirmed=[q['analysis']['confirmed_total'] for q in qdata if q['analysis']['confirmed_total'] is not None]
    result={**{k:getattr(j,k) for k in ('id','title','category','emirate','description','status','selected_quote_id')},'created_at':j.created_at.isoformat(),'quote_count':len(quotes),'flag_count':sum(len(q['analysis']['flags']) for q in qdata),'lowest_confirmed':min(confirmed,key=float) if confirmed else None,'actual_total':money(sum(e.amount for e in expenses))}
    if detail:result.update(quotes=qdata,documents=[doc_out(d) for d in db.scalars(select(Document).where(Document.job_id==j.id).order_by(Document.created_at)).all()],expenses=[expense_out(e) for e in expenses])
    return result
