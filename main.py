from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# Importa as funções CRUD e os objetos de teste do db
from db import get_user, get_bot, get_group, save_message, get_all_bots, update_group_members 
import time
import os
from dotenv import load_dotenv

# --- Integração Gemini ---
from google import genai
from google.genai import types
import asyncio
from typing import Dict, Any, List, Optional
import base64 

# Carrega as variáveis de ambiente
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Definições de Modelos (Baseadas em Pydantic para FastAPI) ---
class User(BaseModel):
    user_id: str
    username: str
    is_admin: bool
class Message(BaseModel):
    sender_id: str
    sender_type: str 
    text: str
    timestamp: float
class ChatGroup(BaseModel):
    group_id: str
    name: str
    scenario: str
    member_ids: list[str]
    messages: list[Message]
class NewMessage(BaseModel):
    group_id: str
    sender_id: str
    text: str
class MemberUpdate(BaseModel):
    member_ids: list[str]
class Bot(BaseModel):
    bot_id: str
    creator_id: str
    name: str
    system_prompt: str
    ai_config: dict
    gender: str
    introduction: str
    personality: str
    welcome_message: str
    conversation_context: str
    context_images: List[str]

# ----------------------------------------------------------------------
# 1. Configuração Inicial e Cliente
# ----------------------------------------------------------------------

client: Optional[genai.Client] = None
if not GEMINI_API_KEY:
    print("ERRO CRÍTICO: GEMINI_API_KEY não encontrada. As IAs não responderão.")
else:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"ERRO: Falha ao inicializar o cliente Gemini: {e}")
        client = None

app = FastAPI(
    title="CRINGE RPG-AI Multi-Bot Backend - V2.3",
    description="API para gerenciar com persistência SQLite e correção Gemini."
)

# ----------------------------------------------------------------------
# 2. Rotas
# ----------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"status": "OK", "version": "2.3 (Finalizada)", "message": "Backend do CRINGE RPG-AI está ativo!"}

@app.get("/users/{user_id}", response_model=User)
def get_user_data(user_id: str):
    user = get_user(user_id)
    if not user:
        if user_id == "user-1":
            from db import TEST_USER, save_user
            save_user(TEST_USER) 
            return TEST_USER
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    # Converte o objeto do db para o modelo Pydantic do FastAPI
    return User(**user.model_dump())


@app.get("/groups/{group_id}", response_model=ChatGroup)
def get_chat_group(group_id: str):
    group = get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    # Converte o objeto do db para o modelo Pydantic do FastAPI
    return ChatGroup(**group.model_dump())

@app.get("/bots/all", response_model=List[Bot])
def get_all_available_bots():
    # Converte a lista de objetos do db para modelos Pydantic
    return [Bot(**b.model_dump()) for b in get_all_bots()]

@app.post("/groups/{group_id}/members")
def update_group_members_route(group_id: str, member_update: MemberUpdate):
    group = get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")

    final_members = list(set(member_update.member_ids))
    if "user-1" not in final_members:
        final_members.append("user-1")
        
    update_group_members(group_id, final_members)
    
    return {"status": "success", "member_ids": final_members}


# ----------------------------------------------------------------------
# 3. Lógica do Gemini (Com correção do método de chamada)
# ----------------------------------------------------------------------

async def get_bot_response(bot: Bot, group: ChatGroup, user_message_text: str) -> Message:
    """Chama a API do Gemini para obter a resposta de um bot específico."""
    
    if not client:
         return Message(
            sender_id=bot.bot_id, sender_type="bot",
            text=f"Erro de IA: Cliente Gemini não inicializado (Chave de API ausente).",
            timestamp=time.time()
        )
        
    # --- CONSTRUÇÃO DO CONTEXTO (HISTÓRICO E INSTRUÇÕES) ---
    contents = []
    
    # Histórico de conversas (Últimas 10 mensagens)
    for msg in group.messages[-10:]:
        role = "user" if msg.sender_type == "user" else "model"
        if msg.sender_type == "bot" and msg.sender_id != bot.bot_id:
             role = "user" 

        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.text)]))

    # SYSTEM INSTRUCTION
    member_names = [get_bot(mid).name if mid.startswith('bot-') else 'Usuário' 
                    for mid in group.member_ids if get_user(mid) or get_bot(mid)]
    
    system_instruction = (
        f"**INSTRUÇÕES DO AGENTE: {bot.name} ({bot.gender})**\n"
        f"1. PERSONALIDADE E REGRAS (NÚCLEO):\n{bot.personality}\n"
        f"2. CONTEXTO DE CONVERSA/ESTILO (TEXTO):\n'{bot.conversation_context}'\n"
        f"3. AMBIENTE ATUAL:\nCenário: '{group.scenario}'\nMEMBROS ATIVOS: {', '.join(member_names)}\n\n"
        f"TAREFA: Sua única resposta deve reagir à última mensagem do usuário ('{user_message_text}'). Mantenha a concisão e o foco no seu papel."
    )
    
    multimodal_parts = [types.Part.from_text(text=system_instruction)]
    
    # Adiciona imagens
    for data_uri in bot.context_images:
        try:
            metadata, encoded_data = data_uri.split(',', 1)
            mime_type = metadata.split(';')[0].split(':')[1]
            image_bytes = base64.b64decode(encoded_data)
            multimodal_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        except Exception as e:
            print(f"Erro ao processar Data URI de imagem: {e}")
            
    contents.insert(0, types.Content(role="user", parts=multimodal_parts))
    
    ai_config_dict: Dict[str, Any] = bot.ai_config
    ai_config = types.GenerateContentConfig(**ai_config_dict)
    
    try:
        # PONTO CRÍTICO: Chamada síncrona do cliente
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=ai_config
        )
        
        return Message(
            sender_id=bot.bot_id, sender_type="bot",
            text=response.text, timestamp=time.time()
        )
        
    except Exception as e:
        print(f"Erro ao chamar Gemini para {bot.name} ({bot.bot_id}): {e}")
        return Message(
            sender_id=bot.bot_id, sender_type="bot",
            text=f"Erro de IA: Não consegui processar a resposta. (Detalhe: {e})",
            timestamp=time.time()
        )

# ----------------------------------------------------------------------
# 4. Rota Principal: Envio de Mensagens
# ----------------------------------------------------------------------

@app.post("/groups/send_message")
async def send_group_message(new_msg: NewMessage):
    """
    Salva a mensagem do usuário e aciona a geração de respostas dos bots em paralelo.
    """
    group = get_group(new_msg.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    
    user_message = Message(
        sender_id=new_msg.sender_id, sender_type="user",
        text=new_msg.text, timestamp=time.time()
    )
    save_message(group.group_id, user_message)

    bot_tasks = []
    
    # Cria as coroutines para cada bot ativo no grupo
    for member_id in group.member_ids:
        bot = get_bot(member_id)
        if bot and member_id != new_msg.sender_id: 
            task = get_bot_response(bot, group, new_msg.text)
            bot_tasks.append(task)
            
    # Executa todas as tarefas de IA em paralelo
    ai_responses = await asyncio.gather(*bot_tasks)
    
    final_responses = []
    for response_message in ai_responses:
        # Só salva no DB se não for uma mensagem de erro
        if response_message.text and not response_message.text.startswith("Erro de IA:"):
            save_message(group.group_id, response_message) 
            final_responses.append(response_message)
        elif response_message.text.startswith("Erro de IA:"):
             final_responses.append(response_message) # Envia o erro de volta para o frontend

    
    return {
        "status": "success",
        "user_message_saved": True,
        "ai_responses": final_responses
    }