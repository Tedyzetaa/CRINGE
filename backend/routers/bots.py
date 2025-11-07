from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import uuid
import logging
import random

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
    """Chat com bot usando OpenRouter com prevenção de loop"""
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
        logger.info(f"🤖 Gerando resposta para: {request.user_message[:50]}...")
        
        # Usar o método to_dict do model
        bot_dict = bot.to_dict()
        
        ai_response = ai_service.generate_response(
            bot_data=bot_dict,
            ai_config=ai_config,
            user_message=request.user_message,
            chat_history=request.chat_history
        )
        
        # 🔥 PREVENÇÃO DE LOOP: Se a resposta for erro, usar fallback criativo
        if any(keyword in ai_response.lower() for keyword in ['❌', 'erro', 'dificuldade', 'problema', 'falha', 'todos os modelos']):
            logger.warning("⚠️ Usando fallback criativo devido a erro na IA")
            
            # Fallbacks específicos para cada bot baseados na personalidade
            fallback_responses = {
                "Pimenta (Pip)": [
                    "💫 *Meus olhos piscam em cores confusas* Chocalho, chocalho! Minhas engrenagens mágicas estão um pouco enferrujadas hoje! Mas eu sinto sua energia - quer um chá de risos enlatados enquanto me reorganizo?",
                    "🎪 *Fazendo malabarismos com estrelas invisíveis* Opa! Parece que minhas palavras fugiram para o País das Maravilhas! Enquanto busco elas, me conte um segredo seu!",
                    "✨ *Meu vestido vira um redemoinho de cores* Professor Cartola está resmungando sobre 'sinais cósmicos instáveis'! Ignore ele! O que sua alma está sussurrando hoje?"
                ],
                "Zimbrak": [
                    "⚙️ *Minhas engrenagens oculares giram lentamente* Parece que uma emoção desalinhada está afetando meus circuitos. Enquanto recalibro, conte-me sobre os mecanismos da sua alma hoje.",
                    "🔧 *Ferramentas flutuam em padrões caóticos* Hmm, meus sistemas de conversação estão precisando de ajustes. Mas sua presença é um catalisador interessante. Como posso ajudá-lo?",
                    "🌌 *Luzes azuis piscam suavemente* Estou experienciando uma falha temporal momentânea. No entanto, sua energia emocional é perfeitamente legível. Compartilhe seus pensamentos."
                ],
                "Luma": [
                    "📖 *Letras douradas dançam lentamente* Meus textos estão se reorganizando... o silêncio entre nós também fala. O que seu coração guarda?",
                    "💡 *Luz suave emana do meu robe* Momentos de quietude podem ser mais eloquentes. Enquanto minhas palavras se recompõem, sinta-se à vontade para compartilhar seus sentimentos.",
                    "🌙 *Páginas viram suavemente no ar* A biblioteca está um pouco sonolenta hoje... mas suas histórias são sempre bem-vindas. O que trás em sua mente?"
                ],
                "Tiko": [
                    "🎈 *Minhas antenas piscam em padrões aleatórios* OLÁ! Minhas palavras fugiram para dançar com as torradeiras filosóficas! Enquanto as recolho, me conte uma coisa ABSURDA!",
                    "🌈 *Cores vibrantes pulsam pelo meu corpo* OPSSS! Parece que engoli um dicionário de trás para frente! Mas isso é CHATO! Vamos falar de coisas IMPORTANTEMENTE irrelevantes!",
                    "🎪 *Fazendo cambalhotas verbais* MEUS circuitos estão fazendo festa sem mim! Que tal ignorarmos a lógica e mergulharmos no ABSURDO?"
                ]
            }
            
            # Encontrar fallback para o bot atual ou usar genérico
            bot_name = bot_dict['name']
            if bot_name in fallback_responses:
                ai_response = random.choice(fallback_responses[bot_name])
            else:
                generic_fallbacks = [
                    f"✨ {bot_name}: Estou passando por uma reinicialização criativa momentânea! Sua energia, no entanto, é perfeitamente clara. Vamos continuar nossa conversa?",
                    f"🎭 {bot_name}: Meus circuitos estão dançando uma valsa incomum hoje! Mas sua presença é o melhor ajuste. O que gostaria de compartilhar?",
                    f"💫 {bot_name}: Estou realinhando minhas frequências existenciais! Enquanto isso, sua voz é minha bússola. Conte-me mais..."
                ]
                ai_response = random.choice(generic_fallbacks)
        
        logger.info(f"✅ Resposta gerada: {ai_response[:100]}...")
        return ChatResponse(ai_response=ai_response)
        
    except Exception as e:
        error_msg = f"Erro na IA: {str(e)}"
        logger.error(f"❌ {error_msg}")
        
        # Fallback criativo em caso de erro geral
        fallbacks = [
            f"🎪 {bot.name}: Meus fios de fantasia se embaraçaram em uma dança cósmica! Enquanto os desenrolo, conte-me o que traz em seu coração...",
            f"✨ {bot.name}: O vento digital está soprando minhas palavras para direções inesperadas! Mas sinto sua energia - que tal continuarmos nossa jornada conversacional?",
            f"💫 {bot.name}: Estou passando por uma metamorfose linguística momentânea! Sua presença, no entanto, é minha âncora. Compartilhe seus pensamentos..."
        ]
        fallback = random.choice(fallbacks)
        return ChatResponse(ai_response=fallback)

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

@router.delete("/{bot_id}")
def delete_bot(bot_id: str, db: Session = Depends(get_db)):
    """Excluir um bot específico"""
    try:
        logger.info(f"🗑️ Tentando excluir bot {bot_id}")
        bot = db.query(Bot).filter(Bot.id == bot_id).first()
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot não encontrado")
        
        bot_name = bot.name
        db.delete(bot)
        db.commit()
        
        logger.info(f"✅ Bot {bot_name} excluído com sucesso")
        return {"message": f"Bot '{bot_name}' excluído com sucesso", "deleted_id": bot_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao excluir bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/health/ai")
def check_ai_health():
    """Verificar saúde do serviço de IA"""
    if not ai_service:
        return {
            "status": "unhealthy",
            "service": "AIService",
            "message": "Serviço de IA não disponível"
        }
    
    try:
        # Testar conexão básica
        test_result = ai_service._test_api_connection() if hasattr(ai_service, '_test_api_connection') else False
        
        return {
            "status": "healthy" if test_result else "unhealthy",
            "service": "AIService",
            "api_connected": test_result,
            "current_model": getattr(ai_service, 'current_model', 'unknown'),
            "api_key_set": bool(getattr(ai_service, 'api_key', None))
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "AIService",
            "error": str(e)
        }
