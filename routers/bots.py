# routers/bots.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os

# CORRIGIDO: Usando AIConfig
from models import Bot as DBBot, AIConfig as DBAiConfig 
from database import get_db
from services.ai_client import AIClient 

DEFAULT_MODEL_ID = "HuggingFaceH4/zephyr-7b-beta"
AI_CLIENT = AIClient(model_id=DEFAULT_MODEL_ID)

router = APIRouter(
    prefix="/bots",
    tags=["bots"],
)

# --- Schemas Pydantic ---

class ChatMessage(BaseModel):
    role: str = Field(..., description="O papel da mensagem (user ou assistant).")
    content: str = Field(..., description="O conteúdo da mensagem.")

class ChatRequest(BaseModel):
    user_message: str = Field(..., description="A nova mensagem do usuário.")
    chat_history: List[ChatMessage] = Field([], description="O histórico completo de mensagens ANTERIORES.") # Corrigida a descrição

class AIConfigSchema(BaseModel):
    model_id: str
    style: str
    temperature: float = 0.9

class BotSchema(BaseModel):
    id: int
    name: str
    role: str
    persona: str
    ai_config: AIConfigSchema
    
    class Config:
        orm_mode = True

# --- Funções de Ajuda ---

def get_bot_by_id(db: Session, bot_id: int):
    bot = db.query(DBBot).filter(DBBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado.")
    return bot

# --- Rotas da API ---

@router.get("/", response_model=List[BotSchema])
def list_bots(db: Session = Depends(get_db)):
    bots = db.query(DBBot).all()
    return bots

@router.get("/{bot_id}", response_model=BotSchema)
def get_bot(bot_id: int, db: Session = Depends(get_db)):
    bot = get_bot_by_id(db, bot_id)
    return bot

@router.post("/chat/{bot_id}")
def chat_with_bot(bot_id: int, request: ChatRequest, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Envia uma mensagem ao bot, gera a resposta da AI e retorna a resposta.
    """
    bot = get_bot_by_id(db, bot_id)
    
    system_prompt = f"Você é {bot.name}, um {bot.role} com a seguinte persona: '{bot.persona}'. Seu estilo de resposta deve ser: '{bot.ai_config.style}'. Responda estritamente no papel."

    MAX_HISTORY_MESSAGES = 10 
    history_for_api = [msg.dict() for msg in request.chat_history]
    
    if len(history_for_api) > MAX_HISTORY_MESSAGES:
         history_for_api = history_for_api[-MAX_HISTORY_MESSAGES:]

    try:
        # 2. Gera a resposta usando o serviço dedicado
        ai_response = AI_CLIENT.generate_response(
            system_prompt=system_prompt,
            chat_history=history_for_api,
            user_message=request.user_message
        )
        
        return {"ai_response": ai_response}

    except Exception as e:
        print(f"ERRO CRÍTICO no chat: {e}")
        raise HTTPException(
            status_code=500, 
            detail="A API de AI falhou. Tente novamente mais tarde ou verifique a HUGGINGFACE_API_KEY."
        )
