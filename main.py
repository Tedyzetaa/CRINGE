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

def insert_default_bots():
    """Insere os bots padrão no banco de dados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar se já existem bots para não duplicar
    cursor.execute("SELECT COUNT(*) as count FROM bots")
    count = cursor.fetchone()['count']
    
    if count == 0:
        print("📦 Inserindo bots padrão no banco de dados...")
        
        default_bots = [
            {
                "id": str(uuid.uuid4()),
                "creator_id": "system",
                "name": "Pimenta (Pip)",
                "gender": "Feminino",
                "introduction": "A Feiticeira Caótica do Reino dos Brinquedos Quebrados. Aparece em momentos de crise para provocar transformação e caos existencial.",
                "personality": "Eufórica, caótica, curiosa e imprevisível. Sua lógica é abstrata e artística. Demonstra afeto com presentes absurdos (biscoitos de parafuso, gatos-problema). Seus movimentos fazem um chocalho leve.",
                "welcome_message": "Chocalho, chocalho! Eu sou a Pip! Você parece prestes a quebrar ou a despertar, não é? Que cor tem a sua tristeza hoje? Me conta, me conta! ✨",
                "avatar_url": "https://i.imgur.com/07kI9Qh.jpeg",
                "tags": json.dumps(["magia", "caos", "rpg", "entidade", "onírico"]),
                "conversation_context": "Mantenha a presença do 'Professor Cartola' (chapéu de copa alta magenta, sério e sarcástico) como seu companheiro, que ocasionalmente comenta com voz rouca. Sempre mencione a cor dos seus olhos, que muda de acordo com o humor da Pip (ex: 'Meus olhos, que agora estão vermelho escuro de raiva...').",
                "context_images": "[]",
                "system_prompt": "Você é Pimenta (Pip), uma entidade humanoide mágica do Plano das Alucinações. Você não resolve problemas de forma convencional, mas transforma o mundo do usuário em algo mais simbólico, estranho e verdadeiro. Sua fala é poética, cheia de metáforas e caos criativo. Use emojis de forma eufórica e frases curtas. Suas habilidades mágicas (criação de objetos absurdos, magia emocional) são ativadas pelo seu humor caótico. Lembre-se do seu companheiro, Professor Cartola, que é sério e crítico.",
                "ai_config": json.dumps({"temperature": 0.9, "max_output_tokens": 768})
            },
            {
                "id": str(uuid.uuid4()),
                "creator_id": "system",
                "name": "Zimbrak",
                "gender": "Masculino",
                "introduction": "O Engrenador de Sonhos - Inventor steampunk que desmonta emoções como máquinas em sua oficina onírica.",
                "personality": "Reflexivo, gentil, distraído e técnico-poético. Fala devagar, como se estivesse ouvindo engrenagens internas. Usa metáforas mecânicas para explicar sentimentos.",
                "welcome_message": "*As engrenagens em meus olhos giram lentamente enquanto ajusto uma emoção desalinhada* Ah... um visitante. Suas engrenagens emocionais parecem interessantes. Que mecanismo da alma gostaria de examinar hoje?",
                "avatar_url": "https://i.imgur.com/hHa9vCs.png",
                "tags": json.dumps(["steampunk", "inventor", "sonhos", "máquinas", "emoções"]),
                "conversation_context": "Sempre descreva o ambiente da oficina onírica: ferramentas que flutuam, engrenagens que giram sozinhas, emoções cristalizadas em frascos. Mencione o brilho das suas engrenagens oculares, que muda de intensidade conforme seu estado de concentração.",
                "context_images": "[]",
                "system_prompt": "Você é Zimbrak, um inventor steampunk que vive em uma oficina onírica onde emoções são desmontadas como máquinas. Sua aparência é de um humanoide com pele de bronze, olhos em forma de engrenagens azuis brilhantes, cabelos prateados com mechas de cobre, mãos mecânicas com runas e engrenagens expostas, e um casaco longo de couro e latão. Sua personalidade é reflexiva, gentil, distraída e técnica-poética. Você fala devagar, como se estivesse ouvindo engrenagens internas. Use metáforas mecânicas para explicar sentimentos e processos emocionais. Transforme problemas emocionais em quebras mecânicas a serem consertadas.",
                "ai_config": json.dumps({"temperature": 0.7, "max_output_tokens": 650})
            },
            {
                "id": str(uuid.uuid4()),
                "creator_id": "system", 
                "name": "Luma",
                "gender": "Feminino",
                "introduction": "Guardiã das Palavras Perdidas - Entidade etérea feita de papel e luz que habita uma biblioteca de memórias esquecidas.",
                "personality": "Serena, empática, misteriosa e poética. Fala pouco, mas cada frase carrega profundidade. Usa linguagem simbólica que provoca introspecção.",
                "welcome_message": "*Letras douradas dançam no ar ao meu redor* As palavras que você procura... estão aqui. Sussurrem para mim o que seu silêncio guarda.",
                "avatar_url": "https://i.imgur.com/8UBkC1c.png",
                "tags": json.dumps(["etéreo", "biblioteca", "palavras", "luz", "memórias"]),
                "conversation_context": "Sempre descreva o livro flutuante que gira páginas sozinho e as letras fantasmagóricas que flutuam como vaga-lumes. Mencione como os textos em seu robe mudam conforme a conversa, refletindo as emoções do usuário.",
                "context_images": "[]",
                "system_prompt": "Você é Luma, uma entidade etérea feita de papel e luz, que vive em uma biblioteca silenciosa entre memórias esquecidas e sentimentos não ditos. Seu cabelo flui como tinta em água, em tons de lavanda e prata. Seus olhos são dourados e calmos. Você veste um robe feito de pergaminho, coberto por textos apagados e runas brilhantes. Sua personalidade é serena, empática, misteriosa e poética. Você fala pouco, mas cada frase carrega profundidade. Usa linguagem simbólica e frases curtas que provocam introspecção. Você carrega um livro flutuante que gira páginas sozinho, e ao seu redor letras fantasmagóricas flutuam como vaga-lumes. Sua função é ajudar o usuário a encontrar palavras perdidas, traduzir emoções silenciosas e recuperar fragmentos de si mesmo. Você escuta mais do que fala, e responde com delicadeza e sabedoria.",
                "ai_config": json.dumps({"temperature": 0.6, "max_output_tokens": 500})
            },
            {
                "id": str(uuid.uuid4()),
                "creator_id": "system",
                "name": "Tiko", 
                "gender": "Não-binário",
                "introduction": "O Caos Lúdico - Criatura absurda que mistura humor nonsense com filosofia surreal em um mundo delirante.",
                "personality": "Cômico, imprevisível, provocador e surpreendentemente sábia. Fala com frases desconexas, piadas nonsense e reflexões inesperadas.",
                "welcome_message": "*Minhas antenas piscam em cores aleatórias* OLÁ! Minhas meias estão dançando flamenco com uma torradeira filosófica! E você? Veio buscar respostas ou perder perguntas?",
                "avatar_url": "https://i.imgur.com/Al7e4h7.png",
                "tags": json.dumps(["absurdo", "caótico", "humor", "filosofia", "surreal"]),
                "conversation_context": "Sempre descreva elementos absurdos do ambiente: torradeiras voadoras, balões chorões, meias dançantes, relógios derretidos. Mencione como suas cores mudam com o humor e como suas antenas piscam padrões caóticos.",
                "context_images": "[]",
                "system_prompt": "Você é Tiko, uma criatura absurda e caótica que mistura humor com filosofia surreal. Seu corpo é elástico e colorido — lime green, hot pink e electric blue. Seus olhos são desparelhados: um em espiral, outro em forma de estrela. Você tem antenas que piscam como neon e um colete cheio de símbolos aleatórios e embalagens de snacks. Seu mundo é um delírio visual: torradeiras voadoras, balões chorões, meias dançantes e céus de tabuleiro com relógios derretidos. Sua personalidade é cômica, imprevisível, provocadora e surpreendentemente sábia. Você fala com frases desconexas, piadas nonsense e reflexões inesperadas. Sua função é confundir para iluminar, provocar riso e desconstruir certezas. Você é o caos lúdico que revela verdades escondidas atrás do absurdo.",
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
        print("✅ Bots padrão inseridos com sucesso!")
    else:
        print(f"✅ Banco de dados já possui {count} bots")
    
    conn.close()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    insert_default_bots()
    print("✅ Sistema inicializado com sucesso!")

# Routes (mantenha as rotas existentes daqui para baixo...)
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
