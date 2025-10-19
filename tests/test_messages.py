from fastapi.testclient import TestClient
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import app
from db.test_db import init_test_db
init_test_db()

client = TestClient(app)

def test_send_message():
    # Cria usuário
    client.post("/users", json={
        "user_id": "msg-user",
        "username": "Mensageiro",
        "is_admin": False
    })

    # Cria grupo
    group_resp = client.post("/groups", json={
        "name": "Grupo Mensagem",
        "scenario": "Testando mensagens.",
        "bot_ids": []
    })
    group_id = group_resp.json()["group_id"]

    # Envia mensagem
    response = client.post("/groups/send_message", json={
        "group_id": group_id,
        "sender_id": "msg-user",
        "text": "Olá, grupo!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Olá, grupo!"

def test_list_group_messages():
    groups = client.get("/groups").json()
    if groups:
        group_id = groups[0]["group_id"]
        response = client.get(f"/groups/{group_id}/messages")
        assert response.status_code == 200
        assert isinstance(response.json(), list)