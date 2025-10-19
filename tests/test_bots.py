from fastapi.testclient import TestClient
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import app
from db.test_db import init_test_db
init_test_db()

client = TestClient(app)

def test_create_bot():
    response = client.post("/bots", json={
        "creator_id": "test-user",
        "name": "Bot Teste",
        "gender": "Indefinido",
        "introduction": "Sou um bot de testes.",
        "personality": "Respondo com lógica e clareza.",
        "welcome_message": "Olá, aventureiro!",
        "conversation_context": "Foco em testes.",
        "context_images": [],
        "system_prompt": "Você é um bot de testes.",
        "ai_config": {"temperature": 0.5, "max_output_tokens": 256}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Bot Teste"

def test_list_bots():
    response = client.get("/bots")
    assert response.status_code == 200
    assert isinstance(response.json(), list)