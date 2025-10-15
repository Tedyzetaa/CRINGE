from fastapi import FastAPI, HTTPException
from models import User, Bot, ChatGroup, NewMessage, Message
# Importa o dicionário de bots para que a nova rota possa salvar
from db import get_user, get_bot, get_group, save_message, DB_BOTS 
import time
import os
from dotenv import load_dotenv

# --- Integração Gemini ---
from google import genai
from google.genai import types
import asyncio
from typing import Dict, Any

# Carrega as variáveis de ambiente (incluindo GEMINI_API_KEY)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrada no arquivo .env. Certifique-se de que ele está na pasta raiz e contém a chave.")

# Inicializa o cliente Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# ----------------------------------------------------------------------
# 1. Configuração Inicial e Aplicação
# ----------------------------------------------------------------------
app = FastAPI(
    title="CRINGE RPG-AI Multi-Bot Backend",
    description="API para gerenciar usuários, bots e grupos de chat com múltiplos agentes de IA."
)

# ----------------------------------------------------------------------
# 2. Rotas de Teste e Informação
# ----------------------------------------------------------------------

@app.get("/")
def read_root():
    # Versão atualizada para 1.2
    return {"status": "OK", "version": "1.2", "message": "Backend do CRINGE RPG-AI está ativo!"}

@app.get("/groups/{group_id}")
def get_chat_group(group_id: str) -> ChatGroup:
    """Retorna detalhes completos de um grupo de chat, incluindo histórico."""
    group = get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    return group

@app.get("/users/{user_id}", response_model=User)
def get_user_details(user_id: str):
    """Retorna detalhes de um usuário."""
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user

# NOVA ROTA: Permite criar bots pelo Frontend
@app.post("/bots/create", response_model=Bot)
def create_new_bot(new_bot: Bot):
    """Cria um novo Bot de IA no banco de dados em memória."""
    if new_bot.bot_id in DB_BOTS:
        raise HTTPException(status_code=400, detail="Bot ID já existe.")
        
    DB_BOTS[new_bot.bot_id] = new_bot
    return new_bot


# ----------------------------------------------------------------------
# 3. Lógica do Gemini para um Único Bot - CORREÇÃO DE VERSÃO/ASSÍNCRONA
# ----------------------------------------------------------------------

async def get_bot_response(bot: Bot, group: ChatGroup, user_message_text: str) -> Message:
    """Chama a API do Gemini para obter a resposta de um bot específico."""
    
    # 1. Montar o histórico de mensagens para o Gemini
    contents = []
    
    for msg in group.messages[-10:]:
        role = "user" if msg.sender_type == "user" else "model"
        if msg.sender_type == "bot" and msg.sender_id != bot.bot_id:
             role = "user" 

        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.text)]))

    # Adicionar a instrução do sistema (personalidade do bot e contexto)
    system_instruction = bot.system_prompt + (
        f"\n---\n"
        f"CONTEXTO DO CENÁRIO: {group.scenario}\n"
        f"Sua próxima resposta deve reagir à última mensagem do usuário ('{user_message_text}') e manter sua personalidade. "
        f"Se for o Mestre, descreva a cena. Se for um NPC, reaja como personagem."
    )
    
    # 2. Configurar a chamada
    # Usa Dict[str, Any] como tipo para garantir flexibilidade nas configurações
    ai_config_dict: Dict[str, Any] = bot.ai_config
    
    # Converte para o objeto GenerateContentConfig
    ai_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        **ai_config_dict
    )
    
    try:
        # CORREÇÃO: Usar a chamada síncrona DENTRO de um executor para evitar erros de versão do SDK
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=ai_config
            )
        )
        
        # 3. Formatar a resposta do Gemini
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
# 4. Rota Principal: Envio de Mensagens e Resposta da IA (USANDO PARALELISMO)
# ----------------------------------------------------------------------

@app.post("/groups/send_message")
async def send_group_message(new_msg: NewMessage):
    """
    Recebe uma mensagem de um usuário, salva e aciona a lógica da IA 
    para gerar respostas de múltiplos bots em paralelo.
    """
    group = get_group(new_msg.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    
    # 1. Salvar a mensagem do usuário
    user_message = Message(
        sender_id=new_msg.sender_id,
        sender_type="user",
        text=new_msg.text,
        timestamp=time.time()
    )
    save_message(group.group_id, user_message)

    # 2. Identificar os bots na sala e criar tarefas assíncronas
    bot_tasks = []
    
    for member_id in group.member_ids:
        bot = get_bot(member_id)
        if bot:
            task = get_bot_response(bot, group, new_msg.text)
            bot_tasks.append(task)
            
    # 3. Executa todas as chamadas à API do Gemini em paralelo
    ai_responses = await asyncio.gather(*bot_tasks)
    
    # 4. Salvar as respostas geradas pelos bots e preparar o retorno
    final_responses = []
    for response_message in ai_responses:
        # Salva apenas respostas válidas (sem a mensagem de erro debug)
        if response_message.text and not response_message.text.startswith("Erro de IA:"):
            save_message(group.group_id, response_message)
            final_responses.append(response_message)
        elif response_message.text.startswith("Erro de IA:"):
             # Retorna a mensagem de erro para debug no frontend
             final_responses.append(response_message)

    
    return {
        "status": "success",
        "user_message_saved": True,
        "ai_responses": final_responses
    }