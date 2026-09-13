import os
os.environ['DATABASE_URL']='sqlite:///./test.db'
os.environ['JWT_SECRET']='test-secret'
import jwt, pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def token():
    return jwt.encode({'sub':'missing','cpf':'52998224725','iss':'oficina-auth'}, 'test-secret', algorithm='HS256')
