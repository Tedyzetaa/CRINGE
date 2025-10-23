# models.py

from sqlalchemy import Column, String, Integer, Float, JSON
from database import Base
import json

# Definição do Modelo de Banco de Dados para o Bot
class Bot(Base):
    __tablename__ = "bots"

    # Campos de identificação e metadados
    id = Column(String, primary_key=True, index=True) # UUID do Bot
    creator_id = Column(String, index=True)
    name = Column(String, index=True)
    gender = Column(String)
    introduction = Column(String)
    personality = Column(String)
    welcome_message = Column(String)
    avatar_url = Column(String)
    
    # Tags e Contexto serão armazenados como strings JSON para simplicidade
    tags = Column(String) # Será um JSON string de List[str]
    conversation_context = Column(String)
    context_images = Column(String)
    
    # Configurações de IA (AIConfig) serão armazenadas como string JSON
    ai_config_json = Column("ai_config", String) 
    system_prompt = Column(String)

    # --- Métodos Auxiliares para Converter JSON ---
    
    # Converte o campo 'tags' de JSON string para List[str] ao ler
    def get_tags(self):
        try:
            return json.loads(self.tags)
        except (json.JSONDecodeError, TypeError):
            return []

    # Converte o campo 'ai_config_json' de JSON string para Dict[str, Any] ao ler
    def get_ai_config(self):
        try:
            # Retorna o dicionário de AIConfig
            return json.loads(self.ai_config_json) 
        except (json.JSONDecodeError, TypeError):
            # Retorno de segurança
            return {"temperature": 0.7, "max_output_tokens": 512} 
            
    # Converte a instância do modelo DB para o formato Pydantic/Dict
    def to_dict(self):
        return {
            "id": self.id,
            "creator_id": self.creator_id,
            "name": self.name,
            "gender": self.gender,
            "introduction": self.introduction,
            "personality": self.personality,
            "welcome_message": self.welcome_message,
            "avatar_url": self.avatar_url,
            "tags": self.get_tags(), # Usando o helper
            "conversation_context": self.conversation_context,
            "context_images": self.context_images,
            "system_prompt": self.system_prompt,
            "ai_config": self.get_ai_config() # Usando o helper
        }