# models.py

import json
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
# Importa o tipo JSON corrigido
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON 
from sqlalchemy.dialects.postgresql import JSON as PGJSON
from sqlalchemy.types import TypeDecorator, Unicode
from database import Base # Importa Base de database.py
import datetime
from typing import List, Dict, Any

# Mapeia o tipo JSON para compatibilidade entre bancos de dados
class JSONEncodedDict(TypeDecorator):
    """Permite armazenar e recuperar JSON como strings."""
    impl = Unicode
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            # Converte o Python dict/list para string JSON
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            # Converte a string JSON para Python dict/list
            return json.loads(value)
        return value

# Escolhe o tipo JSON específico do dialeto ou o genérico
# Para simplicidade, usaremos o JSONEncodedDict que funciona bem com a maioria dos backends
JSON_TYPE = JSONEncodedDict

class Bot(Base):
    __tablename__ = "bots"

    id = Column(String, primary_key=True, index=True)
    creator_id = Column(String, index=True) 
    
    # Informações básicas
    name = Column(String, index=True)
    gender = Column(String)
    introduction = Column(String)
    personality = Column(Text)
    welcome_message = Column(Text)
    
    # 💡 CORREÇÃO AQUI: tags agora usa o tipo JSON_TYPE para armazenar a lista
    avatar_url = Column(String, nullable=True)
    tags = Column(JSON_TYPE, default=[]) 
    
    # Configurações de IA
    conversation_context = Column(Text, nullable=True)
    context_images = Column(JSON_TYPE, default=[]) # Lista de strings
    system_prompt = Column(Text, nullable=True)
    
    # Configuração de IA (JSON, ex: {"temperature": 0.7})
    ai_config = Column(JSON_TYPE, default={}) 

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relações (opcional, para grupos/chats)
    groups = relationship("Group", back_populates="bot")

    # Garante que o construtor SQLAlchemy consiga inicializar o objeto
    def __init__(self, **kwargs):
        # Garante que os campos JSON tenham valores padrão se não forem fornecidos
        if 'tags' not in kwargs:
            kwargs['tags'] = []
        if 'context_images' not in kwargs:
            kwargs['context_images'] = []
        if 'ai_config' not in kwargs:
            kwargs['ai_config'] = {}
        super().__init__(**kwargs)


class Group(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True, index=True)
    bot_id = Column(String, ForeignKey("bots.id"))
    player_id = Column(String, index=True) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relação com o Bot
    bot = relationship("Bot", back_populates="groups")

    # Mensagens dentro do grupo
    messages = relationship("Message", back_populates="group", order_by="Message.timestamp")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    group_id = Column(String, ForeignKey("groups.id"))
    sender_id = Column(String)  # ID de quem enviou (bot ou player)
    sender_type = Column(String) # 'bot' ou 'player'
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relação com o Grupo
    group = relationship("Group", back_populates="messages")
