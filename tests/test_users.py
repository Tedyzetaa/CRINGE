from fastapi.testclient import TestClient
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import app
from db.test_db import init_test_db
init_test_db()

client = TestClient(app)

def test_create_user():
    response = client.post("/users", json={
        "user_id": "test-user",
        "username": "Testador",
        "is_admin": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test-user"
    assert data["username"] == "Testador"

def test_list_users():
    response = client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)