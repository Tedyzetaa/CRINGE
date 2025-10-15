from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal
import time
import uuid

# --- 1. MODELOS DE DADOS BASE ---

class User(BaseModel):
    """Representa um usuário ou jogador."""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    is_admin: bool = False

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
    
    # CAMPOS DE PERSONALIZAÇÃO (V2.1)
    gender: Literal['Masculino', 'Feminino', 'Não Binário', 'Indefinido'] = 'Indefinido'
    introduction: str = ""
    personality: str
    welcome_message: str = "Saudações, aventureiro!"
    conversation_context: str = "" 
    
    # NOVO CAMPO PARA IMAGENS DE CONTEXTO (V2.2)
    context_images: List[str] = Field(default_factory=list) # Lista de Data URIs (Base64)

    system_prompt: str = "" 
    
    ai_config: Dict[str, Any]

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

# Modelo auxiliar para a rota de atualização de membros
class MemberUpdate(BaseModel):
    member_ids: list[str]