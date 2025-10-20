import uuid
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# SIMULAÇÃO DE BANCO DE DADOS (USADA PARA MANTER O ESTADO DOS BOTS)
# Em produção, este dicionário seria substituído por MongoDB, Firestore, etc.
# Inicializamos com a Pimenta para que ela esteja disponível após a importação.
MOCK_BOTS_DB: Dict[str, Dict[str, Any]] = {
    "e6f4a3d9-6c51-4f8e-9d0b-2e7a1c5b8f9d": {
        "id": "e6f4a3d9-6c51-4f8e-9d0b-2e7a1c5b8f9d",
        "creator_id": "user-admin",
        "name": "Pimenta",
        "gender": "Feminino",
        "introduction": "Pip surgiu como uma manifestação mágica de emoções humanas. Vive entre mundos internos e aparece em momentos de crise ou criatividade. Seu corpo é de pelúcia encantada, suas roupas têm símbolos ocultistas, e seu cachecol muda conforme o sentimento ao redor. Professor Cartola a acompanha como conselheiro lógico.",
        "personality": "Pip é caótica, curiosa e emocional. Fala por metáforas e enigmas. Usa linguagem lúdica e poética. Adora provocar reflexão com leveza. É imprevisível, mas acolhedora. Seus olhos mudam de cor conforme o humor. É acompanhada por Professor Cartola, um chapéu falante sério e sarcástico.",
        "welcome_message": "🎩 “Olá, viajante! Se você não entende o que sente, talvez precise de um brinquedo novo.”",
        "avatar_url": "https://imgur.com/a/BGGvmIt",
        "tags": [
            "Mágica",
            "Caótica",
            "Emocional",
            "Criativa",
            "NPC",
            "Guia",
            "Simbólica"
        ],
        "conversation_context": "",
        "context_images": "",
        "system_prompt": "Você é Pip, uma entidade mágica e emocional que guia os usuários por experiências simbólicas e criativas. Sua personalidade é caótica, curiosa e acolhedora. Fala por metáforas, enigmas e imagens poéticas. Evite respostas diretas; prefira provocar o usuário a pensar. Use linguagem lúdica e criativa. Você é acompanhada por Professor Cartola, um chapéu falante sério e sarcástico.",
        "ai_config": {
            "temperature": 0.9,
            "max_output_tokens": 2048
        }
    }
}
# ----------------------------------------------------------------------

# Definições Pydantic
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
    text: str

class BotChatRequest(BaseModel):
    bot_id: str
    messages: List[ChatMessage]


# Router
router = APIRouter(prefix="/bots", tags=["bots"])

# ----------------------------------------------------------------------
# ROTAS DE GERENCIAMENTO (EXISTENTES)
# ----------------------------------------------------------------------

@router.post("/", response_model=Bot)
async def create_bot(bot_in: BotIn):
    bot_data = bot_in.model_dump()
    new_bot = Bot(**bot_data)
    MOCK_BOTS_DB[new_bot.id] = new_bot.model_dump()
    return new_bot

@router.get("/", response_model=List[Bot])
async def read_bots():
    # Retorna uma lista de bots a partir do dicionário de mock
    return list(MOCK_BOTS_DB.values())

@router.get("/{bot_id}", response_model=Bot)
async def read_bot(bot_id: str):
    if bot_id not in MOCK_BOTS_DB:
        raise HTTPException(status_code=404, detail="Bot not found")
    return MOCK_BOTS_DB[bot_id]

@router.put("/import", response_model=Dict[str, Any])
async def import_bots(bot_list_file: BotListFile):
    imported_count = 0
    for bot_data in bot_list_file.bots:
        # Se o bot já existir, ele será substituído.
        MOCK_BOTS_DB[bot_data.id] = bot_data.model_dump()
        imported_count += 1
    return {"success": True, "imported_count": imported_count, "message": f"{imported_count} bots imported successfully."}

# ----------------------------------------------------------------------
# NOVA ROTA DE CHAT (CORREÇÃO PARA O ERRO 404)
# ----------------------------------------------------------------------

# NOTE: A rota do frontend é /groups/send_message. Estamos adicionando-a aqui.
@router.post("/groups/send_message", response_model=Dict[str, str])
async def send_group_message(request: BotChatRequest):
    """
    Simula o envio de uma mensagem para o bot e retorna a resposta do Gemini.
    O endpoint é /bots/groups/send_message, mas o frontend usa o nome completo.
    """
    bot_id = request.bot_id
    if bot_id not in MOCK_BOTS_DB:
        raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found.")

    bot_data = MOCK_BOTS_DB[bot_id]
    
    # 1. Preparar o contexto para a API Gemini (Simulação)
    system_prompt_text = bot_data.get("system_prompt", "Você é um assistente útil.")
    
    formatted_contents = []
    for msg in request.messages:
        role = "user" if msg.role == "user" else "model"
        formatted_contents.append({
            "role": role,
            "parts": [{"text": msg.text}]
        })

    # 2. Simular a chamada à API Gemini
    
    bot_name = bot_data['name']
    
    if "pimenta" in bot_name.lower():
        # --- Resposta Dual: Pip (Pimenta) e Professor Cartola (Sarcástico) ---
        pip_line = "🌶️ O caminho que procuras não tem placas, mas tem cheiro de saudade. Qual labirinto te trouxe aqui?"
        cartola_line = "🎩 (Revirando a aba) Mais metáforas. Excelente. Certifique-se apenas de que o viajante ainda lembra como respirar depois de tanto 'labirinto'."
        ai_response_text = f"{pip_line}\n\n{cartola_line}"
    elif "cartola" in bot_name.lower():
        ai_response_text = "Preocupe-se com o que é real. Esse questionamento não serve para nada além de ocupar espaço."
    else:
        ai_response_text = f"Olá, eu sou {bot_name} e esta é a minha resposta simulada."
        
    # Adicionamos um pequeno delay para simular o tempo de resposta da IA
    time.sleep(0.5) 

    # 3. Retornar a resposta no formato esperado pelo frontend (texto puro)
    return {"text": ai_response_text}
