from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .config import settings
from .database import engine
from .routers import auth,jobs,documents,reports
app=FastAPI(title='QuoteClear UAE API',version='1.0.0',docs_url='/api/docs',openapi_url='/api/openapi.json')
app.add_middleware(CORSMiddleware,allow_origins=settings().origins,allow_credentials=True,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Content-Type','X-QuoteClear'])
@app.middleware('http')
async def security_headers(request:Request,call_next):
    if request.method in ('POST','PUT','PATCH','DELETE'):
        origin=request.headers.get('origin','').rstrip('/')
        if request.headers.get('X-QuoteClear')!='1' or (origin and origin not in settings().origins):return JSONResponse({'detail':'Request origin or CSRF header rejected'},status_code=403)
    response=await call_next(request);response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='same-origin';response.headers['Cache-Control']='no-store';return response
@app.get('/api/health')
def health():
    with engine.connect() as conn:conn.execute(text('SELECT 1'))
    return {'status':'ok','service':'QuoteClear UAE'}
for router in (auth.router,jobs.router,documents.router,reports.router):app.include_router(router,prefix='/api')
