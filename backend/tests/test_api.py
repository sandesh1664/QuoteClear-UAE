import io
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from app.main import app
from app.worker import process_next

def quote(**changes):
    return {'provider':'Sample Provider','tax_mode':'excluded','tax_rate':'5.00','warranty_days':30,'completion_days':2,'exclusions':'No additional parts','items':[{'label':'Service','kind':'Labour','pricing':'fixed','amount':'0.10','quantity':3,'reviewed':True}],**changes}

def test_auth_csrf_and_session(client):
    assert client.get('/api/jobs').status_code==401
    assert TestClient(app).post('/api/auth/login',json={}).status_code==403
    assert client.post('/api/auth/register',headers={'Origin':'https://evil.example'},json={}).status_code==403
    r=client.post('/api/auth/register',json={'name':'A','email':'a@example.test','password':'long-password-123'});assert r.status_code==201
    assert 'HttpOnly' in r.headers['set-cookie'];assert client.get('/api/auth/me').status_code==200
    assert client.post('/api/auth/logout').status_code==204;assert client.get('/api/auth/me').status_code==401
    assert client.post('/api/auth/login',json={'email':'a@example.test','password':'wrong'}).status_code==401
    assert client.post('/api/auth/login',json={'email':'a@example.test','password':'long-password-123'}).status_code==200

def test_rounding_unknowns_selection_and_actuals(authed,job):
    r=authed.post('/api/jobs/'+job['id']+'/quotes',json=quote());assert r.status_code==201,r.text
    q=r.json();assert q['analysis']['known_subtotal']=='0.30';assert q['analysis']['additional_tax']=='0.02';assert q['analysis']['confirmed_total']=='0.32'
    assert authed.post('/api/jobs/'+job['id']+'/selection',json={'quote_id':q['id']}).status_code==200
    updated=authed.put('/api/quotes/'+q['id'],json=quote(tax_mode='unspecified')).json();assert updated['analysis']['confirmed_total'] is None
    assert authed.get('/api/jobs/'+job['id']).json()['selected_quote_id'] is None
    assert authed.post('/api/jobs/'+job['id']+'/selection',json={'quote_id':q['id']}).status_code==400
    for bad in ['-1.00','0.001']:
        assert authed.post('/api/jobs/'+job['id']+'/quotes',json=quote(items=[{'label':'Bad','amount':bad}])).status_code==422
    e=authed.post('/api/jobs/'+job['id']+'/expenses',json={'label':'Paid','amount':'40.25','paid_on':'2026-11-09'});assert e.status_code==201
    assert authed.get('/api/jobs/'+job['id']).json()['actual_total']=='40.25'
    assert authed.delete('/api/expenses/'+e.json()['id']).status_code==204
    pdf=authed.get('/api/jobs/'+job['id']+'/report.pdf');assert pdf.status_code==200;assert pdf.content.startswith(b'%PDF')

def test_cross_account_isolation(authed,job):
    q=authed.post('/api/jobs/'+job['id']+'/quotes',json=quote()).json()
    other=TestClient(app,headers={'X-QuoteClear':'1'});other.post('/api/auth/register',json={'name':'Other','email':'other@example.test','password':'long-password-123'})
    assert other.get('/api/jobs').json()==[]
    for path in [f"/api/jobs/{job['id']}",f"/api/jobs/{job['id']}/report.pdf"]:assert other.get(path).status_code==404
    assert other.put('/api/quotes/'+q['id'],json=quote()).status_code==404
    assert other.delete('/api/quotes/'+q['id']).status_code==404
    assert other.post('/api/jobs/'+job['id']+'/quotes',json=quote()).status_code==404

def test_document_extraction_and_exact_provenance(authed,job):
    stream=io.BytesIO();c=canvas.Canvas(stream);c.drawString(50,750,'AC service AED 250.00. Labour included.');c.save()
    uploaded=authed.post('/api/jobs/'+job['id']+'/documents',files={'file':('../quote.pdf',stream.getvalue(),'application/pdf')});assert uploaded.status_code==202,uploaded.text
    d=uploaded.json();assert d['state']=='queued';assert '/' not in d['filename'];assert process_next()
    doc=authed.get('/api/documents/'+d['id']).json();assert doc['state']=='ready';candidate=doc['pages'][0]['candidates'][0];assert candidate['amount']=='250.00'
    data=quote(document_id=d['id'],items=[{'label':'Service','kind':'Labour','pricing':'fixed','amount':candidate['amount'],'reviewed':True,'source_page':1,'source_excerpt':candidate['excerpt']}])
    assert authed.post('/api/jobs/'+job['id']+'/quotes',json=data).status_code==201
    data['items'][0]['source_excerpt']='invented source text';assert authed.post('/api/jobs/'+job['id']+'/quotes',json=data).status_code==400
    assert authed.get('/api/documents/'+d['id']+'/file').content==stream.getvalue()
    assert authed.post('/api/jobs/'+job['id']+'/documents',files={'file':('bad.pdf',b'<script>bad</script>','application/pdf')}).status_code==415

def test_images_are_honestly_flagged_for_manual_entry(authed,job):
    d=authed.post('/api/jobs/'+job['id']+'/documents',files={'file':('image.png',b'\x89PNG\r\n\x1a\nfake','image/png')}).json();assert process_next();assert authed.get('/api/documents/'+d['id']).json()['state']=='ocr_needed'
