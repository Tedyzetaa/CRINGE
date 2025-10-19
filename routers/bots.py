# c:\cringe\3.0\routers\bots.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import json
from database import get_db
from models import Bot, BotRead, BotCreate

router = APIRouter(prefix="/bots", tags=["Bots"])

@router.get("/", response_model=list[BotRead])
def list_bots(db: Session = Depends(get_db)):
    """Lista todos os bots do banco de dados."""
    return db.query(Bot).all()

@router.post("/", response_model=BotRead)
def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    """Cria um novo bot, serializando os campos JSON/Dicts."""
    
    # Cria o objeto ORM, serializando campos complexos
    db_bot = Bot(
        name=bot.name,
        creator_id=bot.creator_id,
        gender=bot.gender,
        introduction=bot.introduction,
        personality=bot.personality,
        welcome_message=bot.welcome_message,
        conversation_context=bot.conversation_context,
        system_prompt=bot.system_prompt,
        # Serializa listas/dicts para TEXTO
        context_images=json.dumps(bot.context_images), 
        ai_config=json.dumps(bot.ai_config)
    )
    
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    
    return db_bot