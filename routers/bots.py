from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import uuid
import logging

# Importações absolutas
from database import get_db
from models import Bot
from schemas import ChatRequest, ChatResponse, BotDisplay

# Configuração de logging
logger = logging.getLogger(__name__)

# Importação do serviço AI
try:
    from services.ai_service import AIService
    ai_service = AIService()
    logger.info("✅ AIService carregado com sucesso")
except ImportError as e:
    logger.error(f"❌ Erro ao importar AIService: {e}")
    ai_service = None
except Exception as e:
    logger.error(f"❌ Erro na inicialização do AIService: {e}")
    ai_service = None

router = APIRouter(prefix="/bots", tags=["Bots"])

@router.get("/", response_model=List[BotDisplay])
def list_bots(db: Session = Depends(get_db)):
    """Lista todos os bots disponíveis"""
    try:
        logger.info("📋 Buscando lista de bots")
        bots = db.query(Bot).all()
        result = []
        
        for bot in bots:
            try:
                # Converter tags de JSON para lista
                tags = json.loads(bot.tags) if bot.tags else []
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Tags inválidas para bot {bot.id}, usando lista vazia")
                tags = []
            
            # Criar dicionário do bot
            bot_data = {
                "id": bot.id,
                "name": bot.name,
                "gender": bot.gender,
                "avatar_url": bot.avatar_url,
                "personality": bot.personality,
                "welcome_message": bot.welcome_message,
                "introduction": bot.introduction,  # Adicionado para o frontend
                "tags": tags,
            }
            result.append(BotDisplay(**bot_data))
        
        logger.info(f"✅ Retornando {len(result)} bots")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro em list_bots: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/chat/{bot_id}", response_model=ChatResponse)
def chat_with_bot(bot_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """Chat com bot usando OpenRouter"""
    if not ai_service:
        logger.error("❌ Serviço de IA não disponível")
        raise HTTPException(status_code=500, detail="Serviço de IA não disponível")
    
    # Validar entrada
    if not request.user_message or not request.user_message.strip():
        raise HTTPException(status_code=400, detail="Mensagem não pode estar vazia")
    
    if len(request.user_message) > 1000:
        raise HTTPException(status_code=400, detail="Mensagem muito longa (máximo 1000 caracteres)")
    
    logger.info(f"💬 Iniciando chat com bot {bot_id}")
    
    # Buscar bot
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        logger.warning(f"❌ Bot {bot_id} não encontrado")
        raise HTTPException(status_code=404, detail=f"Bot '{bot_id}' não encontrado")
    
    try:
        # Converter configurações AI
        ai_config = {}
        if bot.ai_config_json:
            try:
                ai_config = json.loads(bot.ai_config_json)
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Config AI inválida para bot {bot_id}, usando padrão")
                ai_config = {"temperature": 0.7, "max_output_tokens": 400}
    except Exception as e:
        logger.warning(f"⚠️ Erro ao carregar config AI: {e}")
        ai_config = {"temperature": 0.7, "max_output_tokens": 400}

    try:
        logger.info(f"🤖 Gerando resposta para mensagem: {request.user_message[:50]}...")
        
        # Usar o método to_dict do model para garantir compatibilidade
        bot_dict = bot.to_dict()
        
        ai_response = ai_service.generate_response(
            bot_data=bot_dict,
            ai_config=ai_config,
            user_message=request.user_message,
            chat_history=request.chat_history
        )
        
        logger.info(f"✅ Resposta gerada: {ai_response[:100]}...")
        return ChatResponse(ai_response=ai_response)
        
    except Exception as e:
        error_msg = f"Erro na IA: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/import")
def import_bots(import_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Importa bots de JSON"""
    logger.info("📥 Iniciando importação de bots")
    
    if 'bots' not in import_data:
        raise HTTPException(status_code=400, detail="JSON deve conter chave 'bots'")
    
    bots_data = import_data['bots']
    results = {
        'imported': 0, 
        'failed': 0, 
        'errors': [],
        'total_processed': len(bots_data)
    }
    
    for i, bot_data in enumerate(bots_data):
        try:
            bot_id = bot_data.get('id', str(uuid.uuid4()))
            
            # Verificar se bot já existe
            existing_bot = db.query(Bot).filter(Bot.id == bot_id).first()
            
            if existing_bot:
                # Atualizar bot existente
                logger.info(f"🔄 Atualizando bot existente: {bot_data.get('name', 'Unknown')}")
                update_count = 0
                
                for key, value in bot_data.items():
                    if hasattr(existing_bot, key) and key != 'id':
                        if key in ['tags', 'ai_config']:
                            # Converter para JSON
                            setattr(existing_bot, key, json.dumps(value))
                        else:
                            setattr(existing_bot, key, value)
                        update_count += 1
                
                logger.info(f"✅ Bot atualizado com {update_count} campos")
                
            else:
                # Criar novo bot
                logger.info(f"🆕 Criando novo bot: {bot_data.get('name', 'Unknown')}")
                
                # Validar campos obrigatórios
                required_fields = ['name', 'system_prompt']
                missing_fields = [field for field in required_fields if not bot_data.get(field)]
                
                if missing_fields:
                    results['errors'].append(f"Bot {i}: Campos obrigatórios faltando: {', '.join(missing_fields)}")
                    results['failed'] += 1
                    continue
                
                new_bot = Bot(
                    id=bot_id,
                    creator_id=bot_data.get('creator_id', 'imported-user'),
                    name=bot_data['name'],
                    gender=bot_data.get('gender', 'Não especificado'),
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
            error_msg = f"Bot {i} ({bot_data.get('name', 'Unknown')}): {str(e)}"
            results['errors'].append(error_msg)
            results['failed'] += 1
            logger.error(f"❌ {error_msg}")
    
    try:
        db.commit()
        results['message'] = f"Importação concluída: {results['imported']} sucessos, {results['failed']} falhas"
        logger.info(f"✅ {results['message']}")
    except Exception as e:
        db.rollback()
        error_msg = f"Erro no commit do banco: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    
    return results

@router.get("/{bot_id}", response_model=BotDisplay)
def get_bot(bot_id: str, db: Session = Depends(get_db)):
    """Obter detalhes de um bot específico"""
    try:
        logger.info(f"📋 Buscando bot {bot_id}")
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot não encontrado")
        
        # Converter tags
        try:
            tags = json.loads(bot.tags) if bot.tags else []
        except json.JSONDecodeError:
            tags = []
        
        bot_data = {
            "id": bot.id,
            "name": bot.name,
            "gender": bot.gender,
            "avatar_url": bot.avatar_url,
            "personality": bot.personality,
            "welcome_message": bot.welcome_message,
            "introduction": bot.introduction,
            "tags": tags,
        }
        
        return BotDisplay(**bot_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
