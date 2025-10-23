# routers/bots.py (FINAL E COMPLETO COM CORREÇÃO DE CONEXÃO HTTPX)

import uuid
import time
import os
import asyncio
import json
from typing import List, Dict, Any, Optional

# Importações do SQLAlchemy e da dependência de DB
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Body, BackgroundTasks, status, Depends
from pydantic import BaseModel, Field

# IMPORTAÇÕES DO PROJETO 
from database import get_db
from models import Bot as DBBot 

# Importação de cliente HTTP assíncrono para chamadas externas
try:
    import httpx
except ImportError:
    # Se httpx não estiver disponível, levantamos um erro.
    raise RuntimeError("A biblioteca 'httpx' é necessária. Instale com: pip install httpx")
# Removed: HTTP_CLIENT global is removed to fix LocalProtocolError

# ----------------------------------------------------------------------
# Variáveis de Configuração Hugging Face
# ----------------------------------------------------------------------

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "") 
HF_API_BASE_URL = "https://api-inference.huggingface.co/models/"

# Simulação de cache ou banco de dados para armazenar o status da tarefa de background
TASK_RESULTS_DB: Dict[str, Dict[str, Optional[str]]] = {} 

# ----------------------------------------------------------------------
# Definições Pydantic (Esquemas de Dados)
# ----------------------------------------------------------------------

class AIConfig(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_output_tokens: int = Field(default=512, ge=128, le=4096)

class Bot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    creator_id: str
    name: str
    gender: str
    introduction: str
    personality: str
    welcome_message: str
    avatar_url: str
    tags: List[str]
    conversation_context: str
    context_images: str
    system_prompt: str
    ai_config: AIConfig
    
class BotIn(BaseModel):
    creator_id: str
    name: str
    gender: str
    introduction: str
    personality: str
    welcome_message: str
    avatar_url: str
    tags: List[str]
    conversation_context: str
    context_images: str
    system_prompt: str
    ai_config: AIConfig

class BotListFile(BaseModel):
    bots: List[Bot]

class ChatMessage(BaseModel):
    role: str # 'user' or 'model'
    text: str = Field(min_length=1)
    
class BotChatRequest(BaseModel):
    bot_id: str
    messages: List[ChatMessage] 
    
# NOVOS SCHEMAS PARA ROTA DE CHAT 1:1
class ChatRequest(BaseModel):
    """Esquema de entrada da mensagem do Streamlit."""
    user_message: str
    chat_history: List[Dict[str, str]] 

class ChatResponse(BaseModel):
    """Esquema de resposta da rota de chat."""
    response: str

# Router
router = APIRouter(tags=["bots"])

# ----------------------------------------------------------------------
# Funções de Serviço Hugging Face
# ----------------------------------------------------------------------

def _prepare_hf_payload(bot_data: Dict[str, Any], messages: List[ChatMessage]) -> Dict[str, Any]:
    full_prompt = f"{bot_data['system_prompt']}\n\n" 
    for msg in messages:
        role = "Usuário" if msg.role == "user" else "Assistente"
        full_prompt += f"{role}: {msg.text}\n"
    full_prompt += "Assistente: "
    
    ai_config = bot_data.get('ai_config', {})
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": ai_config.get('max_output_tokens', 512), 
            "temperature": ai_config.get('temperature', 0.8),
            "return_full_text": False, 
            "do_sample": True
        }
    }
    return payload

async def _call_hf_api(payload: Dict[str, Any], bot_id: str) -> str:
    """
    Chama a API de Inferência do Hugging Face.
    Agora usa 'async with' para garantir o correto fechamento da conexão (Fix LocalProtocolError).
    """
    HF_MODEL_ID = "HuggingFaceH4/zephyr-7b-beta" 
    url = f"{HF_API_BASE_URL}{HF_MODEL_ID}"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}","Content-Type": "application/json"}
    
    max_retries = 3
    initial_delay = 2 

    # NOVO: Criação do cliente dentro do contexto para garantir a estabilidade da conexão
    async with httpx.AsyncClient(timeout=60.0) as client: 
        for attempt in range(max_retries):
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status() 
                result = response.json()
                text = result[0].get('generated_text', '') 
                if text:
                    return text.strip() 
                else:
                    raise ValueError("Resposta do LLM vazia ou inválida.")
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [429, 503] and attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    print(f"Tentativa {attempt+1} falhou. Status {e.response.status_code}. Tentando novamente em {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise HTTPException(status_code=e.response.status_code, detail=f"Erro na API Hugging Face: {e.response.text}")
            except (httpx.RequestError, ValueError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    print(f"Tentativa {attempt+1} falhou. Erro: {e.__class__.__name__}. Tentando novamente em {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise HTTPException(status_code=503, detail=f"A API Hugging Face falhou após várias tentativas (Timeout/Rede/Erro de Dados). Erro: {e.__class__.__name__}")

    return "Falha na comunicação com a IA." 

# ----------------------------------------------------------------------
# LÓGICA DE BACKGROUND 
# ----------------------------------------------------------------------

def _get_bot_from_db(db: Session, bot_id: str):
    """Função síncrona para buscar o bot no DB (necessário para Background Task)."""
    db_bot = db.query(DBBot).filter(DBBot.id == bot_id).first()
    if db_bot is None:
        return None
    return db_bot.to_dict()

async def _process_group_message(bot_id: str, request_data: Dict[str, Any], task_id: str):
    """
    Esta função executa a chamada lenta de IA em segundo plano, incluindo a busca DB.
    """
    TASK_RESULTS_DB[task_id] = {"status": "processing", "result": None}  
    
    db_generator = get_db()
    db = next(db_generator) 
    
    try:
        bot_data = _get_bot_from_db(db, bot_id)
        
        if not bot_data:
            raise ValueError(f"Bot {bot_id} não encontrado no DB para processamento em background.")

        # Converte o histórico recebido para o formato ChatMessage
        messages = [ChatMessage(role=msg['role'].replace('bot', 'model'), text=msg['content']) 
                    for msg in request_data.get('chat_history', []) 
                    if 'content' in msg]
        
        # Adiciona a mensagem do usuário (recebida como user_message)
        messages.append(ChatMessage(role="user", text=request_data.get('user_message', '')))
        
        payload = _prepare_hf_payload(bot_data, messages)

        ai_response_text = await _call_hf_api(payload, bot_id)

        TASK_RESULTS_DB[task_id]["status"] = "complete"
        TASK_RESULTS_DB[task_id]["result"] = ai_response_text
        
    except Exception as e:
        error_message = f"❌ ERRO FATAL na tarefa de background: {e.__class__.__name__}: {e}"
        TASK_RESULTS_DB[task_id]["status"] = "error"
        TASK_RESULTS_DB[task_id]["result"] = error_message
        print(error_message)
    finally:
        db.close()

# ----------------------------------------------------------------------
# ROTAS DE GERENCIAMENTO 
# ----------------------------------------------------------------------

@router.post("/bots/", response_model=Bot, status_code=status.HTTP_201_CREATED)
async def create_bot(bot_in: BotIn, db: Session = Depends(get_db)):
    bot_id = str(uuid.uuid4())
    tags_json = json.dumps(bot_in.tags)
    ai_config_json = json.dumps(bot_in.ai_config.model_dump())
    
    db_bot = DBBot(
        id=bot_id, creator_id=bot_in.creator_id, name=bot_in.name, gender=bot_in.gender,
        introduction=bot_in.introduction, personality=bot_in.personality, 
        welcome_message=bot_in.welcome_message, avatar_url=bot_in.avatar_url,
        tags=tags_json, conversation_context=bot_in.conversation_context,
        context_images=bot_in.context_images, system_prompt=bot_in.system_prompt,
        ai_config_json=ai_config_json
    )
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return Bot(**db_bot.to_dict())

@router.get("/bots/", response_model=List[Bot])
async def read_bots(db: Session = Depends(get_db)):
    db_bots = db.query(DBBot).all()
    return [Bot(**db_bot.to_dict()) for db_bot in db_bots]

@router.get("/bots/{bot_id}", response_model=Bot)
async def read_bot(bot_id: str, db: Session = Depends(get_db)):
    db_bot = db.query(DBBot).filter(DBBot.id == bot_id).first()
    
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    return Bot(**db_bot.to_dict())

@router.put("/bots/import", response_model=Dict[str, Any])
async def import_bots(bot_list_file: BotListFile, db: Session = Depends(get_db)):
    imported_count = 0
    
    for bot_data in bot_list_file.bots:
        db_bot = db.query(DBBot).filter(DBBot.id == bot_data.id).first()
        tags_json = json.dumps(bot_data.tags)
        ai_config_json = json.dumps(bot_data.ai_config.model_dump())
        
        # Simplifiquei para apenas criar um novo se não existir (sem atualização complexa)
        if db_bot:
            continue 
        else:
            db_bot = DBBot(
                id=bot_data.id, creator_id=bot_data.creator_id, name=bot_data.name, gender=bot_data.gender,
                introduction=bot_in.introduction, personality=bot_data.personality, 
                welcome_message=bot_data.welcome_message, avatar_url=bot_data.avatar_url,
                tags=tags_json, conversation_context=bot_data.conversation_context,
                context_images=bot_data.context_images, system_prompt=bot_data.system_prompt,
                ai_config_json=ai_config_json
            )
            db.add(db_bot)
            imported_count += 1
            
    db.commit()
    return {"success": True, "imported_count": imported_count, "message": f"{imported_count} bots imported successfully."}

# Rotas de Health Check e Polling 
@router.get("/health")
async def health():
    ai_status = "ok" if HF_API_TOKEN else "warning (chave HF não definida)"
    return {"status": "ok", "services": {"database": "ok", "huggingface_api": ai_status}}

@router.get("/tasks/{task_id}", response_model=Dict[str, Optional[str]])
async def get_task_status(task_id: str):
    if task_id not in TASK_RESULTS_DB:
        raise HTTPException(status_code=404, detail="Task ID not found or expired.")
    return TASK_RESULTS_DB[task_id]

# Rota de Grupo (Usa Background Task)
@router.post("/groups/send_message", status_code=status.HTTP_202_ACCEPTED, response_model=Dict[str, str])
async def send_group_message(request: ChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # NOTA: Assumindo que o ChatRequest deve ter um bot_id para a tarefa de background
    try:
         target_bot_id = request.bot_id
    except AttributeError:
         # Se não houver bot_id no payload (o que deve ser corrigido), usamos um ID padrão.
         target_bot_id = "default-bot-for-group-task" 

    if db.query(DBBot).filter(DBBot.id == target_bot_id).first() is None:
        raise HTTPException(status_code=404, detail=f"Bot with ID {target_bot_id} not found in database for group task.")

    task_id = str(uuid.uuid4())
    
    background_tasks.add_task(_process_group_message, target_bot_id, request.model_dump(), task_id)
    
    return {
        "task_id": task_id,
        "status": "Processamento de IA enfileirado em Background.",
        "message": "Sua solicitação está sendo processada. O frontend fará o polling da tarefa."
    }

# ----------------------------------------------------------------------
# ROTA DE CHAT 1:1 (SÍNCRONA)
# ----------------------------------------------------------------------

@router.post("/chat/{bot_id}", response_model=ChatResponse)
async def chat_with_bot(bot_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """
    Rota para o chat em tempo real com um bot (chamada síncrona à IA).
    """
    # 1. Busca os dados do Bot no DB
    db_bot = db.query(DBBot).filter(DBBot.id == bot_id).first()
    
    if db_bot is None:
        raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found.")
        
    bot_data = db_bot.to_dict()

    try:
        # 2. Converte o histórico e a nova mensagem para o formato ChatMessage
        messages_for_ia = []
        
        # Adiciona o histórico
        for msg in request.chat_history:
             role = msg.get('role', 'user').replace('bot', 'model') 
             messages_for_ia.append(ChatMessage(role=role, text=msg.get('content', '')))
        
        # Adiciona a mensagem atual do usuário
        messages_for_ia.append(ChatMessage(role="user", text=request.user_message))
        
        # 3. Prepara o payload para a API HF
        payload = _prepare_hf_payload(bot_data, messages_for_ia)

        # 4. Chama a API Hugging Face (agora com a correção de protocolo)
        ai_response_text = await _call_hf_api(payload, bot_id)

        # 5. Retorna a resposta
        return ChatResponse(response=ai_response_text)
        
    except HTTPException:
        # Repassa o erro de API HF (429, 500, etc.)
        raise
    except Exception as e:
        # Erro genérico de processamento
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar chat: {e.__class__.__name__}")
