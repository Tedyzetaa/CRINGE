# routers/bots.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import BotCreate, Bot as BotSchema # Renomeado Bot para BotSchema para evitar conflito
from models import Bot as BotModel # O modelo SQLAlchemy
# 💡 CORREÇÃO AQUI: Importa get_db e SessionLocal de database
from database import SessionLocal, get_db
import uuid
from typing import List

# Importa o schema Bot do seu projeto (assumindo que ele está definido em schemas.py)
# Se você tiver um arquivo schemas.py, garanta que ele tenha o Bot.

router = APIRouter(
    prefix="/bots",
    tags=["bots"],
)

# A função get_db foi movida para database.py para centralização.
# --- Funções CRUD (Internas) ---

def get_bot(db: Session, bot_id: str):
    return db.query(BotModel).filter(BotModel.id == bot_id).first()

def get_bots(db: Session, skip: int = 0, limit: int = 100):
    return db.query(BotModel).offset(skip).limit(limit).all()

# --- Rotas da API ---

@router.post("/", response_model=BotSchema, status_code=201)
def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    """Cria um novo Bot (IA) no sistema."""
    
    # O Pydantic (BotCreate) garante que tags é uma List[str] e ai_config é um Dict.
    # Passamos esses objetos Python diretamente para o modelo SQLAlchemy.
    # O tipo JSONEncodedDict no models.py cuidará da serialização (Python -> JSON string).
    
    # Converte o Pydantic BaseModel para um dicionário Python simples para ai_config
    # Nota: Usamos .dict() ou .model_dump() (dependendo da versão do Pydantic)
    # Aqui, assumimos uma versão que ainda usa .dict() ou que BotCreate possui um método .dict()
    try:
        ai_config_dict = bot.ai_config.dict() if bot.ai_config else {}
    except AttributeError:
        # Para Pydantic v2+
        ai_config_dict = bot.ai_config.model_dump() if bot.ai_config else {}
    
    db_bot = BotModel(
        id=str(uuid.uuid4()),
        creator_id=bot.creator_id,
        name=bot.name,
        gender=bot.gender,
        introduction=bot.introduction,
        personality=bot.personality,
        welcome_message=bot.welcome_message,
        avatar_url=bot.avatar_url,
        tags=bot.tags, 
        conversation_context=bot.conversation_context,
        context_images=bot.context_images,
        system_prompt=bot.system_prompt,
        ai_config=ai_config_dict # Dicionário Python
    )
    
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return db_bot

@router.get("/", response_model=List[BotSchema])
def read_bots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista todos os Bots disponíveis."""
    bots = get_bots(db, skip=skip, limit=limit)
    return bots

@router.get("/{bot_id}", response_model=BotSchema)
def read_bot(bot_id: str, db: Session = Depends(get_db)):
    """Busca um Bot específico pelo ID."""
    db_bot = get_bot(db, bot_id=bot_id)
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    return db_bot
