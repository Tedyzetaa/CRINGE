from fastapi.testclient import TestClient
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import app
from db.test_db import init_test_db
init_test_db()

client = TestClient(app)

def test_create_group():
    # Primeiro, cria um bot para vincular
    bot_resp = client.post("/bots", json={
        "creator_id": "test-user",
        "name": "Bot do Grupo",
        "gender": "Masculino",
        "introduction": "Bot para grupo.",
        "personality": "Ajuda em grupo.",
        "welcome_message": "Bem-vindo ao grupo!",
        "conversation_context": "Contexto de grupo.",
        "context_images": [],
        "system_prompt": "Você é um bot de grupo.",
        "ai_config": {"temperature": 0.6, "max_output_tokens": 512}
    })
    bot_id = bot_resp.json()["bot_id"]

    response = client.post("/groups", json={
        "name": "Grupo Teste",
        "scenario": "Cenário de teste.",
        "bot_ids": [bot_id]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Grupo Teste"

def test_list_groups():
    response = client.get("/groups")
    assert response.status_code == 200
    assert isinstance(response.json(), list)