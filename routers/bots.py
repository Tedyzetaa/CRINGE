# routers/bots.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os

# CORRIGIDO: Removida a importação de AIConfig. Usamos apenas Bot.
from models import Bot as DBBot
from database import get_db
from services.ai_client import AIClient 

# O modelo padrão deve ser o mesmo usado na lógica de fallback do models.py
DEFAULT_MODEL_ID = "gemini-2.5-flash" 
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
    # Corrigida a descrição para ser mais clara sobre o histórico
    chat_history: List[ChatMessage] = Field([], description="O histórico completo de mensagens ANTERIORES.") 

class AIConfigSchema(BaseModel):
    """
    Schema Pydantic para as configurações de AI armazenadas no campo JSON.
    Adicionado max_output_tokens, temperature e model_id, que são esperados do JSON.
    """
    model_id: str = Field(..., description="O ID do modelo de AI a ser usado.")
    temperature: float = Field(0.7, description="Temperatura de amostragem.")
    max_output_tokens: int = Field(512, description="Limite máximo de tokens de saída.")
    
    # Adicionando 'style', se for usado na lógica do system_prompt.
    # Se 'style' não estiver no JSON, ele deve ser opcional ou o system_prompt deve ser ajustado.
    # Assumindo que 'style' ou 'persona' do Bot é usado para o prompt.
    # Para consistência, vou remover 'style' do AIConfigSchema se não estiver no JSON.
    # No entanto, vamos adicionar os campos do Bot que são usados no system prompt original.
    
class BotSchema(BaseModel):
    """
    Schema que reflete o formato de saída do método to_dict() do modelo Bot.
    """
    id: str
    name: str
    creator_id: str
    gender: Optional[str] = None
    introduction: Optional[str] = None
    personality: Optional[str] = None
    welcome_message: Optional[str] = None
    avatar_url: Optional[str] = None
    tags: List[str]
    conversation_context: Optional[str] = None
    context_images: Optional[str] = None
    system_prompt: Optional[str] = None
    
    # O campo ai_config agora é um Dict[str, Any], espelhando bot.get_ai_config()
    # Em vez de um schema Pydantic aninhado, usamos Dict[str, Any] para flexibilidade,
    # pois a estrutura é lida dinamicamente do JSON.
    ai_config: Dict[str, Any]

    class Config:
        # Corrigido: orm_mode está obsoleto, use from_attributes
        from_attributes = True

# --- Funções de Ajuda ---

def get_bot_by_id(db: Session, bot_id: str) -> DBBot: # ID deve ser str
    """Busca o bot e garante que o ID seja tratado como string (UUID)."""
    # Corrigido: O Bot ID no DB agora é String (UUID) conforme models.py
    bot = db.query(DBBot).filter(DBBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado.")
    return bot

# --- Rotas da API ---

@router.get("/", response_model=List[BotSchema])
def list_bots(db: Session = Depends(get_db)):
    # Usamos o to_dict() para garantir que a saída seja compatível com BotSchema
    bots = db.query(DBBot).all()
    return [bot.to_dict() for bot in bots]

@router.get("/{bot_id}", response_model=BotSchema)
def get_bot(bot_id: str, db: Session = Depends(get_db)): # ID deve ser str
    bot = get_bot_by_id(db, bot_id)
    # Usamos o to_dict() para garantir que a saída seja compatível com BotSchema
    return bot.to_dict() 

@router.post("/chat/{bot_id}")
def chat_with_bot(bot_id: str, request: ChatRequest, db: Session = Depends(get_db)) -> Dict[str, str]: # ID deve ser str
    """
    Envia uma mensagem ao bot, gera a resposta da AI e retorna a resposta.
    """
    bot = get_bot_by_id(db, bot_id)
    
    # 1. Extrai as configurações de AI e o prompt do Bot
    ai_config = bot.get_ai_config()
    
    # O system_prompt é usado diretamente, pois agora está armazenado como um campo no Bot
    # Se o system_prompt do DB for None, usamos um fallback
    system_prompt = bot.system_prompt
    if not system_prompt:
        system_prompt = f"Você é o bot '{bot.name}' com a personalidade: '{bot.personality}'. Responda de forma útil e envolvente."

    MAX_HISTORY_MESSAGES = 10 
    history_for_api = [msg.dict() for msg in request.chat_history]
    
    if len(history_for_api) > MAX_HISTORY_MESSAGES:
         history_for_api = history_for_api[-MAX_HISTORY_MESSAGES:]

    try:
        # 2. Gera a resposta usando o serviço dedicado
        ai_response = AI_CLIENT.generate_response(
            system_prompt=system_prompt,
            chat_history=history_for_api,
            user_message=request.user_message,
            # Passando as configs dinamicamente do JSON
            model_id=ai_config.get("model_id", DEFAULT_MODEL_ID), 
            temperature=ai_config.get("temperature", 0.7), 
            max_output_tokens=ai_config.get("max_output_tokens", 512)
        )
        
        return {"ai_response": ai_response}

    except Exception as e:
        print(f"ERRO CRÍTICO no chat para Bot {bot_id}: {e}")
        # Melhorei a mensagem de erro para o usuário final
        raise HTTPException(
            status_code=500, 
            detail="Ocorreu um erro ao gerar a resposta da AI. Verifique as configurações do modelo ou a chave da API."
        )
