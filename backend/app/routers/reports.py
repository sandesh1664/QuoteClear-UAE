import io,json
from xml.sax.saxutils import escape
from fastapi import APIRouter,Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from ..database import get_db
from ..security import current_user
from ..models import User
from ..dependencies import own_job
from ..serialize import job_out
router=APIRouter(tags=['Reports'])
@router.get('/jobs/{job_id}/export')
def export(job_id:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    return Response(json.dumps({'app':'QuoteClear UAE','version':1,'job':job_out(db,own_job(db,job_id,user),True)},indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename="quoteclear-comparison.json"','Cache-Control':'no-store'})
@router.get('/jobs/{job_id}/report.pdf')
def report(job_id:str,db:Session=Depends(get_db),user:User=Depends(current_user)):
    data=job_out(db,own_job(db,job_id,user),True);buffer=io.BytesIO();styles=getSampleStyleSheet();story=[]
    def p(text,style='BodyText'):return Paragraph(escape(str(text)),styles[style])
    story.extend([p('QuoteClear UAE','Title'),p(data['title'],'Heading1'),p(data['category']+' | '+data['emirate']),p('User-reviewed quotation comparison. Prices are entered or confirmed by the account owner. This report does not verify providers or guarantee final charges.'),Spacer(1,18)])
    for q in data['quotes']:
        a=q['analysis'];story.append(p(q['provider'],'Heading2'));story.append(p('Confirmed total: '+('AED '+a['confirmed_total'] if a['confirmed_total'] else 'Incomplete; clarification required')));story.append(p('Known cost including specified additional tax: AED '+a['known_total']))
        source=next((d for d in data['documents'] if d['id']==q['document_id']),None)
        if source:story.extend([p('Source: '+source['filename']),p('File SHA-256: '+source['sha256'])])
        rows=[[p('Item'),p('Pricing'),p('Amount / unit'),p('Qty'),p('Reviewed')]]
        for i in q['items']:rows.append([p(i['label']),p(i['pricing']),p('AED '+i['amount'] if i['amount'] is not None else 'Unknown'),p(i['quantity']),p('Yes' if i['reviewed'] else 'No')])
        table=Table(rows,colWidths=[190,75,100,35,60],repeatRows=1);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf2ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#dbe6e0')),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8)]));story.extend([Spacer(1,8),table])
        for f in a['flags']:story.append(p('Clarify: '+f['label']+' - '+f['detail']))
        for i in q['items']:
            if i['source_excerpt']:story.append(p('Source page '+str(i['source_page'])+': '+i['source_excerpt']))
        story.append(Spacer(1,15))
    story.extend([p('Actual spending','Heading2'),p('Recorded total: AED '+data['actual_total'])])
    for e in data['expenses']:story.append(p(e['paid_on']+' | '+e['label']+' | AED '+e['amount']))
    SimpleDocTemplate(buffer,title='QuoteClear comparison',author='QuoteClear UAE',leftMargin=40,rightMargin=40).build(story)
    return Response(buffer.getvalue(),media_type='application/pdf',headers={'Content-Disposition':'attachment; filename="quoteclear-report.pdf"','Cache-Control':'no-store'})
