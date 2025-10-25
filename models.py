from sqlalchemy import Column, String, Text
from database import Base
import json

class Bot(Base):
    __tablename__ = "bots"

    id = Column(String, primary_key=True, index=True)
    creator_id = Column(String, index=True)
    name = Column(String, index=True)
    gender = Column(String)
    introduction = Column(Text)
    personality = Column(Text)
    welcome_message = Column(Text)
    avatar_url = Column(String)
    tags = Column(Text)
    conversation_context = Column(Text)
    context_images = Column(Text)
    ai_config_json = Column("ai_config", Text)
    system_prompt = Column(Text)

    def to_dict(self):
        try:
            tags = json.loads(self.tags) if self.tags else []
        except:
            tags = []
            
        try:
            ai_config = json.loads(self.ai_config_json) if self.ai_config_json else {}
        except:
            ai_config = {}
            
        return {
            "id": self.id,
            "creator_id": self.creator_id,
            "name": self.name,
            "gender": self.gender,
            "introduction": self.introduction,
            "personality": self.personality,
            "welcome_message": self.welcome_message,
            "avatar_url": self.avatar_url,
            "tags": tags,
            "conversation_context": self.conversation_context,
            "context_images": self.context_images,
            "system_prompt": self.system_prompt,
            "ai_config": ai_config
        }
