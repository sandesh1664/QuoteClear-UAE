import hashlib,uuid,re
from fastapi import APIRouter,Depends,HTTPException,UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..security import current_user
from ..models import User,Document,now
from ..dependencies import own_job,own_document
from ..serialize import doc_out
from ..config import settings
router=APIRouter(tags=['Source documents'])
@router.post('/jobs/{job_id}/documents',status_code=202)
async def upload(job_id:str,file:UploadFile,db:Session=Depends(get_db),user:User=Depends(current_user)):
    own_job(db,job_id,user);data=bytearray()
    while chunk:=await file.read(65536):
        data.extend(chunk)
        if len(data)>settings().max_upload_bytes:raise HTTPException(413,'Maximum upload size is 10 MB')
    if data.startswith(b'%PDF-'):mime,ext='application/pdf','.pdf'
    elif data.startswith(b'\x89PNG\r\n\x1a\n'):mime,ext='image/png','.png'
    elif data.startswith(b'\xff\xd8\xff'):mime,ext='image/jpeg','.jpg'
    else:raise HTTPException(415,'Upload a PDF, PNG or JPEG file')
    root=settings().storage_dir;root.mkdir(parents=True,exist_ok=True);key=str(uuid.uuid4())+ext;path=root/key;path.write_bytes(data)
    name=re.sub(r'[\x00-\x1f/\\]','_',file.filename or 'document')[:170];doc=Document(job_id=job_id,filename=name,storage_key=key,mime=mime,sha256=hashlib.sha256(data).hexdigest(),size=len(data))
    try:db.add(doc);db.commit()
    except Exception:path.unlink(missing_ok=True);raise
    return doc_out(doc)
@router.get('/documents/{doc_id}')
def document(doc_id:str,db:Session=Depends(get_db),user:User=Depends(current_user)):return doc_out(own_document(db,doc_id,user))
@router.get('/documents/{doc_id}/file')
def download(doc_id:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    d=own_document(db,doc_id,user);path=settings().storage_dir/d.storage_key
    if not path.is_file():raise HTTPException(404,'The original file is unavailable')
    return FileResponse(path,media_type=d.mime,filename=d.filename,content_disposition_type='attachment',headers={'X-Content-Type-Options':'nosniff','Cache-Control':'private, no-store'})
@router.post('/documents/{doc_id}/retry')
def retry(doc_id:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    d=own_document(db,doc_id,user)
    if d.state in ('queued','processing'):raise HTTPException(409,'Extraction is already in progress')
    d.state='queued';d.error='';d.updated_at=now();db.commit();return doc_out(d)
