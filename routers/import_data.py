# c:\cringe\3.0\routers\import_data.py (NOVO ARQUIVO)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Bot, Group # Importe todos os seus modelos
import json
import os

router = APIRouter(prefix="/admin", tags=["Admin"])
JSON_FILE = os.path.join(os.path.dirname(__file__), "..", "exported_test_data.json")

# ⚠️ SEGURANÇA: Este endpoint deve ser protegido com senha em produção!
@router.post("/import-tests")
def import_test_data(db: Session = Depends(get_db)):
    """Lê o arquivo JSON e recria os usuários e bots no banco de dados."""
    
    if not os.path.exists(JSON_FILE):
        raise HTTPException(status_code=404, detail=f"Arquivo de dados não encontrado em: {JSON_FILE}")

    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Erro ao ler JSON de dados de teste.")

    results = {"users_created": 0, "bots_created": 0}

    # 1. Importar Usuários
    for user_data in data.get('users', []):
        if not db.query(User).filter(User.id == user_data['id']).first():
            db_user = User(id=user_data['id'], name=user_data['name'])
            db.add(db_user)
            results['users_created'] += 1

    # 2. Importar Bots
    for bot_data in data.get('bots', []):
        if not db.query(Bot).filter(Bot.id == bot_data['id']).first():
            db_bot = Bot(**bot_data)
            db.add(db_bot)
            results['bots_created'] += 1
            
    db.commit()
    
    return {"status": "Importação de dados de teste concluída.", "details": results}