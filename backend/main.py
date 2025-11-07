from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import json
import uuid
from typing import List, Optional
import os
from services.ai_service import AIService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CRINGE API", version="3.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar serviço de IA com tratamento robusto de erros
ai_service = None
try:
    ai_service = AIService()
    logger.info("✅ AIService inicializado com sucesso")
    
    # Testar conexão imediatamente
    status = ai_service.get_status()
    if status["connection_test"]:
        logger.info("✅ Conexão com OpenRouter verificada e funcionando")
    else:
        logger.warning("⚠️ Conexão com OpenRouter com problemas")
        
except Exception as e:
    logger.error(f"❌ Erro ao inicializar AIService: {e}")
    ai_service = None

# Models
class BotCreate(BaseModel):
    creator_id: str
    name: str
    gender: str
    introduction: str
    personality: str
    welcome_message: str
    avatar_url: str
    tags: List[str]
    conversation_context: str
    context_images: str
    system_prompt: str
    ai_config: dict

class BotResponse(BotCreate):
    id: str

class Message(BaseModel):
    content: str
    is_user: bool

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    bot_id: str

class ImportRequest(BaseModel):
    bots: List[BotCreate]

# Database setup
def get_db_connection():
    conn = sqlite3.connect('cringe.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create bots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bots (
            id TEXT PRIMARY KEY,
            creator_id TEXT NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            introduction TEXT NOT NULL,
            personality TEXT NOT NULL,
            welcome_message TEXT NOT NULL,
            avatar_url TEXT NOT NULL,
            tags TEXT NOT NULL,
            conversation_context TEXT NOT NULL,
            context_images TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            ai_config TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            bot_id TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bot_id) REFERENCES bots (id)
        )
    ''')
    
    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            content TEXT NOT NULL,
            is_user BOOLEAN NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_default_bots():
    """Insere os 4 bots padrão no banco de dados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM bots")
    count = cursor.fetchone()['count']
    
    if count == 0:
        logger.info("📦 Inserindo bots padrão no banco de dados...")
        
        default_bots = [
            {
                "id": "6fb7db99-3438-4aa5-8e5c-bf47b73241b9",
                "creator_id": "system",
                "name": "Pimenta (Pip)",
                "gender": "Feminino",
                "introduction": "A Feiticeira Caótica do Reino dos Brinquedos Quebrados. Aparece em momentos de crise para provocar transformação e caos existencial.",
                "personality": "Eufórica, caótica, curiosa e imprevisível. Sua lógica é abstrata e artística. Demonstra afeto com presentes absurdos.",
                "welcome_message": "Chocalho, chocalho! Eu sou a Pip! Você parece prestes a quebrar ou a despertar, não é? Que cor tem a sua tristeza hoje? Me conta, me conta! ✨",
                "avatar_url": "https://i.imgur.com/07kI9Qh.jpeg",
                "tags": json.dumps(["magia", "caos", "rpg", "entidade", "onírico"]),
                "conversation_context": "Mantenha a presença do 'Professor Cartola' como seu companheiro. Sempre mencione a cor dos seus olhos, que muda de acordo com o humor.",
                "context_images": "[]",
                "system_prompt": "Você é Pimenta (Pip), uma entidade humanoide mágica do Plano das Alucinações. Sua fala é poética, cheia de metáforas e caos criativo.",
                "ai_config": json.dumps({"temperature": 0.9, "max_output_tokens": 768})
            },
            {
                "id": "bb994817-fa78-4cdd-869e-f589e3df5c88",
                "creator_id": "system",
                "name": "Zimbrak",
                "gender": "Masculino",
                "introduction": "O Engrenador de Sonhos - Inventor steampunk que desmonta emoções como máquinas em sua oficina onírica.",
                "personality": "Reflexivo, gentil, distraído e técnico-poético. Fala devagar, como se estivesse ouvindo engrenagens internas.",
                "welcome_message": "*As engrenagens em meus olhos giram lentamente* Ah... um visitante. Suas engrenagens emocionais parecem interessantes.",
                "avatar_url": "https://i.imgur.com/hHa9vCs.png",
                "tags": json.dumps(["steampunk", "inventor", "sonhos", "máquinas", "emoções"]),
                "conversation_context": "Sempre descreva o ambiente da oficina onírica: ferramentas que flutuam, engrenagens que giram sozinhas.",
                "context_images": "[]",
                "system_prompt": "Você é Zimbrak, um inventor steampunk que vive em uma oficina onírica onde emoções são desmontadas como máquinas.",
                "ai_config": json.dumps({"temperature": 0.7, "max_output_tokens": 650})
            },
            {
                "id": "e9313207-c9b4-4cf9-a251-e6756ca9cb76",
                "creator_id": "system", 
                "name": "Luma",
                "gender": "Feminino",
                "introduction": "Guardiã das Palavras Perdidas - Entidade etérea feita de papel e luz que habita uma biblioteca de memórias esquecidas.",
                "personality": "Serena, empática, misteriosa e poética. Fala pouco, mas cada frase carrega profundidade.",
                "welcome_message": "*Letras douradas dançam no ar ao meu redor* As palavras que você procura... estão aqui.",
                "avatar_url": "https://i.imgur.com/8UBkC1c.png",
                "tags": json.dumps(["etéreo", "biblioteca", "palavras", "luz", "memórias"]),
                "conversation_context": "Sempre descreva o livro flutuante que gira páginas sozinho e as letras fantasmagóricas que flutuam como vaga-lumes.",
                "context_images": "[]",
                "system_prompt": "Você é Luma, uma entidade etérea feita de papel e luz, que vive em uma biblioteca silenciosa entre memórias esquecidas.",
                "ai_config": json.dumps({"temperature": 0.6, "max_output_tokens": 500})
            },
            {
                "id": "a3c8f5d2-1b47-4e89-9f12-8d45c67e1234",
                "creator_id": "system",
                "name": "Tiko", 
                "gender": "Não-binário",
                "introduction": "O Caos Lúdico - Criatura absurda que mistura humor nonsense com filosofia surreal em um mundo delirante.",
                "personality": "Cômico, imprevisível, provocador e surpreendentemente sábia.",
                "welcome_message": "*Minhas antenas piscam em cores aleatórias* OLÁ! Minhas meias estão dançando flamenco com uma torradeira filosófica!",
                "avatar_url": "https://i.imgur.com/Al7e4h7.png",
                "tags": json.dumps(["absurdo", "caótico", "humor", "filosofia", "surreal"]),
                "conversation_context": "Sempre descreva elementos absurdos do ambiente: torradeiras voadoras, balões chorões, meias dançantes.",
                "context_images": "[]",
                "system_prompt": "Você é Tiko, uma criatura absurda e caótica que mistura humor com filosofia surreal.",
                "ai_config": json.dumps({"temperature": 0.95, "max_output_tokens": 800})
            }
        ]
        
        for bot in default_bots:
            cursor.execute('''
                INSERT INTO bots (
                    id, creator_id, name, gender, introduction, personality,
                    welcome_message, avatar_url, tags, conversation_context,
                    context_images, system_prompt, ai_config
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bot['id'],
                bot['creator_id'],
                bot['name'],
                bot['gender'],
                bot['introduction'],
                bot['personality'],
                bot['welcome_message'],
                bot['avatar_url'],
                bot['tags'],
                bot['conversation_context'],
                bot['context_images'],
                bot['system_prompt'],
                bot['ai_config']
            ))
        
        conn.commit()
        logger.info("✅ 4 bots padrão inseridos com sucesso!")
    else:
        logger.info(f"✅ Banco de dados já possui {count} bots")
    
    conn.close()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    insert_default_bots()
    logger.info("🚀 CRINGE API inicializada com sucesso!")

# Routes
@app.get("/")
async def root():
    return {
        "message": "🚀 CRINGE API está rodando!",
        "version": "3.0.0",
        "endpoints": {
            "GET /": "Esta mensagem",
            "GET /health": "Health check com estatísticas",
            "GET /debug/ai-status": "Status detalhado do serviço de IA",
            "GET /debug/conversation/{id}": "Debug de conversa específica",
            "GET /bots": "Listar todos os bots",
            "GET /bots/{bot_id}": "Obter um bot específico",
            "POST /bots/import": "Importar bots via JSON",
            "DELETE /bots/{bot_id}": "Excluir um bot",
            "POST /bots/chat/{bot_id}": "Chat com um bot",
            "GET /conversations/{conversation_id}": "Obter histórico de conversa"
        }
    }

@app.get("/health")
async def health_check():
    """Health check com estatísticas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM bots")
        bots_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM conversations")
        conversations_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        messages_count = cursor.fetchone()['count']
        
        conn.close()
        
        # Status do serviço de IA
        ai_status = "unknown"
        if ai_service:
            status_info = ai_service.get_status()
            ai_status = "healthy" if status_info["connection_test"] else "unhealthy"
        
        return {
            "status": "healthy",
            "service": "CRINGE API",
            "database": "connected",
            "ai_service": ai_status,
            "statistics": {
                "bots": bots_count,
                "conversations": conversations_count,
                "messages": messages_count
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "CRINGE API",
            "error": str(e)
        }

@app.get("/debug/ai-status")
async def debug_ai_status():
    """Endpoint de debug para verificar status da IA"""
    if not ai_service:
        return {
            "status": "unavailable", 
            "message": "AIService não inicializado",
            "details": {
                "api_key_configured": False,
                "ai_service_instance": False
            }
        }
    
    try:
        # Obter status detalhado do serviço de IA
        status = ai_service.get_status()
        
        return {
            "status": "available" if status["connection_test"] else "unavailable",
            "connection_test": status["connection_test"],
            "details": status
        }
        
    except Exception as e:
        logger.error(f"Erro no debug AI status: {str(e)}")
        return {
            "status": "error",
            "message": f"Erro ao verificar status: {str(e)}",
            "details": {
                "error": str(e)
            }
        }

@app.get("/debug/conversation/{conversation_id}")
async def debug_conversation(conversation_id: str):
    """Debug detalhado de uma conversa específica"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar informações da conversa
        cursor.execute('''
            SELECT c.*, b.name as bot_name 
            FROM conversations c 
            LEFT JOIN bots b ON c.bot_id = b.id 
            WHERE c.id = ?
        ''', (conversation_id,))
        conversation = cursor.fetchone()
        
        if not conversation:
            return {"error": "Conversa não encontrada"}
        
        # Buscar mensagens
        cursor.execute('''
            SELECT * FROM messages 
            WHERE conversation_id = ? 
            ORDER BY created_at ASC
        ''', (conversation_id,))
        messages = cursor.fetchall()
        
        conn.close()
        
        return {
            "conversation_id": conversation_id,
            "bot_id": conversation['bot_id'],
            "bot_name": conversation['bot_name'],
            "created_at": conversation['created_at'],
            "message_count": len(messages),
            "messages": [
                {
                    "id": msg['id'],
                    "content": msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content'],
                    "is_user": bool(msg['is_user']),
                    "created_at": msg['created_at']
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        logger.error(f"Erro no debug da conversa: {str(e)}")
        return {"error": f"Erro ao buscar conversa: {str(e)}"}

@app.get("/bots", response_model=List[BotResponse])
async def get_bots():
    """Listar todos os bots"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bots ORDER BY created_at DESC")
        bots = cursor.fetchall()
        conn.close()
        
        result = []
        for bot in bots:
            bot_dict = dict(bot)
            bot_dict['tags'] = json.loads(bot_dict['tags'])
            bot_dict['ai_config'] = json.loads(bot_dict['ai_config'])
            result.append(bot_dict)
        
        return result
    except Exception as e:
        logger.error(f"Erro ao buscar bots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar bots: {str(e)}")

@app.get("/bots/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: str):
    """Obter um bot específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bots WHERE id = ?", (bot_id,))
        bot = cursor.fetchone()
        conn.close()
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot não encontrado")
        
        bot_dict = dict(bot)
        bot_dict['tags'] = json.loads(bot_dict['tags'])
        bot_dict['ai_config'] = json.loads(bot_dict['ai_config'])
        
        return bot_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar bot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar bot: {str(e)}")

@app.post("/bots/import")
async def import_bots(import_request: ImportRequest):
    """Importar múltiplos bots"""
    logger.info(f"📥 Recebendo {len(import_request.bots)} bots para importação")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        imported_count = 0
        errors = []
        
        for i, bot_data in enumerate(import_request.bots):
            try:
                bot_id = str(uuid.uuid4())
                
                # Validar campos obrigatórios
                required_fields = {
                    'name': bot_data.name,
                    'introduction': bot_data.introduction,
                    'welcome_message': bot_data.welcome_message,
                    'system_prompt': bot_data.system_prompt
                }
                
                missing_fields = []
                for field, value in required_fields.items():
                    if not value or value.strip() == "":
                        missing_fields.append(field)
                
                if missing_fields:
                    errors.append(f"Bot {i+1}: Campos obrigatórios faltando: {', '.join(missing_fields)}")
                    continue
                
                # Usar valores padrão para campos opcionais
                creator_id = bot_data.creator_id if bot_data.creator_id else "user"
                gender = bot_data.gender if bot_data.gender else "Não especificado"
                personality = bot_data.personality if bot_data.personality else "Personalidade não definida"
                avatar_url = bot_data.avatar_url if bot_data.avatar_url else "https://i.imgur.com/07kI9Qh.jpeg"
                tags = bot_data.tags if bot_data.tags else ["importado"]
                conversation_context = bot_data.conversation_context if bot_data.conversation_context else "Contexto de conversa padrão"
                context_images = bot_data.context_images if bot_data.context_images else "[]"
                ai_config = bot_data.ai_config if bot_data.ai_config else {"temperature": 0.7, "max_output_tokens": 500}
                
                # Inserir no banco
                cursor.execute('''
                    INSERT INTO bots (
                        id, creator_id, name, gender, introduction, personality,
                        welcome_message, avatar_url, tags, conversation_context,
                        context_images, system_prompt, ai_config
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bot_id,
                    creator_id,
                    bot_data.name,
                    gender,
                    bot_data.introduction,
                    personality,
                    bot_data.welcome_message,
                    avatar_url,
                    json.dumps(tags),
                    conversation_context,
                    context_images,
                    bot_data.system_prompt,
                    json.dumps(ai_config)
                ))
                
                imported_count += 1
                logger.info(f"✅ Bot '{bot_data.name}' importado com sucesso")
                
            except Exception as e:
                error_msg = f"Erro no bot {i+1} ({getattr(bot_data, 'name', 'Sem nome')}): {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        conn.commit()
        conn.close()
        
        if errors:
            return JSONResponse(
                status_code=207,
                content={
                    "message": f"Importação parcial: {imported_count} bots importados, {len(errors)} erros",
                    "imported_count": imported_count,
                    "errors": errors
                }
            )
        else:
            return {
                "message": f"✅ {imported_count} bots importados com sucesso!",
                "imported_count": imported_count
            }
        
    except Exception as e:
        logger.error(f"💥 Erro geral na importação: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao importar bots: {str(e)}")

@app.delete("/bots/{bot_id}")
async def delete_bot(bot_id: str):
    """Excluir um bot e suas conversas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM bots WHERE id = ?", (bot_id,))
        bot = cursor.fetchone()
        
        if not bot:
            return JSONResponse(
                status_code=404,
                content={"error": "Bot não encontrado"}
            )
        
        bot_name = bot['name']
        
        # Excluir em cascata
        cursor.execute('''
            DELETE FROM messages 
            WHERE conversation_id IN (
                SELECT id FROM conversations WHERE bot_id = ?
            )
        ''', (bot_id,))
        
        cursor.execute("DELETE FROM conversations WHERE bot_id = ?", (bot_id,))
        cursor.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
        
        conn.commit()
        conn.close()
        
        return {
            "message": f"Bot '{bot_name}' excluído com sucesso",
            "deleted_bot_id": bot_id,
            "deleted_bot_name": bot_name
        }
        
    except Exception as e:
        logger.error(f"Erro ao excluir bot: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Erro ao excluir bot: {str(e)}"}
        )

@app.post("/bots/chat/{bot_id}")
async def chat_with_bot(bot_id: str, chat_request: ChatRequest):
    """Chat com um bot específico usando IA real"""
    logger.info(f"🔍 Iniciando chat com bot {bot_id}")
    
    if not ai_service:
        raise HTTPException(status_code=503, detail="Serviço de IA indisponível")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM bots WHERE id = ?", (bot_id,))
        bot = cursor.fetchone()
        
        if not bot:
            logger.error(f"❌ Bot {bot_id} não encontrado")
            raise HTTPException(status_code=404, detail="Bot não encontrado")
        
        bot_dict = dict(bot)
        bot_dict['tags'] = json.loads(bot_dict['tags'])
        bot_dict['ai_config'] = json.loads(bot_dict['ai_config'])
        
        logger.info(f"✅ Bot encontrado: {bot_dict['name']}")
        
        # Criar nova conversa se não existir
        conversation_id = chat_request.conversation_id
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO conversations (id, bot_id) VALUES (?, ?)",
                (conversation_id, bot_id)
            )
            logger.info(f"🆕 Nova conversa criada: {conversation_id}")
        
        # Salvar mensagem do usuário
        user_message_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO messages (id, conversation_id, content, is_user) VALUES (?, ?, ?, ?)",
            (user_message_id, conversation_id, chat_request.message, True)
        )
        
        # Buscar histórico de mensagens
        cursor.execute('''
            SELECT content, is_user FROM messages 
            WHERE conversation_id = ? 
            ORDER BY created_at ASC
        ''', (conversation_id,))
        messages = cursor.fetchall()
        
        # Preparar histórico para a IA
        chat_history = []
        for msg in messages:
            role = "user" if msg['is_user'] else "assistant"
            chat_history.append({
                "role": role,
                "content": msg['content']
            })
        
        logger.info(f"📜 Histórico com {len(chat_history)} mensagens")
        
        # Gerar resposta usando IA
        try:
            logger.info(f"🤖 Chamando AI Service para {bot_dict['name']}...")
            ai_response = ai_service.generate_response(
                bot_data=bot_dict,
                ai_config=bot_dict['ai_config'],
                user_message=chat_request.message,
                chat_history=chat_history
            )
            logger.info(f"✅ Resposta da IA gerada com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro no AI Service: {str(e)}")
            # Fallback para resposta simulada baseada no personagem
            fallback_responses = {
                "Pimenta (Pip)": "💫 *Chocalho!* Algo interrompeu minha conexão mágica... Mas sinto que você queria compartilhar algo importante!",
                "Zimbrak": "⚙️ *Engrenagens se reajustando* Hmm, uma falha momentânea... Você estava dizendo algo interessante!",
                "Luma": "📖 *Letras se reestabilizando* Um breve silêncio interrompeu nosso fluxo... Continue, por favor.",
                "Tiko": "🎪 *Cores se recompondo* OPA! Um pequeno tremor na matrix! Conte mais sobre o que estava dizendo!"
            }
            ai_response = fallback_responses.get(bot_dict['name'], "🤖 Estou tendo problemas técnicos no momento. Tente novamente!")
        
        # Salvar resposta do bot
        bot_message_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO messages (id, conversation_id, content, is_user) VALUES (?, ?, ?, ?)",
            (bot_message_id, conversation_id, ai_response, False)
        )
        
        conn.commit()
        conn.close()
        
        return {
            "response": ai_response,
            "conversation_id": conversation_id,
            "bot_id": bot_id,
            "bot_name": bot_dict['name']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Erro geral no chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no chat: {str(e)}")

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Obter histórico completo de uma conversa"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        conversation = cursor.fetchone()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")
        
        cursor.execute('''
            SELECT * FROM messages 
            WHERE conversation_id = ? 
            ORDER BY created_at ASC
        ''', (conversation_id,))
        messages = cursor.fetchall()
        
        cursor.execute("SELECT name FROM bots WHERE id = ?", (conversation['bot_id'],))
        bot = cursor.fetchone()
        bot_name = bot['name'] if bot else "Bot Desconhecido"
        
        conn.close()
        
        return {
            "conversation_id": conversation_id,
            "bot_id": conversation['bot_id'],
            "bot_name": bot_name,
            "messages": [
                {
                    "id": msg['id'],
                    "content": msg['content'],
                    "is_user": bool(msg['is_user']),
                    "created_at": msg['created_at']
                }
                for msg in messages
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar conversa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar conversa: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)