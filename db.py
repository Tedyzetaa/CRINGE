from typing import Dict, List
from models import User, Bot, ChatGroup, Message # CORRIGIDO
import time

# SIMULAÇÃO DE BANCO DE DADOS EM MEMÓRIA
DB_USERS: Dict[str, User] = {}
DB_BOTS: Dict[str, Bot] = {}
DB_GROUPS: Dict[str, ChatGroup] = {}

def initialize_db():
    """Popula o "banco de dados" com dados iniciais para teste."""
    
    # 1. Usuário
    user = User(user_id="user-1", username="Aventureiro_01")
    DB_USERS[user.user_id] = user

    # 2. Bots (Agentes de IA)
    bot_mestre = Bot(
        bot_id="bot-mestre",
        creator_id="system",
        name="Mestre da Masmorra",
        system_prompt="Você é o Mestre do Jogo em um cenário de fantasia medieval. Descreva cenários e NPCs de forma imersiva e aja como árbitro. Seu tom é épico e levemente misterioso.",
        ai_config={"temperature": 0.8, "max_output_tokens": 1024}
    )
    bot_npc = Bot(
        bot_id="bot-npc-1",
        creator_id="system",
        name="Bardo Errante",
        system_prompt="Você é um Bardo Errante chamado Elara. Sua personalidade é alegre, otimista, e você responde frequentemente com rimas ou canções. Você está sempre disposto a ajudar.",
        ai_config={"temperature": 0.7, "max_output_tokens": 512}
    )
    DB_BOTS[bot_mestre.bot_id] = bot_mestre
    DB_BOTS[bot_npc.bot_id] = bot_npc

    # 3. Grupo de Chat (Partida)
    initial_message = Message(
        sender_id="bot-mestre",
        sender_type="bot",
        text="A névoa matinal se levanta sobre as Ruínas de Eldoria. O que vocês fazem agora?",
        timestamp=time.time()
    )
    
    group = ChatGroup(
        group_id="group-123",
        name="A Busca por Eldoria",
        member_ids=[user.user_id, bot_mestre.bot_id, bot_npc.bot_id],
        messages=[initial_message],
        scenario="Um grupo de aventureiros busca um artefato mágico em ruínas antigas."
    )
    DB_GROUPS[group.group_id] = group

# Inicializa o banco de dados na primeira execução
initialize_db()

# Funções de acesso
def get_user(user_id: str) -> User | None:
    return DB_USERS.get(user_id)

def get_bot(bot_id: str) -> Bot | None:
    return DB_BOTS.get(bot_id)

def get_group(group_id: str) -> ChatGroup | None:
    return DB_GROUPS.get(group_id)

def save_message(group_id: str, message: Message):
    if group_id in DB_GROUPS:
        DB_GROUPS[group_id].messages.append(message)