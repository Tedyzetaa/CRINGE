# schemas.py
# Define os modelos de dados (schemas) Pydantic usados pelo FastAPI
# para validação e serialização de dados de entrada/saída.

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Schema Base para Bot ---
class BotBase(BaseModel):
    """Atributos comuns para criar e ler um Bot."""
    name: str = Field(..., max_length=100)
    gender: Optional[str] = None
    introduction: Optional[str] = None
    personality: Optional[str] = None
    welcome_message: Optional[str] = None
    avatar_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    system_prompt: str = Field(..., description="Prompt de instrução principal para a IA do Bot.")
    
    # ai_config e conversation_context (opcionais e tratados como JSON/Text no DB)
    ai_config: Dict[str, Any] = Field(default_factory=dict, description="Configurações avançadas da IA (e.g., temperatura, top_p).")
    conversation_context: Optional[str] = None
    context_images: Optional[str] = None
    
    class Config:
        # Permite que o Pydantic mapeie os campos do SQLAlchemy
        from_attributes = True


# --- Esquema para Criação de Bot ---
class BotCreate(BotBase):
    """Esquema para criação de um novo Bot. Não requer o ID."""
    # O creator_id será injetado do token de autenticação/usuário logado, 
    # mas o campo é mantido aqui para fins de demonstração, caso seja necessário 
    # passá-lo explicitamente.
    creator_id: str


# --- Esquema para Leitura (Resposta da API) ---
class Bot(BotBase):
    """Esquema de resposta completo, incluindo campos gerados pelo BD."""
    id: str
    creator_id: str

    # Permite que o Pydantic mapeie os campos do SQLAlchemy
    class Config:
        from_attributes = True

# --- Schemas para User e Group (Básicos) ---

class User(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

class Group(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

# --- Schemas para Importação/Exportação (JSON File) ---

class BotListFile(BaseModel):
    """
    Schema para importação/exportação de múltiplos bots em um arquivo JSON.
    Usa o schema Bot completo, que inclui 'id' e 'creator_id'.
    """
    bots: List[Bot] = Field(default_factory=list)

    class Config:
        from_attributes = True
