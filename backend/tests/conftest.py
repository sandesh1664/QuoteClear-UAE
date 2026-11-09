import os,tempfile
from pathlib import Path
root=Path(tempfile.mkdtemp(prefix='quoteclear-test-'))
os.environ['DATABASE_URL']='sqlite:///'+str(root/'test.db')
os.environ['STORAGE_DIR']=str(root/'files')
os.environ['ALLOWED_ORIGINS']='http://testserver'
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base,engine
@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
@pytest.fixture
def client():
    with TestClient(app,headers={'X-QuoteClear':'1'}) as c:yield c
@pytest.fixture
def authed(client):
    r=client.post('/api/auth/register',json={'name':'Sample','email':'sample@example.test','password':'StrongTestPass123!'})
    assert r.status_code==201,r.text
    return client
@pytest.fixture
def job(authed):
    return authed.post('/api/jobs',json={'title':'AC repair','category':'AC & maintenance','emirate':'Dubai'}).json()
