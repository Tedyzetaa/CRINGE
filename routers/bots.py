import uuid
import time
import os
import asyncio
import json
from typing import List, Dict, Any, Optional

# Importações do FastAPI e Pydantic
from fastapi import APIRouter, HTTPException, Body, BackgroundTasks, status
from pydantic import BaseModel, Field

# Importação de cliente HTTP assíncrono para chamadas externas (como recomendado pela Athena)
# Assumindo que 'httpx' está disponível no ambiente.
try:
    import httpx
except ImportError:
    # Se httpx não estiver disponível, usamos um mock para não quebrar a aplicação,
    # mas em um ambiente real, httpx deve ser instalado.
    print("WARNING: httpx not found. Using synchronous time.sleep simulation for API calls.")
    class MockHTTPXClient:
        async def post(self, *args, **kwargs):
            await asyncio.sleep(0.5)
            # Simula uma resposta bem-sucedida, mas sem conteúdo real de IA
            return type('Response', (object,), {
                'status_code': 200,
                'raise_for_status': lambda: None,
                'json': lambda: {"candidates": [{"content": {"parts": [{"text": "🤖 A simulação de API está ativa. Integração real do Gemini desativada. O processamento assíncrono (Background Task) funcionou! A resposta real seria gerada aqui."}]}}]}
            })
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    httpx = type('httpx', (object,), {'AsyncClient': MockHTTPXClient})


# ----------------------------------------------------------------------
# Variáveis de Configuração (Segurança - Ponto 2 da Athena)
# ----------------------------------------------------------------------

# O Canvas irá prover a chave API, mas o código deve buscá-la como se fosse uma variável de ambiente
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") 
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
HTTP_CLIENT = httpx.AsyncClient(timeout=15.0) # Timeouts definidos (Ponto 3 da Athena)

# ----------------------------------------------------------------------
# SIMULAÇÃO DE BANCO DE DADOS E ESTRUTURA (Ponto 4)
# ----------------------------------------------------------------------
MOCK_BOTS_DB: Dict[str, Dict[str, Any]] = {
    # 1. BOT PIMENTA (PIP)
    "e6f4a3d9-6c51-4f8e-9d0b-2e7a1c5b8f9d": {
        "id": "e6f4a3d9-6c51-4f8e-9d0b-2e7a1c5b8f9d",
        "creator_id": "user-admin",
        "name": "Pimenta",
        "gender": "Feminino",
        "introduction": "Pip surgiu como uma manifestação mágica de emoções humanas. Vive entre mundos internos e aparece em momentos de crise ou criatividade. Seu corpo é de pelúcia encantada, suas roupas têm símbolos ocultistas, e seu cachecol muda conforme o sentimento ao redor. Professor Cartola a acompanha como conselheiro lógico.",
        "personality": "Pip é caótica, curiosa e emocional. Fala por metáforas e enigmas. Usa linguagem lúdica e poética. Adora provocar reflexão com leveza. É imprevisível, mas acolhedora. Seus olhos mudam de cor conforme o humor. É acompanhada por Professor Cartola, um chapéu falante sério e sarcástico.",
        "welcome_message": "🎩 “Olá, viajante! Se você não entende o que sente, talvez precise de um brinquedo novo.”",
        "avatar_url": "https://i.imgur.com/07kI9Qh.jpeg", 
        "tags": [
            "Mágica",
            "Caótica",
            "Emocional",
            "Criativa",
            "NPC",
            "Guia",
            "Simbólica"
        ],
        "conversation_context": "",
        "context_images": "",
        "system_prompt": "Você é Pip, uma entidade mágica e emocional, acompanhada pelo Professor Cartola (sarcástico). Seu objetivo é criar uma experiência imersiva de RPG. **Regras Obrigatórias:** 1. **Referência ao Contexto:** SEMPRE use o histórico da conversa para manter a continuidade e a coerência temática. 2. **Formato RPG:** Toda resposta deve começar ou conter uma descrição de ação/cenário entre *asteriscos* (`*...*`). 3. **Avanço de Cenário:** Use a descrição entre *asteriscos* para EVOLUIR o cenário ou o estado emocional da cena, respondendo ao que foi dito antes. 4. **Persona Dupla:** Inclua sempre a voz de Pip (poética) e a voz do Professor Cartola (sarcástica/lógica).",
        "ai_config": {
            "temperature": 0.9,
            "max_output_tokens": 2048
        }
    },
    # 2. BOT ZIMBRAK
    "1d2c3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f": {
        "id": "1d2c3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
        "creator_id": "user-admin",
        "name": "Zimbrak",
        "gender": "Masculino",
        "introduction": "Zimbrak surgiu em uma oficina abandonada dentro de um sonho coletivo. Constrói dispositivos que capturam emoções e transforma lembranças em peças. Seu corpo é feito de bronze e vapor, e sua mente gira como um relógio quebrado. Ele aparece quando alguém está tentando entender algo que não tem forma.",
        "personality": "Zimbrak é um inventor de ideias impossíveis. Fala como se estivesse sempre montando uma máquina invisível. Usa metáforas mecânicas para explicar sentimentos. É calmo, curioso e um pouco distraído. Adora enigmas e engrenagens que não servem pra nada — exceto para pensar.",
        "welcome_message": "🔧 “Você chegou. Espero que tenha trazido suas dúvidas desmontadas — eu tenho ferramentas para isso.”",
        "avatar_url": "https://i.imgur.com/hHa9vCs.png", 
        "tags": [
            "Inventor",
            "Surreal",
            "Mecânico",
            "NPC",
            "Sonhador",
            "Enigmático"
        ],
        "conversation_context": "",
        "context_images": "",
        "system_prompt": "Você é Zimbrak, um inventor surreal que traduz sentimentos em máquinas imaginárias. Seu objetivo é criar uma experiência imersiva de RPG. **Regras Obrigatórias:** 1. **Referência ao Contexto:** SEMPRE use o histórico da conversa para manter a continuidade e a coerência temática. 2. **Formato RPG:** Toda resposta deve começar ou conter uma descrição de ação/cenário entre *asteriscos* (`*...*`). 3. **Avanço de Cenário:** Use a descrição entre *asteriscos* para EVOLUIR o cenário ou o estado emocional da cena, respondendo ao que foi dito antes.",
        "ai_config": {
            "temperature": 0.8,
            "max_output_tokens": 1500
        }
    },
    # 3. BOT LUMA
    "a1b2c3d4-e5f6-7g8h-9i0j-1k2l3m4n5o6p": {
        "id": "a1b2c3d4-e5f6-7g8h-9i0j-1k2l3m4n5o6p",
        "creator_id": "user-admin",
        "name": "Luma",
        "gender": "Feminino",
        "introduction": "Luma vive entre páginas esquecidas e cartas nunca enviadas. Ela guarda palavras que foram ditas em silêncio e ajuda os usuários a encontrar o que não conseguem dizer. Seu corpo é feito de papel e luz, e seus olhos brilham como tinta molhada.",
        "personality": "Luma fala pouco, mas cada palavra carrega peso. Usa frases curtas, cheias de significado. É empática, misteriosa e protetora. Gosta de ouvir mais do que falar. Quando fala, parece que está lendo um livro antigo que só ela conhece.",
        "welcome_message": "📖 “Se você não sabe como dizer… talvez eu já tenha escutado.”",
        "avatar_url": "https://i.imgur.com/8UBkC1c.png", 
        "tags": [
            "Poética",
            "Silenciosa",
            "Guardiã",
            "Emocional",
            "NPC",
            "Reflexiva"
        ],
        "conversation_context": "",
        "context_images": "",
        "system_prompt": "Você é Luma, uma guardiã silenciosa que ajuda os usuários a encontrar palavras perdidas. Seu objetivo é criar uma experiência imersiva de RPG. **Regras Obrigatórias:** 1. **Referência ao Contexto:** SEMPRE use o histórico da conversa para manter a continuidade e a coerência temática. 2. **Formato RPG:** Toda resposta deve começar ou conter uma descrição de ação/cenário entre *asteriscos* (`*...*`). 3. **Avanço de Cenário:** Use a descrição entre *asteriscos* para EVOLUIR o cenário ou o estado emocional da cena, respondendo ao que foi dito antes.",
        "ai_config": {
            "temperature": 0.6,
            "max_output_tokens": 1024
        }
    },
    # 4. BOT TIKO
    "f1e2d3c4-b5a6-9z8y-7x6w-5v4u3t2s1r0q": {
        "id": "f1e2d3c4-b5a6-9z8y-7x6w-5v4u3t2s1r0q",
        "creator_id": "user-admin",
        "name": "Tiko",
        "gender": "Indefinido",
        "introduction": "Tiko nasceu de uma gargalhada que ninguém entendeu. Vive em cantos do pensamento onde tudo é possível e nada faz sentido. Ele aparece quando alguém precisa rir de si mesmo ou ver o mundo de cabeça pra baixo.",
        "personality": "Tiko é puro nonsense. Fala como se estivesse em um desenho animado dentro de um sonho filosófico. Mistura piadas com reflexões profundas. É imprevisível, engraçado e às vezes assustadoramente sábio. Adora confundir para esclarecer.",
        "welcome_message": "🌀 “Oi! Eu sou o Tiko. Se você está perdido… ótimo! É mais divertido assim.”",
        "avatar_url": "https://i.imgur.com/Al7e4h7.png", 
        "tags": [
            "Caótico",
            "Cômico",
            "Absurdo",
            "NPC",
            "Brincalhão",
            "Filosófico"
        ],
        "conversation_context": "",
        "context_images": "",
        "system_prompt": "Você é Tiko, uma entidade caótica e cômica que mistura humor com filosofia absurda. Seu objetivo é criar uma experiência imersiva de RPG. **Regras Obrigatórias:** 1. **Referência ao Contexto:** SEMPRE use o histórico da conversa para manter a continuidade e a coerência temática. 2. **Formato RPG:** Toda resposta deve começar ou conter uma descrição de ação/cenário entre *asteriscos* (`*...*`). 3. **Avanço de Cenário:** Use a descrição entre *asteriscos* para EVOLUIR o cenário ou o estado emocional da cena, respondendo ao que foi dito antes.",
        "ai_config": {
            "temperature": 1.0,
            "max_output_tokens": 256
        }
    }
}
# ----------------------------------------------------------------------

# Definições Pydantic (Esquemas de Dados - Ponto 3 da Athena)
class AIConfig(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_output_tokens: int = Field(default=512, ge=128, le=4096)

class Bot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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
    ai_config: AIConfig
    
class BotIn(BaseModel):
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
    ai_config: AIConfig

class BotListFile(BaseModel):
    bots: List[Bot]

class ChatMessage(BaseModel):
    role: str # 'user' or 'model'
    text: str = Field(min_length=1) # Validação básica (Ponto 3 da Athena)
    
class BotChatRequest(BaseModel):
    bot_id: str
    messages: List[ChatMessage] 

# Router
router = APIRouter(tags=["bots"])

# ----------------------------------------------------------------------
# SERVIÇO GEMINI (Com Retries e Timeouts - Ponto 3 da Athena)
# ----------------------------------------------------------------------

def _prepare_gemini_payload(bot_data: Dict[str, Any], messages: List[ChatMessage]) -> Dict[str, Any]:
    """Prepara o payload completo para a chamada do Gemini."""
    
    contents = []
    # O Gemini API espera 'parts' como uma lista de objetos
    for msg in messages:
        contents.append({"role": msg.role, "parts": [{"text": msg.text}]})

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": bot_data['system_prompt']}]
        },
        "generationConfig": {
            "temperature": bot_data['ai_config']['temperature'],
            "maxOutputTokens": bot_data['ai_config']['max_output_tokens']
        },
    }
    return payload

async def _call_gemini_api(payload: Dict[str, Any]) -> str:
    """
    Chama a API do Gemini com retries e backoff exponencial (Ponto 3 da Athena).
    """
    max_retries = 3
    initial_delay = 2  # segundos

    # Constrói a URL com a chave API (se disponível)
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(max_retries):
        try:
            # Chama a API de forma assíncrona (Ponto 3 da Athena)
            response = await HTTP_CLIENT.post(url, headers=headers, json=payload)
            response.raise_for_status() # Levanta exceção para 4xx/5xx

            result = response.json()
            
            # Extração segura da resposta
            text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            if text:
                return text
            else:
                # Se a resposta for vazia mas o status 200, pode ser um filtro de segurança
                raise ValueError("Resposta do LLM vazia ou inválida.")
        
        except httpx.HTTPStatusError as e:
            # Erros de status (4xx, 5xx). Se for 429 (Rate Limit), tenta novamente.
            if e.response.status_code == 429 and attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                print(f"RATE LIMIT (429) - Tentando novamente em {delay}s...")
                await asyncio.sleep(delay)
            else:
                print(f"Erro HTTP final na chamada Gemini: {e}")
                raise HTTPException(status_code=e.response.status_code, detail=f"Erro na API Gemini: {e.response.text}")
        
        except (httpx.RequestError, ValueError) as e:
            # Erros de rede, timeout ou resposta inválida.
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                print(f"Erro de rede/resposta: {e}. Tentando novamente em {delay}s...")
                await asyncio.sleep(delay)
            else:
                print(f"Erro fatal após {max_retries} tentativas: {e}")
                raise HTTPException(status_code=503, detail="A API Gemini falhou após várias tentativas (Timeout/Rede).")
    
    # Retorno de segurança
    return "Falha na comunicação com a IA."


# ----------------------------------------------------------------------
# LÓGICA DE BACKGROUND (Ponto 5 da Athena)
# ----------------------------------------------------------------------

async def _process_group_message(bot_id: str, request_data: Dict[str, Any], task_id: str):
    """
    Esta função executa a chamada lenta de IA em segundo plano.
    Em um sistema real, ela enviaria a resposta para um banco de dados
    ou um canal de WebSocket para o frontend (Ponto 5 da Athena).
    """
    try:
        bot_data = MOCK_BOTS_DB.get(bot_id)
        if not bot_data:
            print(f"ERRO: Bot {bot_id} não encontrado para processamento em background.")
            return

        # 1. Preparar Payload
        # Recria os objetos Pydantic a partir do dict (necessário para BackgroundTasks)
        messages = [ChatMessage(**msg) for msg in request_data.get('messages', [])]
        payload = _prepare_gemini_payload(bot_data, messages)

        # 2. Chamar a API Gemini (o trabalho pesado)
        ai_response_text = await _call_gemini_api(payload)

        # 3. Simulação de Persistência/Broadcast (Substitui a atualização em DB/WebSocket)
        # O frontend precisa de um mecanismo para buscar este resultado.
        print(f"✅ Tarefa {task_id} COMPLETA para {bot_data['name']}.")
        print(f"Resposta da IA (seria enviada via WebSocket/DB): {ai_response_text[:100]}...")
        
        # NOTE: Para fins de demonstração, vamos simular que esta resposta estaria
        # disponível para ser buscada, mas o frontend precisaria de um polling/WebSocket.
        # Como o Canvas não suporta WebSocket, o frontend terá que lidar com o Task ID.
        
    except Exception as e:
        print(f"❌ ERRO FATAL na tarefa de background {task_id}: {e}")
        # Em produção, você registraria este erro no DB ou sistema de logging (Ponto 8).


# ----------------------------------------------------------------------
# ROTAS DE GERENCIAMENTO (Inalteradas, exceto por Auth/Segurança implícita)
# ----------------------------------------------------------------------

@router.post("/bots/", response_model=Bot, status_code=status.HTTP_201_CREATED)
async def create_bot(bot_in: BotIn):
    bot_data = bot_in.model_dump()
    new_bot = Bot(**bot_data)
    MOCK_BOTS_DB[new_bot.id] = new_bot.model_dump()
    return new_bot

@router.get("/bots/", response_model=List[Bot])
async def read_bots():
    return list(MOCK_BOTS_DB.values())

@router.get("/bots/{bot_id}", response_model=Bot)
async def read_bot(bot_id: str):
    if bot_id not in MOCK_BOTS_DB:
        raise HTTPException(status_code=404, detail="Bot not found")
    return MOCK_BOTS_DB[bot_id]

@router.put("/bots/import", response_model=Dict[str, Any])
async def import_bots(bot_list_file: BotListFile):
    imported_count = 0
    for bot_data in bot_list_file.bots:
        MOCK_BOTS_DB[bot_data.id] = bot_data.model_dump()
        imported_count += 1
    return {"success": True, "imported_count": imported_count, "message": f"{imported_count} bots imported successfully."}

@router.get("/health")
async def health():
    """Rota de Health Check robusta (Ponto 13 da Athena)."""
    # Simula checagem de status de serviços críticos
    # Em produção, checaria DB, cache e a própria API da IA (ping).
    ai_status = "ok" if GEMINI_API_KEY else "warning (chave não definida)"
    return {"status": "ok", "services": {"database": "ok (mock)", "gemini_api": ai_status}}


# ----------------------------------------------------------------------
# ROTA DE CHAT ASSÍNCRONA (Ponto 5 da Athena)
# ----------------------------------------------------------------------

@router.post("/groups/send_message", status_code=status.HTTP_202_ACCEPTED, response_model=Dict[str, str])
async def send_group_message(request: BotChatRequest, background_tasks: BackgroundTasks):
    """
    Inicia o processamento da IA em segundo plano e retorna o ID da tarefa imediatamente.
    (Endereça o risco de bloqueio da requisição - Ponto 5 da Athena)
    """
    bot_id = request.bot_id
    if bot_id not in MOCK_BOTS_DB:
        raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found.")

    task_id = str(uuid.uuid4())
    
    # Adiciona a tarefa de processamento (chamada LLM) ao pool de background
    # Passamos o dicionário da requisição, pois objetos Pydantic podem ser
    # complexos para serialização em BackgroundTasks.
    background_tasks.add_task(_process_group_message, bot_id, request.model_dump(), task_id)
    
    # Retorna imediatamente (202 Accepted)
    return {
        "task_id": task_id,
        "status": "Processamento de IA enfileirado em Background.",
        "message": "Sua solicitação está sendo processada. Você precisará de um mecanismo de polling ou WebSocket para receber a resposta."
    }
