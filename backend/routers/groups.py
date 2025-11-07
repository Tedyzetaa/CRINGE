# c:\cringe\3.0\routers\groups.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
# Certifique-se de que estes modelos (Bot, Message, etc.) estão no seu models.py
from models import Group, GroupRead, GroupCreate, Bot, Message, MessageSend, MessageRead
import json
import os 
from dotenv import load_dotenv # <-- Adicionado para carregar o .env

# --- Configuração LLM (Google Gemini) ---

# Carrega as variáveis de ambiente do arquivo .env
# Isso permite que o genai.Client() encontre a GEMINI_API_KEY
load_dotenv()

client = None
GEMINI_MODEL = "gemini-2.5-flash" 

try:
    from google import genai
    from google.genai.errors import APIError
    
    # O cliente genai.Client() agora buscará a chave GEMINI_API_KEY automaticamente 
    # se ela estiver corretamente configurada no seu .env.
    client = genai.Client() 
except ImportError:
    print("AVISO: O SDK 'google-genai' não está instalado. A resposta do bot será um MOCK.")
except Exception as e:
    # Captura o erro, geralmente a chave API ausente, e mantém o cliente como None
    print(f"AVISO: Não foi possível inicializar o cliente Gemini. Resposta do bot será um MOCK. Erro: {e}")

router = APIRouter(prefix="/groups", tags=["Groups"])

# ----------------------------------------------------------------------
# FUNÇÃO AUXILIAR: Geração da Resposta do Bot (Com Lógica Gemini)
# ----------------------------------------------------------------------
def generate_bot_response(db: Session, group: Group, user_message: str):
    """
    Função que chama o LLM para gerar a resposta do bot.
    Retorna (texto_resposta, id_do_bot)
    """
    
    # Se o cliente Gemini não inicializou, retorna o mock
    if client is None:
        main_bot = group.bots[0] if group.bots else None
        if not main_bot:
            return "Desculpe, este grupo não tem bots associados para responder.", None
        return f"✨ MOCK: {main_bot.name} (Pip) responde. Sua mensagem foi processada: '{user_message}' (IA Offline).", main_bot.id

    # 1. Obter o(s) bot(s) e o System Prompt
    # Assume que o primeiro bot na lista é o bot principal para responder
    main_bot = group.bots[0] if group.bots else None
    
    if not main_bot:
        return "Desculpe, este grupo não tem bots associados para responder.", None

    try:
        # Pega o System Prompt do bot (armazenado como string no ORM)
        system_prompt = main_bot.system_prompt 
        
        # 2. Obter o Histórico (Últimas 20 mensagens)
        # O histórico é crucial para manter a continuidade da conversa.
        messages_db = db.query(Message).filter(Message.group_id == group.id).order_by(Message.id.asc()).limit(20).all()
        
        # Converte o histórico para o formato da API do Gemini (role e parts)
        history = []
        for msg in messages_db:
            # Assumimos que 'user-' é o jogador e 'bot-' é o modelo/assistente
            role = "user" if msg.sender_id.startswith("user") else "model"
            history.append({"role": role, "parts": [{"text": msg.text}]})

        # Adiciona a mensagem atual do usuário ao histórico antes de enviar
        history.append({"role": "user", "parts": [{"text": user_message}]})

        # 3. CHAMA A API DO GEMINI
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=history,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.8, # Ajustado para um bom equilíbrio entre criatividade e coerência
                "max_output_tokens": 800,
            }
        )
        
        # 4. Retorna o texto da resposta
        return response.text, main_bot.id
        
    except APIError as e:
        print(f"Erro na API do Gemini: {e}")
        return f"Desculpe, houve um erro ao chamar a IA: {e}", None
    except Exception as e:
        print(f"Erro inesperado na geração de resposta: {e}")
        return f"Erro interno ao processar a resposta do bot.", None


# ----------------------------------------------------------------------
# ENDPOINTS
# ----------------------------------------------------------------------

@router.get("/", response_model=list[GroupRead])
def list_groups(db: Session = Depends(get_db)):
    """Lista todos os grupos do banco de dados."""
    return db.query(Group).all()

@router.post("/", response_model=GroupRead)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    """Cria um novo grupo no banco de dados e associa os bots."""
    
    bots = db.query(Bot).filter(Bot.id.in_(group.bot_ids)).all()
    
    db_group = Group(
        name=group.name, 
        scenario=group.scenario,
        bots=bots 
    )
    
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    return db_group

@router.get("/{group_id}/messages", response_model=list[MessageRead])
def list_messages(group_id: int, db: Session = Depends(get_db)):
    """Lista o histórico de mensagens para um grupo específico."""
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")

    messages = db.query(Message).filter(Message.group_id == group_id).all()
    
    return messages


@router.post("/send_message")
def send_message(message_data: MessageSend, db: Session = Depends(get_db)):
    """Recebe a mensagem do jogador, salva, chama o LLM e salva a resposta do bot."""
    
    group = db.query(Group).filter(Group.id == message_data.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    
    # 1. Salva a mensagem do JOGADOR
    db_user_message = Message(
        group_id=message_data.group_id,
        sender_id=message_data.sender_id,
        text=message_data.text,
    )
    db.add(db_user_message)
    db.commit()
    db.refresh(db_user_message)
    
    # 2. Gera a resposta do BOT (CHAMADA REAL AO GEMINI ou MOCK)
    bot_response_text, bot_id = generate_bot_response(db, group, message_data.text)

    if bot_id is None:
        # Se falhar ou não houver bot, apenas retorna a confirmação da mensagem do usuário
        return {"status": "User message saved, no bot response generated."}

    # 3. Salva a resposta do BOT
    db_bot_message = Message(
        group_id=message_data.group_id,
        sender_id=f"bot-{bot_id}", # Identificador único do Bot
        text=bot_response_text,
    )
    db.add(db_bot_message)
    db.commit()
    db.refresh(db_bot_message)
    
    # 4. Retorna sucesso
    return {"status": "Message and response received", "user_message_id": db_user_message.id, "bot_message_id": db_bot_message.id}