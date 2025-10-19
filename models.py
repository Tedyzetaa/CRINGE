# c:\cringe\3.0\models.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base 
from pydantic import BaseModel 
import json # Usado para serializar listas/dicts no ORM

# -----------------------------------------------------
# --- SCHEMAS PYDANTIC (Para comunicação FastAPI) ---
# -----------------------------------------------------

# Esquemas de LEITURA (SAÍDA da API)
class UserRead(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class BotRead(BaseModel):
    id: int
    name: str
    gender: str
    personality: str
    introduction: str
    # Não precisa retornar todos os campos, mas listei os principais para visualização
    class Config:
        from_attributes = True

class GroupRead(BaseModel):
    id: int
    name: str
    scenario: str
    class Config:
        from_attributes = True

class MessageRead(BaseModel):
    id: int
    group_id: int
    sender_id: str
    text: str
    class Config:
        from_attributes = True

# Esquemas de CRIAÇÃO (ENTRADA na API)
class UserCreate(BaseModel):
    name: str

class BotCreate(BaseModel):
    creator_id: str
    name: str
    gender: str = "Indefinido"
    introduction: str = ""
    personality: str = ""
    welcome_message: str = ""
    conversation_context: str = ""
    context_images: list = [] # O front envia lista, o back converte para string
    system_prompt: str = ""
    ai_config: dict = {"temperature": 0.7} # O front envia dict, o back converte para string

class GroupCreate(BaseModel):
    name: str
    scenario: str = ""
    bot_ids: list[int] = []

class MessageSend(BaseModel):
    group_id: int
    sender_id: str
    text: str

# -----------------------------------------------------
# --- MÓDELOS ORM (Tabelas do Banco de Dados) ---
# -----------------------------------------------------

# 1. Tabela de Associação (Group e Bot)
group_bot_association = Table('group_bot_association', Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('bot_id', Integer, ForeignKey('bots.id'), primary_key=True)
)

# 2. Classe User (ORM)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # UNIQUE constraint: Causa do IntegrityError. A lógica Find or Create corrige isso.
    name = Column(String, unique=True, index=True) 

# 3. Classe Bot (ORM)
class Bot(Base):
    __tablename__ = "bots"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    creator_id = Column(String)
    gender = Column(String)
    introduction = Column(Text)
    personality = Column(Text)
    welcome_message = Column(Text)
    conversation_context = Column(Text)
    # Campos que o ORM salva como STRING, mas armazenam JSON
    context_images = Column(Text) 
    system_prompt = Column(Text)
    ai_config = Column(Text)
    
    groups = relationship("Group", secondary=group_bot_association, back_populates="bots")

# 4. Classe Group (ORM)
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    scenario = Column(Text)
    
    bots = relationship("Bot", secondary=group_bot_association, back_populates="groups")
    messages = relationship("Message", back_populates="group")

# 5. Classe Message (ORM)
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    sender_id = Column(String) # ID do usuário ou bot
    text = Column(Text)
    
    group = relationship("Group", back_populates="messages")