# routers/bots.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import os

# TENTA CORRIGIR O ERRO DE IMPORTAÇÃO (NameError: AIService)
# Em ambientes de execução (como Uvicorn/Render), imports relativos (..) falham.
# Tentamos usar o nome do módulo diretamente, se possível.

try:
    # 1. Tentativa de importação para ambientes de teste e execução principal (com caminho absoluto)
    from services.ai_service import AIService 
    from database import get_db
    from models import Bot
    # Schemas são tipicamente importados no início do projeto, assumindo que estão em schemas.py
    # Se você tem um subdiretório schemas, mude para: from schemas.seu_arquivo import ...
    from schemas import ChatRequest, ChatResponse, BotDisplay
except ImportError as e:
    # 2. Fallback para imports relativos, que funcionam em alguns contextos (ex: dentro de testes)
    try:
        from ..database import get_db
        from ..models import Bot
        from ..schemas import ChatRequest, ChatResponse, BotDisplay
        from ..services.ai_service import AIService
    except ImportError as e_relative:
        print(f"ERRO CRÍTICO DE IMPORTAÇÃO: Não foi possível importar AIService ou componentes do DB. Isso geralmente significa que o servidor (uvicorn) não está sendo iniciado a partir do diretório raiz do projeto.")
        # Se a importação falhar, defina uma classe placeholder para evitar NameError
        class AIService:
            def generate_response(self, *args, **kwargs):
                raise NotImplementedError("AIService não foi carregado corretamente.")
        
router = APIRouter(
    prefix="/bots",
    tags=["Bots"],
)

# Inicializa o serviço de IA.
ai_service = AIService()

# --- Rotas de Bots (GET /bots) ---

@router.get("/", response_model=List[BotDisplay])
def list_bots(db: Session = Depends(get_db)):
    """Lista todos os bots disponíveis no banco de dados."""
    bots = db.query(Bot).all()
    
    result = []
    for bot in bots:
        # Desserializa os campos JSON
        try:
            tags = json.loads(bot.tags)
        except (json.JSONDecodeError, TypeError):
            tags = []
        
        bot_data = {
            "id": bot.id,
            "name": bot.name,
            "gender": bot.gender,
            "avatar_url": bot.avatar_url,
            "personality": bot.personality,
            "welcome_message": bot.welcome_message,
            "tags": tags,
        }
        result.append(BotDisplay(**bot_data))
        
    return result

# --- Rotas de Chat (POST /bots/chat/{bot_id}) ---

@router.post("/chat/{bot_id}", response_model=ChatResponse)
def chat_with_bot(bot_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """Envia uma mensagem para o bot e recebe a resposta da IA."""
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot com ID '{bot_id}' não encontrado.")
    
    try:
        ai_config = json.loads(bot.ai_config_json)
    except (json.JSONDecodeError, TypeError):
        ai_config = {}

    try:
        # Chama o serviço de IA
        ai_response = ai_service.generate_response(
            bot_data=bot,
            ai_config=ai_config,
            user_message=request.user_message,
            chat_history=request.chat_history
        )
        
        return ChatResponse(ai_response=ai_response)
    
    except NotImplementedError as e:
        # Erro gerado pelo nosso placeholder, significa que a importação falhou
        raise HTTPException(status_code=500, detail="AIService não foi carregado. Verifique os logs de importação.")
    except Exception as e:
        error_detail = f"A API de IA falhou. Erro: {e}"
        print(f"ERRO DE CHAT: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)
