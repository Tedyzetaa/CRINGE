from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import uuid

# Importações absolutas
from database import get_db
from models import Bot
from schemas import ChatRequest, ChatResponse, BotDisplay

# Importação do serviço AI
try:
    from services.ai_service import AIService
    ai_service = AIService()
    print("✅ AIService carregado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar AIService: {e}")
    ai_service = None
except Exception as e:
    print(f"❌ Erro na inicialização do AIService: {e}")
    ai_service = None

router = APIRouter(prefix="/bots", tags=["Bots"])

@router.get("/", response_model=List[BotDisplay])
def list_bots(db: Session = Depends(get_db)):
    """Lista todos os bots disponíveis"""
    try:
        bots = db.query(Bot).all()
        result = []
        
        for bot in bots:
            try:
                tags = json.loads(bot.tags) if bot.tags else []
            except:
                tags = []
            
            bot_data = {
                "id": bot.id,
                "name": bot.name,
                "gender": bot.gender,
                "avatar_url": bot.avatar_url,
                "personality": bot.personality,
                "welcome_message": bot.welcome_message,
                "tags": tags,
            }
            result.append(BotDisplay(**bot_data))
            
        return result
    except Exception as e:
        print(f"❌ Erro em list_bots: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/chat/{bot_id}", response_model=ChatResponse)
def chat_with_bot(bot_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """Chat com bot usando OpenRouter"""
    if not ai_service:
        raise HTTPException(status_code=500, detail="Serviço de IA não disponível")
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot '{bot_id}' não encontrado")
    
    try:
        ai_config = json.loads(bot.ai_config_json) if bot.ai_config_json else {}
    except:
        ai_config = {}

    try:
        ai_response = ai_service.generate_response(
            bot_data=bot,
            ai_config=ai_config,
            user_message=request.user_message,
            chat_history=request.chat_history
        )
        return ChatResponse(ai_response=ai_response)
    except Exception as e:
        error_msg = f"Erro na IA: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/import")
def import_bots(import_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Importa bots de JSON"""
    if 'bots' not in import_data:
        raise HTTPException(status_code=400, detail="JSON deve conter chave 'bots'")
    
    bots_data = import_data['bots']
    results = {'imported': 0, 'failed': 0, 'errors': []}
    
    for bot_data in bots_data:
        try:
            bot_id = bot_data.get('id', str(uuid.uuid4()))
            
            existing_bot = db.query(Bot).filter(Bot.id == bot_id).first()
            
            if existing_bot:
                # Atualiza bot existente
                for key, value in bot_data.items():
                    if hasattr(existing_bot, key) and key != 'id':
                        if key in ['tags', 'ai_config']:
                            setattr(existing_bot, key, json.dumps(value))
                        else:
                            setattr(existing_bot, key, value)
            else:
                # Cria novo bot
                new_bot = Bot(
                    id=bot_id,
                    creator_id=bot_data.get('creator_id', 'imported-user'),
                    name=bot_data['name'],
                    gender=bot_data.get('gender', ''),
                    introduction=bot_data.get('introduction', ''),
                    personality=bot_data.get('personality', ''),
                    welcome_message=bot_data.get('welcome_message', ''),
                    avatar_url=bot_data.get('avatar_url', ''),
                    tags=json.dumps(bot_data.get('tags', [])),
                    conversation_context=bot_data.get('conversation_context', ''),
                    context_images=bot_data.get('context_images', '[]'),
                    ai_config_json=json.dumps(bot_data.get('ai_config', {})),
                    system_prompt=bot_data.get('system_prompt', '')
                )
                db.add(new_bot)
            
            results['imported'] += 1
                
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"{bot_data.get('name', 'Unknown')}: {str(e)}")
    
    try:
        db.commit()
        results['message'] = f"Importados: {results['imported']}, Falhas: {results['failed']}"
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no banco: {str(e)}")
    
    return results
