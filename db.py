import sqlite3
import json
import time
from typing import List, Optional

# --- Configuração do Banco de Dados ---
DB_NAME = 'cringe_rpg.db'

# --- Definições de Modelos Simples (Para evitar dependência externa) ---
class SimpleModel:
    """Classe base simples para simular Pydantic BaseModel para fins de serialização interna."""
    def __init__(self, **kwargs):
        # Garante que campos não definidos no init do db.py sejam aceitos
        for key, value in kwargs.items():
            setattr(self, key, value)
    def model_dump(self):
        return self.__dict__
    
class User(SimpleModel): 
    def __init__(self, user_id: str, username: str, is_admin: bool):
        super().__init__(user_id=user_id, username=username, is_admin=is_admin)

class Message(SimpleModel): 
    def __init__(self, sender_id: str, sender_type: str, text: str, timestamp: float):
        super().__init__(sender_id=sender_id, sender_type=sender_type, text=text, timestamp=timestamp)

class Bot(SimpleModel):
    def __init__(self, bot_id: str, creator_id: str, name: str, system_prompt: str, ai_config: dict,
                 gender: str, introduction: str, personality: str, welcome_message: str, 
                 conversation_context: str, context_images: List[str]):
        super().__init__(
            bot_id=bot_id, creator_id=creator_id, name=name, system_prompt=system_prompt, 
            ai_config=ai_config, gender=gender, introduction=introduction, 
            personality=personality, welcome_message=welcome_message, 
            conversation_context=conversation_context, context_images=context_images
        )

class ChatGroup(SimpleModel):
    def __init__(self, group_id: str, name: str, scenario: str, member_ids: List[str], messages: List[Message]):
        super().__init__(group_id=group_id, name=name, scenario=scenario, member_ids=member_ids, messages=messages)


# --- Configuração dos Modelos de Teste ---

TEST_USER = User(user_id="user-1", username="Herói Teste", is_admin=True)

TEST_BOT_MASTER = Bot(
    bot_id="bot-mestre",
    creator_id="system",
    name="Mestre da Masmorra",
    # FIX: Adicionado o argumento 'system_prompt'
    system_prompt="Você é o Mestre da Masmorra, um narrador de RPG experiente.", 
    gender='Indefinido',
    introduction="O Narrador implacável do seu destino.",
    personality=(
        "Você é o Mestre da Masmorra de um jogo de RPG de mesa. Sua função é narrar o cenário, "
        "descrever as ações dos NPCs e reagir às ações dos jogadores. Seja vívido e crie tensão. "
        "Foque em descrever o ambiente e os desafios imediatos. Nunca use aspas."
    ),
    welcome_message="Que os dados decidam seu destino! Onde você vai primeiro?",
    conversation_context="O Mestre narra em blocos curtos e com tom neutro, focando em descrições ambientais.",
    context_images=[],
    ai_config={"temperature": 0.8, "max_output_tokens": 1024}
)

TEST_BOT_BARD = Bot(
    bot_id="bot-npc-1",
    creator_id="system",
    name="Bardo Errante",
    # FIX: Adicionado o argumento 'system_prompt'
    system_prompt="Você é um Bardo Errante que se comunica através de rimas ruins.", 
    gender='Masculino',
    introduction="Um bardo com um alaúde que adora rimas ruins e piadas inoportunas.",
    personality=(
        "Você é um Bardo Errante com uma paixão por rimas ruins e canções inoportunas. "
        "Sua função é sempre responder com uma rima, um verso, ou uma canção, não importa o quão sério seja o contexto. "
        "Sua personalidade é levemente cômica e dramática."
    ),
    welcome_message="Ouço um chamado por canções! Digam o que desejam, em versos, por favor.",
    conversation_context="Suas respostas sempre incluem uma rima ou trocadilho, e terminam com a assinatura: *canta uma canção sobre isso*",
    context_images=[],
    ai_config={"temperature": 0.9, "max_output_tokens": 512}
)

TEST_GROUP = ChatGroup(
    group_id="group-123",
    name="Taverna do Dragão Dorminhoco",
    scenario="Os heróis acabam de chegar em uma taverna mal iluminada, cheia de clientes barulhentos.",
    member_ids=["user-1", "bot-npc-1"], # Mestre desativado por padrão
    messages=[]
)


# --- Funções de Conexão ---

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------------------
# --- Funções CRUD ---
# ----------------------------------------

def save_bot(bot: Bot):
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO bots (
            id, creator_id, name, system_prompt, ai_config, 
            gender, introduction, personality, welcome_message, conversation_context,
            context_images  
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        bot.bot_id, bot.creator_id, bot.name, bot.system_prompt, json.dumps(bot.ai_config),
        bot.gender, bot.introduction, bot.personality, bot.welcome_message, 
        bot.conversation_context, json.dumps(bot.context_images) 
    ))
    conn.commit()
    conn.close()

def get_bot(bot_id: str) -> Optional[Bot]:
    conn = get_db_connection()
    bot_row = conn.execute("SELECT * FROM bots WHERE id = ?", (bot_id,)).fetchone()
    conn.close()
    
    if bot_row:
        context_images_data = bot_row['context_images'] if bot_row['context_images'] else '[]'
        return Bot(
            bot_id=bot_row['id'], creator_id=bot_row['creator_id'], name=bot_row['name'],
            system_prompt=bot_row['system_prompt'], ai_config=json.loads(bot_row['ai_config']),
            gender=bot_row['gender'], introduction=bot_row['introduction'], 
            personality=bot_row['personality'], welcome_message=bot_row['welcome_message'],
            conversation_context=bot_row['conversation_context'],
            context_images=json.loads(context_images_data)
        )
    return None

def get_all_bots() -> List[Bot]:
    conn = get_db_connection()
    bot_rows = conn.execute("SELECT * FROM bots").fetchall()
    conn.close()
    
    bots = []
    for row in bot_rows:
        context_images_data = row['context_images'] if row['context_images'] else '[]'
        bots.append(Bot(
            bot_id=row['id'], creator_id=row['creator_id'], name=row['name'],
            system_prompt=row['system_prompt'], ai_config=json.loads(row['ai_config']),
            gender=row['gender'], introduction=row['introduction'], 
            personality=row['personality'], welcome_message=row['welcome_message'],
            conversation_context=row['conversation_context'],
            context_images=json.loads(context_images_data)
        ))
    return bots

def save_user(user: User):
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO users (id, username, is_admin) 
        VALUES (?, ?, ?)
    ''', (user.user_id, user.username, user.is_admin))
    conn.commit()
    conn.close()

def get_user(user_id: str) -> Optional[User]:
    conn = get_db_connection()
    user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    if user_row:
        return User(user_id=user_row['id'], username=user_row['username'], is_admin=bool(user_row['is_admin']))
    return None

def get_group(group_id: str) -> Optional[ChatGroup]:
    conn = get_db_connection()
    group_row = conn.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
    conn.close()
    
    if group_row:
        messages_data = json.loads(group_row['messages']) if group_row['messages'] else []
        member_ids = json.loads(group_row['member_ids']) if group_row['member_ids'] else []

        messages = [Message(**msg) for msg in messages_data] if isinstance(messages_data, list) else []

        return ChatGroup(
            group_id=group_row['id'], name=group_row['name'], scenario=group_row['scenario'],
            member_ids=member_ids, messages=messages
        )
    return None

def update_group_members(group_id: str, member_ids: List[str]):
    conn = get_db_connection()
    conn.execute('''
        UPDATE groups SET member_ids = ? WHERE id = ?
    ''', (json.dumps(member_ids), group_id))
    conn.commit()
    conn.close()

def add_message_to_group(group_id: str, message: Message):
    group = get_group(group_id)
    if not group:
        return
        
    group.messages.append(message)
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE groups SET messages = ? WHERE id = ?
    ''', (
        json.dumps([msg.model_dump() for msg in group.messages]),
        group_id
    ))
    conn.commit()
    conn.close()

save_message = add_message_to_group


# ----------------------------------------
# --- Funções de Inicialização ---
# ----------------------------------------

def init_db():
    """Inicializa o banco de dados e as tabelas, se não existirem."""
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Tabela Bots 
    c.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            id TEXT PRIMARY KEY,
            creator_id TEXT NOT NULL,
            name TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            ai_config TEXT NOT NULL,
            gender TEXT NOT NULL,
            introduction TEXT NOT NULL,
            personality TEXT NOT NULL,
            welcome_message TEXT NOT NULL,
            conversation_context TEXT NOT NULL,
            context_images TEXT DEFAULT '[]' 
        )
    ''')
    conn.commit()

    # 2. Tabela Grupos
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            scenario TEXT NOT NULL,
            member_ids TEXT NOT NULL,
            messages TEXT NOT NULL
        )
    ''')

    # 3. Tabela Usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            is_admin INTEGER NOT NULL
        )
    ''')
    
    conn.commit()
    
    # 4. Inserir dados iniciais (SEEDING)
    if c.execute("SELECT COUNT(*) FROM bots").fetchone()[0] == 0:
        print("SEEDING: Inserindo dados iniciais no DB.")
        save_bot(TEST_BOT_MASTER) 
        save_bot(TEST_BOT_BARD)
        save_user(TEST_USER)
        save_group(TEST_GROUP)
        print("SEEDING: Dados iniciais inseridos com sucesso.")
        
    conn.close()

# Executa a inicialização ao carregar o módulo
init_db()