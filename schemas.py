from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Schema Base para Bot ---
class BotBase(BaseModel):
    name: str = Field(..., max_length=100)
    gender: Optional[str] = None
    introduction: Optional[str] = None
    personality: Optional[str] = None
    welcome_message: Optional[str] = None
    avatar_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    system_prompt: str = Field(..., description="Prompt de instrução principal")
    ai_config: Dict[str, Any] = Field(default_factory=dict)
    conversation_context: Optional[str] = None
    context_images: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- Schema para Criação de Bot ---
class BotCreate(BotBase):
    creator_id: str

# --- Schema para Leitura (Resposta da API) ---
class Bot(BotBase):
    id: str
    creator_id: str

    class Config:
        from_attributes = True

# --- Schema para exibição de bots ---
class BotDisplay(BaseModel):
    """Schema para exibição de bots na listagem (campos reduzidos)"""
    id: str
    name: str
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    personality: Optional[str] = None
    welcome_message: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True

# --- Schemas para Chat ---
class ChatRequest(BaseModel):
    user_message: str
    chat_history: List[Dict[str, str]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    ai_response: str

# --- Schemas para User e Group ---
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

# --- Schema para Importação/Exportação ---
class BotListFile(BaseModel):
    bots: List[Bot] = Field(default_factory=list)

    class Config:
        from_attributes = True
