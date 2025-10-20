# c:\cringe\3.0\routers\bots.py (ATUALIZADO)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import json
from database import get_db
# Puxe os schemas e modelos do models.py
from models import Bot, BotRead, BotCreate 

router = APIRouter(prefix="/bots", tags=["Bots"])

@router.get("/", response_model=list[BotRead])
def list_bots(db: Session = Depends(get_db)):
    """Lista todos os bots do banco de dados."""
    return db.query(Bot).all()

@router.post("/", response_model=BotRead)
def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    """Cria um novo bot, serializando os campos JSON/Dicts."""
    
    # Lógica de serialização
    tags_json = json.dumps(bot.tags)
    ai_config_json = json.dumps(bot.ai_config)
    context_images_json = json.dumps(bot.context_images)
    
    db_bot = Bot(
        name=bot.name,
        creator_id=bot.creator_id,
        gender=bot.gender,
        introduction=bot.introduction,
        personality=bot.personality,
        welcome_message=bot.welcome_message,
        
        # 💡 Novos campos
        avatar_url=bot.avatar_url,
        tags=tags_json, # Salva a lista de tags como JSON string
        # ----------------
        
        conversation_context=bot.conversation_context,
        system_prompt=bot.system_prompt,
        context_images=context_images_json, 
        ai_config=ai_config_json
    )
    
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    
    return db_bot