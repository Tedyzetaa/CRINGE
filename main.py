from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import json
import uuid
from typing import List, Optional
import os

app = FastAPI(title="CRINGE API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Tabelas criadas com sucesso!")

# Routes
@app.get("/")
async def root():
    return {
        "message": "🚀 CRINGE API está rodando!",
        "version": "1.0.0",
        "endpoints": {
            "GET /bots": "Listar todos os bots",
            "GET /bots/{bot_id}": "Obter um bot específico",
            "POST /bots/import": "Importar bots via JSON",
            "DELETE /bots/{bot_id}": "Excluir um bot",
            "POST /bots/chat/{bot_id}": "Chat com um bot",
            "GET /conversations/{conversation_id}": "Obter histórico de conversa"
        }
    }

@app.get("/bots", response_model=List[BotResponse])
async def get_bots():
    """Listar todos os bots"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bots")
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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar bot: {str(e)}")

@app.post("/bots/import")
async def import_bots(import_request: ImportRequest):
    """Importar múltiplos bots"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        imported_count = 0
        for bot_data in import_request.bots:
            bot_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO bots (
                    id, creator_id, name, gender, introduction, personality,
                    welcome_message, avatar_url, tags, conversation_context,
                    context_images, system_prompt, ai_config
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bot_id,
                bot_data.creator_id,
                bot_data.name,
                bot_data.gender,
                bot_data.introduction,
                bot_data.personality,
                bot_data.welcome_message,
                bot_data.avatar_url,
                json.dumps(bot_data.tags),
                bot_data.conversation_context,
                bot_data.context_images,
                bot_data.system_prompt,
                json.dumps(bot_data.ai_config)
            ))
            
            imported_count += 1
        
        conn.commit()
        conn.close()
        
        return {
            "message": f"✅ {imported_count} bots importados com sucesso!",
            "imported_count": imported_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao importar bots: {str(e)}")

@app.delete("/bots/{bot_id}")
async def delete_bot(bot_id: str):
    """Excluir um bot e suas conversas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se o bot existe
        cursor.execute("SELECT id FROM bots WHERE id = ?", (bot_id,))
        bot = cursor.fetchone()
        
        if not bot:
            return JSONResponse(
                status_code=404,
                content={"error": "Bot não encontrado"}
            )
        
        # Primeiro excluir as mensagens das conversas deste bot
        cursor.execute('''
            DELETE FROM messages 
            WHERE conversation_id IN (
                SELECT id FROM conversations WHERE bot_id = ?
            )
        ''', (bot_id,))
        
        # Depois excluir as conversas
        cursor.execute("DELETE FROM conversations WHERE bot_id = ?", (bot_id,))
        
        # Finalmente excluir o bot
        cursor.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Bot excluído com sucesso",
            "deleted_bot_id": bot_id
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Erro ao excluir bot: {str(e)}"}
        )

@app.post("/bots/chat/{bot_id}")
async def chat_with_bot(bot_id: str, chat_request: ChatRequest):
    """Chat com um bot específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se o bot existe
        cursor.execute("SELECT * FROM bots WHERE id = ?", (bot_id,))
        bot = cursor.fetchone()
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot não encontrado")
        
        bot_dict = dict(bot)
        bot_dict['tags'] = json.loads(bot_dict['tags'])
        bot_dict['ai_config'] = json.loads(bot_dict['ai_config'])
        
        # Criar nova conversa se não existir
        conversation_id = chat_request.conversation_id
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO conversations (id, bot_id) VALUES (?, ?)",
                (conversation_id, bot_id)
            )
        
        # Salvar mensagem do usuário
        user_message_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO messages (id, conversation_id, content, is_user) VALUES (?, ?, ?, ?)",
            (user_message_id, conversation_id, chat_request.message, True)
        )
        
        # Aqui você integraria com o serviço de IA
        # Por enquanto, vamos simular uma resposta
        ai_response = f"🤖 [{bot_dict['name']}]: Esta é uma resposta simulada para: '{chat_request.message}'. Configure o serviço de IA para respostas reais."
        
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
            "bot_id": bot_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no chat: {str(e)}")

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Obter histórico completo de uma conversa"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se a conversa existe
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        conversation = cursor.fetchone()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")
        
        # Buscar mensagens ordenadas por data
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
        raise HTTPException(status_code=500, detail=f"Erro ao buscar conversa: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "CRINGE API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
