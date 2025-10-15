import sqlite3
import json
import time
from models import User, Bot, Message, ChatGroup

# --- Configuração do Banco de Dados ---
DB_NAME = 'cringe_rpg.db'

# --- Configuração dos Modelos de Teste (Serão inseridos no DB) ---

TEST_USER = User(
    user_id="user-1",
    username="Herói Teste",
    is_admin=True
)

TEST_BOT_MASTER = Bot(
    bot_id="bot-mestre",
    creator_id="system",
    name="Mestre da Masmorra",
    system_prompt=(
        "Você é o Mestre da Masmorra de um jogo de RPG de mesa. Sua função é narrar o cenário, "
        "descrever as ações dos NPCs e reagir às ações dos jogadores. Seja vívido e crie tensão. "
        "Foque em descrever o ambiente e os desafios imediatos."
    ),
    ai_config={"temperature": 0.8, "max_output_tokens": 1024}
)

TEST_BOT_BARD = Bot(
    bot_id="bot-npc-1",
    creator_id="system",
    name="Bardo Errante",
    system_prompt=(
        "Você é um Bardo Errante com uma paixão por rimas ruins e canções inoportunas. "
        "Sua função é sempre responder com uma rima, um verso, ou uma canção, não importa o quão sério seja o contexto. "
        "Sua personalidade é levemente cômica e dramática."
    ),
    ai_config={"temperature": 0.9, "max_output_tokens": 512}
)

TEST_GROUP = ChatGroup(
    group_id="group-123",
    name="Taverna do Dragão Dorminhoco",
    scenario="Os heróis acabam de chegar em uma taverna mal iluminada, cheia de clientes barulhentos.",
    member_ids=["user-1", "bot-mestre", "bot-npc-1"],
    messages=[] # Histórico de mensagens inicial vazio
)


# --- Funções de Inicialização e Conexão ---

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Isso permite acessar colunas por nome
    return conn

def init_db():
    """Inicializa o banco de dados e as tabelas, se não existirem."""
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Tabela Bots (Persistência dos Agentes de IA)
    c.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            id TEXT PRIMARY KEY,
            creator_id TEXT NOT NULL,
            name TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            ai_config TEXT NOT NULL -- Armazenado como JSON
        )
    ''')

    # 2. Tabela Grupos (Persistência do Chat e Membros)
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            scenario TEXT NOT NULL,
            member_ids TEXT NOT NULL, -- Armazenado como JSON list
            messages TEXT NOT NULL -- Armazenado como JSON list de Messages
        )
    ''')

    # 3. Tabela Usuários (Mínima)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            is_admin INTEGER NOT NULL
        )
    ''')
    
    conn.commit()
    
    # 4. Inserir dados iniciais (se o DB estiver vazio)
    if c.execute("SELECT COUNT(*) FROM bots").fetchone()[0] == 0:
        print("SEEDING: Inserindo dados iniciais no DB.")
        # Bots
        save_bot(TEST_BOT_MASTER)
        save_bot(TEST_BOT_BARD)
        # Usuário
        save_user(TEST_USER)
        # Grupo (Inicializa o histórico de mensagens como JSON vazio)
        save_group(TEST_GROUP)
        print("SEEDING: Dados iniciais inseridos com sucesso.")
        
    conn.close()

# Garante que o DB seja inicializado ao carregar o módulo
init_db()


# --- Funções CRUD ---

# --- BOTS ---

def save_bot(bot: Bot):
    """Insere ou atualiza um bot no banco de dados."""
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO bots (id, creator_id, name, system_prompt, ai_config) 
        VALUES (?, ?, ?, ?, ?)
    ''', (
        bot.bot_id, 
        bot.creator_id, 
        bot.name, 
        bot.system_prompt, 
        json.dumps(bot.ai_config)
    ))
    conn.commit()
    conn.close()

def get_bot(bot_id: str) -> Bot | None:
    """Busca um bot pelo ID."""
    conn = get_db_connection()
    bot_row = conn.execute("SELECT * FROM bots WHERE id = ?", (bot_id,)).fetchone()
    conn.close()
    
    if bot_row:
        # Reconstrói o objeto Bot a partir da linha do DB
        return Bot(
            bot_id=bot_row['id'],
            creator_id=bot_row['creator_id'],
            name=bot_row['name'],
            system_prompt=bot_row['system_prompt'],
            ai_config=json.loads(bot_row['ai_config'])
        )
    return None

def get_all_bots() -> list[Bot]:
    """NOVA FUNÇÃO: Retorna todos os bots salvos, incluindo os criados pelo usuário."""
    conn = get_db_connection()
    bot_rows = conn.execute("SELECT * FROM bots").fetchall()
    conn.close()
    
    bots = []
    for row in bot_rows:
        bots.append(Bot(
            bot_id=row['id'],
            creator_id=row['creator_id'],
            name=row['name'],
            system_prompt=row['system_prompt'],
            ai_config=json.loads(row['ai_config'])
        ))
    return bots

# --- USERS ---

def save_user(user: User):
    """Insere ou atualiza um usuário no banco de dados."""
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO users (id, username, is_admin) 
        VALUES (?, ?, ?)
    ''', (
        user.user_id, 
        user.username, 
        user.is_admin
    ))
    conn.commit()
    conn.close()

def get_user(user_id: str) -> User | None:
    """Busca um usuário pelo ID."""
    conn = get_db_connection()
    user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    if user_row:
        return User(
            user_id=user_row['id'],
            username=user_row['username'],
            is_admin=bool(user_row['is_admin'])
        )
    return None

# --- GROUPS (Grupos de Chat) ---

def save_group(group: ChatGroup):
    """Salva todo o objeto ChatGroup (usado para inicialização)."""
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO groups (id, name, scenario, member_ids, messages) 
        VALUES (?, ?, ?, ?, ?)
    ''', (
        group.group_id, 
        group.name, 
        group.scenario, 
        json.dumps(group.member_ids),
        json.dumps([msg.model_dump() for msg in group.messages]) # Pydantic v2 dump
    ))
    conn.commit()
    conn.close()

def get_group(group_id: str) -> ChatGroup | None:
    """Busca um grupo e reconstrói o objeto ChatGroup a partir do DB."""
    conn = get_db_connection()
    group_row = conn.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
    conn.close()
    
    if group_row:
        # Deserializa a lista de mensagens JSON de volta para lista[Message]
        messages_data = json.loads(group_row['messages'])
        messages = [Message(**msg) for msg in messages_data]
        
        # Deserializa a lista de membros JSON
        member_ids = json.loads(group_row['member_ids'])

        return ChatGroup(
            group_id=group_row['id'],
            name=group_row['name'],
            scenario=group_row['scenario'],
            member_ids=member_ids,
            messages=messages
        )
    return None

def add_message_to_group(group_id: str, message: Message):
    """Adiciona uma nova mensagem ao histórico do grupo."""
    group = get_group(group_id)
    if not group:
        # Se o grupo não for encontrado, não faz nada
        return
        
    group.messages.append(message)
    
    # Serializa e salva o objeto de grupo atualizado
    conn = get_db_connection()
    conn.execute('''
        UPDATE groups SET messages = ? WHERE id = ?
    ''', (
        json.dumps([msg.model_dump() for msg in group.messages]),
        group_id
    ))
    conn.commit()
    conn.close()

def update_group_members(group_id: str, member_ids: list[str]):
    """NOVA FUNÇÃO: Atualiza a lista de membros do grupo."""
    conn = get_db_connection()
    conn.execute('''
        UPDATE groups SET member_ids = ? WHERE id = ?
    ''', (
        json.dumps(member_ids),
        group_id
    ))
    conn.commit()
    conn.close()


# Alias para a função de salvar mensagem, usada pelo main.py
save_message = add_message_to_group