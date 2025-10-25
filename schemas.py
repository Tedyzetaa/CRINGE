from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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
        from_attributes = True  # CORRETO para Pydantic 2.x

class BotCreate(BotBase):
    creator_id: str

class Bot(BotBase):
    id: str
    creator_id: str

    class Config:
        from_attributes = True

class BotDisplay(BaseModel):
    id: str
    name: str
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    personality: Optional[str] = None
    welcome_message: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    user_message: str
    chat_history: List[Dict[str, str]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    ai_response: str

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

class BotListFile(BaseModel):
    bots: List[Bot] = Field(default_factory=list)

    class Config:
        from_attributes = True
