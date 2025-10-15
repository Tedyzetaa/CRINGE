from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal
import time
import uuid

# --- 1. MODELOS DE DADOS BASE ---

class User(BaseModel):
    """Representa um usuário ou jogador."""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    is_admin: bool = False  # <--- CAMPO CRÍTICO ADICIONADO PARA O BANCO DE DADOS

class Message(BaseModel):
    """Representa uma única mensagem na conversa."""
    sender_id: str
    sender_type: Literal['user', 'bot']
    text: str
    timestamp: float = Field(default_factory=time.time)

class Bot(BaseModel):
    """Representa um Agente de IA com sua personalidade (system_prompt)."""
    bot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    creator_id: str
    name: str
    system_prompt: str
    ai_config: Dict[str, Any]  # Ex: {"temperature": 0.9, "max_output_tokens": 1024}

class ChatGroup(BaseModel):
    """Representa uma sala de chat com seus membros e histórico."""
    group_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    scenario: str
    member_ids: List[str]  # Lista de user_id's e bot_id's ativos
    messages: List[Message] = []

# --- 2. MODELOS DE DADOS PARA REQUISIÇÕES (INPUT) ---

class NewMessage(BaseModel):
    """Modelo usado para receber novas mensagens via POST."""
    group_id: str
    sender_id: str
    text: str