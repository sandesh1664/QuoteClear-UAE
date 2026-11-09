"""SQL extraction queue. PostgreSQL workers claim jobs with SKIP LOCKED."""
import json,subprocess,sys,time,signal
from datetime import timedelta
from sqlalchemy import select,update
from .database import SessionLocal
from .config import settings
from .models import Document,now

def process_next()->bool:
    with SessionLocal() as db:
        db.execute(update(Document).where(Document.state=='processing',Document.updated_at<now()-timedelta(minutes=5)).values(state='queued'))
        doc=db.scalar(select(Document).where(Document.state=='queued').order_by(Document.created_at).with_for_update(skip_locked=True).limit(1))
        if not doc:db.commit();return False
        doc.state='processing';doc.updated_at=now();doc_id=doc.id;path=settings().storage_dir/doc.storage_key;mime=doc.mime;db.commit()
    state='ready';pages=[];error=''
    try:
        if mime!='application/pdf':state='ocr_needed';error='Image attached. Enter the quote manually; OCR is not enabled in this release.'
        else:
            result=subprocess.run([sys.executable,'-m','app.services.extract_worker',str(path.resolve())],capture_output=True,text=True,timeout=25,check=False)
            if result.returncode:raise ValueError(result.stderr.strip()[:250] or 'Could not parse this PDF')
            pages=json.loads(result.stdout)
            if not any(p['text'].strip() for p in pages):state='ocr_needed';error='No selectable text found. Enter amounts manually or upload a text PDF.'
    except subprocess.TimeoutExpired:state='failed';error='Extraction timed out. Try a smaller PDF.'
    except Exception as e:state='failed';error=str(e)[:250]
    with SessionLocal() as db:
        doc=db.get(Document,doc_id)
        if doc:doc.state=state;doc.extracted=json.dumps(pages);doc.error=error;doc.updated_at=now();db.commit()
    return True
if __name__=='__main__':
    stopped=False
    def stop(*args):
        global stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    while not stopped:
        try:
            if not process_next():time.sleep(2)
        except Exception as e:print('Worker task failed:',type(e).__name__,flush=True);time.sleep(3)
