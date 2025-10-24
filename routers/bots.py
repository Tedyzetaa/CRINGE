# routers/bots.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import json
import os

# Supondo que você tenha um arquivo db.py com get_db
try:
    from ..database import get_db
    from ..models import Bot # Importa o modelo Bot
    from ..schemas import BotBase, BotDisplay, ChatRequest, ChatResponse # Supondo que existam esses Schemas
    from ..services.ai_service import AIService # Serviço de IA
except ImportError as e:
    # Apenas para garantir que os imports funcionem no ambiente de execução
    print(f"Erro de importação no routers/bots.py: {e}")
    
router = APIRouter(
    prefix="/bots",
    tags=["Bots"],
)

# Inicializa o serviço de IA.
# A chave Hugging Face deve ser lida da variável de ambiente no serviço
ai_service = AIService()

# --- Rotas de Bots (GET /bots) ---

@router.get("/", response_model=List[BotDisplay])
def list_bots(db: Session = Depends(get_db)):
    """Lista todos os bots disponíveis no banco de dados."""
    bots = db.query(Bot).all()
    
    # Mapeia para o schema de display, desserializando as configs de AI e tags
    result = []
    for bot in bots:
        # 1. Desserializa ai_config_json de volta para um dict
        try:
            ai_config = json.loads(bot.ai_config_json)
        except (json.JSONDecodeError, TypeError):
            ai_config = {}
            
        # 2. Desserializa tags de volta para uma lista
        try:
            tags = json.loads(bot.tags)
        except (json.JSONDecodeError, TypeError):
            tags = []
        
        # 3. Cria o objeto para o schema de resposta
        bot_data = {
            "id": bot.id,
            "name": bot.name,
            "gender": bot.gender,
            "avatar_url": bot.avatar_url,
            "personality": bot.personality,
            "welcome_message": bot.welcome_message,
            "tags": tags, # Incluído de volta como lista
            # Ai_config não é necessário no display, mas mantemos para referência
        }
        result.append(BotDisplay(**bot_data))
        
    return result

# --- Rotas de Chat (POST /bots/chat/{bot_id}) ---

@router.post("/chat/{bot_id}", response_model=ChatResponse)
def chat_with_bot(bot_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """Envia uma mensagem para o bot e recebe a resposta da IA."""
    
    # 1. Busca o Bot no DB
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot com ID '{bot_id}' não encontrado.")
    
    # 2. Desserializa a configuração de IA
    try:
        ai_config = json.loads(bot.ai_config_json)
    except (json.JSONDecodeError, TypeError):
        ai_config = {}

    # 3. Chama o serviço de IA
    try:
        ai_response = ai_service.generate_response(
            bot_data=bot,
            ai_config=ai_config,
            user_message=request.user_message,
            chat_history=request.chat_history
        )
        
        return ChatResponse(ai_response=ai_response)
    
    except Exception as e:
        # Captura qualquer erro do serviço de IA (como Timeout/ProtocolError do Hugging Face)
        error_detail = f"A API Hugging Face falhou após várias tentativas (Timeout/Rede/Erro de Dados). Erro: {e}"
        print(f"ERRO DE CHAT: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)
