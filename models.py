# models.py
# Define a estrutura das tabelas Bot, User e Group, e tipos de dados customizados para JSON.

import json
from sqlalchemy import Column, String, Text
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.types import TypeDecorator, VARCHAR

# Importa Base do nosso arquivo database.py
from database import Base 

# --- Tipos Customizados para SQLAlchemy ---

class JSONEncodedDict(TypeDecorator):
    """Implementa o tipo dict armazenado como JSON string."""
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None

# --- Modelos de Dados ---

class User(Base):
    __tablename__ = "users"
    # Adicionando a estrutura básica que seu import_script espera
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Você pode adicionar mais campos de usuário conforme necessário (ex: email, hashed_password)

    def __repr__(self):
        return f"<User(name='{self.name}', id='{self.id}')>"


class Bot(Base):
    __tablename__ = "bots"

    # Campos obrigatórios
    id = Column(String, primary_key=True, index=True)
    creator_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    
    # Campos da personalidade/configuração
    gender = Column(String)
    introduction = Column(Text)
    personality = Column(Text)
    welcome_message = Column(Text)
    avatar_url = Column(String)
    
    # Lista de tags (Armazenada como JSON, mas tratada como List[str] no Python)
    tags = Column(MutableList.as_mutable(JSONEncodedDict), default=[])
    
    # Campos de IA
    conversation_context = Column(Text)
    context_images = Column(Text)
    system_prompt = Column(Text, nullable=False)
    
    # Configurações de IA (Armazenado como JSON, tratado como Dict[str, Any] no Python)
    ai_config = Column(MutableDict.as_mutable(JSONEncodedDict), default={})

    def __repr__(self):
        return f"<Bot(name='{self.name}', id='{self.id}')>"

class Group(Base):
    __tablename__ = "groups"
    # Adicionando uma estrutura básica para Group, caso seu script de importação 
    # ou futuras funcionalidades precisem dela.
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Você pode adicionar mais campos (ex: creator_id, members)

    def __repr__(self):
        return f"<Group(name='{self.name}', id='{self.id}')>"
