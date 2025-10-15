from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# --- Modelos Base ---

class Message(BaseModel):
    """Representa uma única mensagem no chat."""
    sender_id: str = Field(..., description="ID do remetente (usuário ou bot).")
    sender_type: str = Field(..., description="Tipo do remetente ('user' ou 'bot').")
    text: str = Field(..., description="Conteúdo da mensagem.")
    timestamp: float = Field(..., description="Carimbo de data/hora (Unix) da mensagem.")

class User(BaseModel):
    """Representa um usuário do aplicativo."""
    user_id: str
    username: str

class Bot(BaseModel):
    """Representa um Agente de IA (Bot) criado pelo usuário."""
    bot_id: str
    creator_id: str
    name: str
    system_prompt: str = Field(..., description="Instruções de personalidade e contexto para a IA.")
    
    # CORREÇÃO: Renomeado para evitar conflito com 'model_config' do Pydantic V2
    ai_config: Dict[str, Any] = Field(default_factory=dict, description="Configurações do modelo (temperatura, etc.).")


# --- Modelos de Chat e Grupo ---

class ChatGroup(BaseModel):
    """Representa uma sala de chat de grupo (partida de RPG)."""
    group_id: str
    name: str
    member_ids: List[str] = Field(default_factory=list, description="IDs de usuários e bots (incluindo IA).")
    messages: List[Message] = Field(default_factory=list)
    scenario: Optional[str] = Field(None, description="Descrição do cenário/mundo do RPG.")

# Estrutura de dados para uma nova mensagem recebida (Input)
class NewMessage(BaseModel):
    """Estrutura para enviar uma nova mensagem para um grupo."""
    group_id: str
    sender_id: str
    text: str