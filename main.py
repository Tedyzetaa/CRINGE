from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models import User, Bot, ChatGroup, NewMessage, Message, MemberUpdate
from db import get_user, get_bot, get_group, save_message, save_bot, get_all_bots, update_group_members 
import time
import os
from dotenv import load_dotenv

# --- Integração Gemini ---
from google import genai
from google.genai import types
import asyncio
from typing import Dict, Any

# --- Multimodal Imports ---
import base64 
from io import BytesIO

# Carrega as variáveis de ambiente (incluindo GEMINI_API_KEY)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("ERRO CRÍTICO: GEMINI_API_KEY não encontrada.")
    client = None
else:
    client = genai.Client(api_key=GEMINI_API_KEY)


# ----------------------------------------------------------------------
# 1. Configuração Inicial e Aplicação
# ----------------------------------------------------------------------
app = FastAPI(
    title="CRINGE RPG-AI Multi-Bot Backend - V2.2",
    description="API para gerenciar com persistência SQLite e contexto multimodal."
)

# ----------------------------------------------------------------------
# 2. Rotas (Permanecem as mesmas da V2.1)
# ----------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"status": "OK", "version": "2.2 (SQLite/Multimodal)", "message": "Backend do CRINGE RPG-AI está ativo!"}

@app.get("/groups/{group_id}", response_model=ChatGroup)
def get_chat_group(group_id: str):
    group = get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    return group

@app.post("/bots/create", response_model=Bot)
def create_new_bot(new_bot: Bot):
    if get_bot(new_bot.bot_id):
        raise HTTPException(status_code=400, detail=f"Bot ID '{new_bot.bot_id}' já existe.")
        
    save_bot(new_bot)
    return new_bot

@app.get("/bots/all", response_model=list[Bot])
def get_all_available_bots():
    return get_all_bots()

@app.post("/groups/{group_id}/members")
def update_group_members_route(group_id: str, member_update: MemberUpdate):
    group = get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")

    final_members = list(set(member_update.member_ids))
    
    if "user-1" not in final_members:
        final_members.append("user-1")

    if "bot-mestre" not in final_members:
        final_members.append("bot-mestre")
        
    update_group_members(group_id, final_members)
    
    return {"status": "success", "member_ids": final_members}


# ----------------------------------------------------------------------
# 3. Lógica do Gemini - NOVO TRATAMENTO MULTIMODAL
# ----------------------------------------------------------------------

async def get_bot_response(bot: Bot, group: ChatGroup, user_message_text: str) -> Message:
    """Chama a API do Gemini para obter a resposta de um bot específico."""
    
    if not client:
         return Message(
            sender_id=bot.bot_id,
            sender_type="bot",
            text=f"Erro de IA: Cliente Gemini não inicializado (Chave de API ausente).",
            timestamp=time.time()
        )
        
    # --- 3.1. CONSTRUÇÃO DO CONTEXTO DE CONVERSA (HISTÓRICO) ---
    contents = []
    for msg in group.messages[-10:]:
        role = "user" if msg.sender_type == "user" else "model"
        if msg.sender_type == "bot" and msg.sender_id != bot.bot_id:
             role = "user" 

        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.text)]))

    # --- 3.2. CONSTRUÇÃO DO SYSTEM INSTRUCTION (TEXTUAL) ---
    
    system_instruction = (
        f"**INSTRUÇÕES DO AGENTE: {bot.name} ({bot.gender})**\n\n"
        f"**1. PERSONALIDADE E REGRAS (NÚCLEO):**\n"
        f"Siga estas instruções rigorosamente:\n{bot.personality}\n\n"
        
        f"**2. CONTEXTO DE CONVERSA/ESTILO (TEXTO):**\n"
        f"O texto a seguir deve guiar o ESTILO, TOM e LORE da sua resposta. Use-o como exemplo, mas NÃO o repita literalmente na resposta:\n"
        f"'{bot.conversation_context}'\n\n"
        
        f"**3. AMBIENTE ATUAL:**\n"
        f"O cenário do grupo é: '{group.scenario}'\n"
        f"Sua breve descrição/introdução é: '{bot.introduction}'\n"
        f"MEMBROS ATIVOS: {', '.join([get_bot(mid).name if mid.startswith('bot-') else 'Usuário' for mid in group.member_ids])}\n\n"
        
        f"**TAREFA:** Sua única resposta deve reagir à última mensagem do usuário ('{user_message_text}'). Mantenha a concisão e o foco no seu papel."
    )
    
    # --- 3.3. ADICIONAR IMAGENS AO CONTEÚDO MULTIMODAL (CONTENTS) ---
    
    multimodal_parts = []
    
    # 1. Adiciona o texto do System Instruction como o primeiro Part
    multimodal_parts.append(types.Part.from_text(text=system_instruction))
    
    # 2. Adiciona as imagens (decodificadas de Base64)
    for data_uri in bot.context_images:
        try:
            # Extrai o tipo e o dado Base64 (ex: "data:image/png;base64,iVBORw...")
            metadata, encoded_data = data_uri.split(',', 1)
            mime_type = metadata.split(';')[0].split(':')[1]
            
            # Decodifica Base64 para bytes
            image_bytes = base64.b64decode(encoded_data)
            
            # Cria a parte do Gemini a partir dos bytes da imagem
            multimodal_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
            
        except Exception as e:
            print(f"Erro ao processar Data URI de imagem para o bot {bot.name}: {e}")
            
    # Insere as instruções multimodais (texto + imagens) no início do histórico como a primeira mensagem do usuário (System Prompt)
    contents.insert(0, types.Content(role="user", parts=multimodal_parts))

    # --------------------------------------------------------
    
    ai_config_dict: Dict[str, Any] = bot.ai_config
    
    ai_config = types.GenerateContentConfig(
        # system_instruction deve estar vazio pois o conteúdo foi movido para 'contents'
        **ai_config_dict
    )
    
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=ai_config
            )
        )
        
        return Message(
            sender_id=bot.bot_id,
            sender_type="bot",
            text=response.text,
            timestamp=time.time()
        )
        
    except Exception as e:
        print(f"Erro ao chamar Gemini para {bot.name} ({bot.bot_id}): {e}")
        return Message(
            sender_id=bot.bot_id,
            sender_type="bot",
            text=f"Erro de IA: Não consegui processar a resposta. (Detalhe: {e})",
            timestamp=time.time()
        )

# ----------------------------------------------------------------------
# 4. Rota Principal: Envio de Mensagens (Permanecem a mesma)
# ----------------------------------------------------------------------

@app.post("/groups/send_message")
async def send_group_message(new_msg: NewMessage):
    """
    Recebe uma mensagem de um usuário, salva (no SQLite) e aciona a lógica da IA 
    para gerar respostas de múltiplos bots em paralelo.
    """
    group = get_group(new_msg.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    
    user_message = Message(
        sender_id=new_msg.sender_id,
        sender_type="user",
        text=new_msg.text,
        timestamp=time.time()
    )
    save_message(group.group_id, user_message)

    bot_tasks = []
    
    for member_id in group.member_ids:
        bot = get_bot(member_id)
        if bot and member_id != new_msg.sender_id: 
            task = get_bot_response(bot, group, new_msg.text)
            bot_tasks.append(task)
            
    ai_responses = await asyncio.gather(*bot_tasks)
    
    final_responses = []
    for response_message in ai_responses:
        if response_message.text and not response_message.text.startswith("Erro de IA:"):
            save_message(group.group_id, response_message) 
            final_responses.append(response_message)
        elif response_message.text.startswith("Erro de IA:"):
             final_responses.append(response_message)

    
    return {
        "status": "success",
        "user_message_saved": True,
        "ai_responses": final_responses
    }