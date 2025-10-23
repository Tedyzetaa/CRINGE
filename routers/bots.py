import uuid
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database import SessionLocal
from models import Bot as DBBot, AICofig as DBAiConfig # Importa modelos do DB
# Importa o cliente de AI refatorado
from services.ai_client import AI_CLIENT 

# Cria o roteador FastAPI
router = APIRouter(
    prefix="/bots",
    tags=["bots"],
)

# --- Schemas Pydantic para Input/Output ---

class AIConfigSchema(BaseModel):
    """Schema para a configuração de IA do bot."""
    temperature: float = Field(..., description="Criatividade da IA (0.0 a 1.0)")
    max_output_tokens: int = Field(..., description="Número máximo de tokens de saída")

class BotBase(BaseModel):
    """Base para criação de bots."""
    creator_id: str
    name: str
    gender: str
    introduction: str
    personality: str
    welcome_message: str
    avatar_url: str
    tags: List[str] = Field(default_factory=list)
    conversation_context: str
    context_images: str
    system_prompt: str
    ai_config: AIConfigSchema

class BotCreate(BotBase):
    """Schema para criação de um novo bot."""
    pass

class BotResponse(BotBase):
    """Schema de resposta com ID."""
    id: str
    
    class Config:
        orm_mode = True

class ChatMessage(BaseModel):
    """Schema para uma mensagem no histórico de chat."""
    role: str = Field(..., description="Função: 'user' ou 'bot'")
    content: str = Field(..., description="Conteúdo da mensagem")

class ChatRequest(BaseModel):
    """Schema para a requisição de chat."""
    user_message: str = Field(..., description="A última mensagem do usuário.")
    chat_history: List[ChatMessage] = Field(..., description="Histórico completo da conversa.")

class ChatResponse(BaseModel):
    """Schema para a resposta do chat."""
    response: str
    model_used: str

class BotListFile(BaseModel):
    """Schema para a importação de lista de bots (PUT /bots/import)"""
    bots: List[BotResponse]

# --- Funções de Dependência ---

def get_db():
    """Dependência para obter uma sessão de banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Rotas da API ---

@router.get("/", response_model=List[BotResponse])
def get_all_bots(db: Session = Depends(get_db)):
    """Retorna todos os bots registrados."""
    bots_db = db.query(DBBot).all()
    if not bots_db:
        # Retorna uma lista vazia, mas não um erro 404, pois a lista pode estar vazia
        return [] 
    
    # Mapeia para o schema de resposta, garantindo que o ai_config seja aninhado corretamente
    response_bots = []
    for bot in bots_db:
        bot_dict = bot.__dict__
        bot_dict['ai_config'] = bot.ai_config.__dict__
        response_bots.append(BotResponse(**bot_dict))
        
    return response_bots

@router.get("/{bot_id}", response_model=BotResponse)
def get_bot(bot_id: str, db: Session = Depends(get_db)):
    """Retorna um bot pelo ID."""
    bot = db.query(DBBot).filter(DBBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    
    # Mapeia para o schema de resposta
    bot_dict = bot.__dict__
    bot_dict['ai_config'] = bot.ai_config.__dict__
    return BotResponse(**bot_dict)

@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
def create_bot(bot: BotCreate, db: Session = Depends(get_db)):
    """Cria um novo bot."""
    
    # 1. Cria a configuração de IA
    ai_config_db = DBAiConfig(
        temperature=bot.ai_config.temperature,
        max_output_tokens=bot.ai_config.max_output_tokens
    )
    
    # 2. Cria a instância do bot
    new_bot_id = str(uuid.uuid4())
    bot_db = DBBot(
        id=new_bot_id,
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
        ai_config=ai_config_db
    )
    
    # 3. Salva no DB
    db.add(bot_db)
    db.commit()
    db.refresh(bot_db)
    
    # 4. Retorna a resposta
    bot_dict = bot_db.__dict__
    bot_dict['ai_config'] = ai_config_db.__dict__
    return BotResponse(**bot_dict)


@router.put("/import", response_model=Dict[str, Any])
def import_bots(bot_list: BotListFile, db: Session = Depends(get_db)):
    """Importa uma lista de bots, limpando a tabela existente (CUIDADO)."""
    
    imported_count = 0
    
    try:
        # Opção 1: Limpar e Recriar (Mais simples para o Render/SQLite)
        db.query(DBBot).delete()
        db.query(DBAiConfig).delete()
        db.commit()

        for bot_data in bot_list.bots:
            # 1. Cria a configuração de IA
            ai_config_db = DBAiConfig(
                temperature=bot_data.ai_config.temperature,
                max_output_tokens=bot_data.ai_config.max_output_tokens
            )
            
            # 2. Cria a instância do bot
            bot_db = DBBot(
                id=str(uuid.uuid4()), # Sempre gera novo ID na importação para evitar colisões
                creator_id=bot_data.creator_id,
                name=bot_data.name,
                gender=bot_data.gender,
                introduction=bot_data.introduction,
                personality=bot_data.personality,
                welcome_message=bot_data.welcome_message,
                avatar_url=bot_data.avatar_url,
                tags=bot_data.tags,
                conversation_context=bot_data.conversation_context,
                context_images=bot_data.context_images,
                system_prompt=bot_data.system_prompt,
                ai_config=ai_config_db
            )
            
            db.add(bot_db)
            imported_count += 1
        
        db.commit()
        return {"success": True, "imported_count": imported_count, "message": "Importação concluída com sucesso."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro durante a importação: {e}")


@router.post("/chat/{bot_id}", response_model=ChatResponse)
async def chat_with_bot(bot_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """
    Processa uma requisição de chat, chama a IA e retorna a resposta.
    """
    
    # 1. Busca o bot no DB
    bot = db.query(DBBot).filter(DBBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot não encontrado")

    # 2. Monta o contexto da IA
    system_prompt = bot.system_prompt
    user_message = request.user_message
    
    # O histórico deve incluir a mensagem de boas-vindas do bot, 
    # pois o frontend a envia no 'chat_history' para manter a persona.
    chat_history = [msg.dict() for msg in request.chat_history]

    # VILANAGEM DE SEGURANÇA: Limita o histórico de chat para evitar estouro de tokens e custo
    # Mantém apenas as últimas 8 mensagens (4 pares de user/bot) + a mensagem atual do usuário
    MAX_MESSAGES_HISTORY = 8
    if len(chat_history) > MAX_MESSAGES_HISTORY:
        # Mantém apenas as últimas N-1 mensagens + a mensagem atual do usuário (que é a última)
        chat_history = chat_history[-MAX_MESSAGES_HISTORY:] 

    # 3. Chama o Serviço de AI
    try:
        # A nova lógica de chamada e retry está encapsulada no AI_CLIENT
        ai_response = await AI_CLIENT.generate_response(
            system_prompt=system_prompt,
            user_message=user_message,
            chat_history=chat_history,
            ai_config={
                "temperature": bot.ai_config.temperature,
                "max_output_tokens": bot.ai_config.max_output_tokens
            }
        )
        
        return ChatResponse(response=ai_response, model_used=AI_CLIENT.model_id)

    except HTTPException as e:
        # Re-lança exceções do cliente AI (400, 429, 503, etc.)
        raise e
    except Exception as e:
        # Erros inesperados
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento do chat: {e}")
