# models.py

from sqlalchemy import Column, String, Integer, Float, JSON
from sqlalchemy.orm import relationship
from database import Base
import json
from typing import Dict, Any, List

# Não precisamos mais da classe AIConfig separada, pois as configurações
# estão sendo serializadas como JSON no campo ai_config_json da classe Bot.

# Definição do Modelo de Banco de Dados para o Bot
class Bot(Base):
    """
    Tabela principal para armazenar bots/personagens.
    As configurações de IA (AIConfig) e as listas de tags são serializadas como JSON.
    """
    __tablename__ = "bots"

    # Campos de identificação e metadados
    # Assumindo que o ID é um UUID (String) conforme o modelo atual
    id = Column(String, primary_key=True, index=True) 
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
    
    def get_tags(self) -> List[str]:
        """Converte o campo 'tags' de JSON string para List[str] ao ler."""
        try:
            # Retorna [] se self.tags for None
            return json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            # Adicionando log de erro se a conversão falhar
            print(f"Alerta de JSON: Falha ao decodificar tags para Bot ID: {self.id}")
            return []

    def get_ai_config(self) -> Dict[str, Any]:
        """Converte o campo 'ai_config_json' de JSON string para Dict[str, Any] ao ler."""
        # Configuração de segurança padrão
        default_config = {"temperature": 0.7, "max_output_tokens": 512, "model_id": "gemini-2.5-flash"}
        try:
            # Retorna a configuração padrão se self.ai_config_json for None
            return json.loads(self.ai_config_json) if self.ai_config_json else default_config
        except (json.JSONDecodeError, TypeError):
            # Adicionando log de erro se a conversão falhar
            print(f"Alerta de JSON: Falha ao decodificar ai_config para Bot ID: {self.id}")
            return default_config
            
    def to_dict(self) -> Dict[str, Any]:
        """Converte a instância do modelo DB para o formato Dict (útil para Pydantic)."""
        return {
            "id": self.id,
            "creator_id": self.creator_id,
            "name": self.name,
            "gender": self.gender,
            "introduction": self.introduction,
            "personality": self.personality,
            "welcome_message": self.welcome_message,
            "avatar_url": self.avatar_url,
            "tags": self.get_tags(), 
            "conversation_context": self.conversation_context,
            "context_images": self.context_images,
            "system_prompt": self.system_prompt,
            "ai_config": self.get_ai_config() 
        }
    
    def __repr__(self):
        return f"<Bot(id={self.id}, name='{self.name}', creator_id='{self.creator_id}')>"
