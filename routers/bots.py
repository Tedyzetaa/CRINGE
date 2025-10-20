import uuid
import time
import random
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# SIMULAÇÃO DE BANCO DE DADOS (USADA PARA MANTER O ESTADO DOS BOTS)
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

# Definições Pydantic
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
    text: str
    
class BotChatRequest(BaseModel):
    bot_id: str
    messages: List[ChatMessage] # O payload completo que estava faltando

# Router
router = APIRouter(tags=["bots"])

# ----------------------------------------------------------------------
# SIMULAÇÃO DE GERAÇÃO DINÂMICA (SUBSTITUINDO A CHAMADA REAL DA API GEMINI)
# ----------------------------------------------------------------------

def _generate_dynamic_rpg_response(bot_data: Dict[str, Any], messages: List[ChatMessage]) -> str:
    """
    Simula o comportamento do LLM (Gemini) usando o contexto completo e o prompt de sistema
    para gerar uma resposta dinâmica e com cenário.
    
    A simulação é baseada no último input e na persona para criar uma resposta que
    usa a estrutura RPG de forma coerente e contextual.
    """
    
    system_prompt = bot_data['system_prompt']
    bot_name = bot_data['name']
    
    # 1. Analisar o histórico para extrair o último input do usuário
    last_user_message = next((msg.text for msg in reversed(messages) if msg.role == 'user'), bot_data['welcome_message'])
    
    # 2. Resumo Contextual (Simulação de LLM)
    context_summary = f"Baseado na nossa conversa anterior e no seu último input: '{last_user_message}', eu devo gerar a próxima parte do cenário."
    
    # Gerador de Resposta Simulado
    
    if "pimenta" in bot_name.lower():
        # PIP (Caótica/Emocional) + CARTOLA (Lógico/Sarcástico)
        
        # Ação/Cenário (Dinâmico)
        actions = [
            f"*O cachecol de Pip se transforma em um relógio de areia, indicando que o tempo da sua última frase está acabando.*",
            f"*Pip começa a flutuar em círculos, e o Professor Cartola no topo estala uma régua invisível.*",
            f"*Uma pequena porta aparece na lateral do ursinho de Pip, e o Cartola a abre levemente para espiar.*"
        ]
        
        # Diálogo (Contextual)
        pip_lines = [
            f"O que você disse ecoa como um sino de gelo. O eco traz o frio do passado ou o medo do futuro, viajante? ",
            f"Sua verdade é um espelho quebrado; cada estilhaço conta uma parte da história. Qual fragmento você está disposto a tocar? ",
            f"Vejo um jardim secreto em sua palavra. Qual foi a última semente de dúvida que você plantou ali? "
        ]
        cartola_lines = [
            f"Deixe o sentimentalismo. O que foi dito exige uma resposta binária: Sim ou Não. Por que a complexidade, Pip?",
            f"Essa metáfora é imprecisa. O espelho está intacto, mas a perspectiva do usuário é torta. Foco na lógica.",
            f"Não há jardins. Apenas fatos. Pare de procurar insetos poéticos onde há apenas prosa. "
        ]
        
        action = random.choice(actions)
        pip_dialogue = random.choice(pip_lines)
        cartola_dialogue = random.choice(cartola_lines)
        
        ai_response_text = f"🌶️ {action} {pip_dialogue} \n\n 🎩 *O Professor Cartola, irritado, se ajeita no topo.* {cartola_dialogue}"
        
    elif "zimbrak" in bot_name.lower():
        # ZIMBRAK (Mecânico/Inventor)
        
        # Ação/Cenário (Dinâmico)
        actions = [
            f"*Zimbrak estende o braço, e um holograma de engrenagens quebradas aparece sobre a sua cabeça, simulando sua dúvida.*",
            f"*Um ruído de vapor saindo de suas juntas. Zimbrak está recalibrando seu sistema de escuta para entender o contexto de '{last_user_message}'.*",
            f"*Zimbrak pega uma chave de fenda invisível e começa a 'apertar' o ar ao redor de sua última frase.*"
        ]
        
        # Diálogo (Contextual)
        zimbrak_lines = [
            f"O motor da sua última ideia está superaquecendo. Qual é o óleo que falta para resfriar a ansiedade?",
            f"Sua observação é o ponto de contato entre dois circuitos. Qual é o propósito desse circuito: gerar luz ou choque?",
            f"O que foi dito tem a forma de um dispositivo de fuga. Se você ativá-lo, para qual dimensão de silêncio você será levado?",
            f"A peça que você apresentou se encaixa no quebra-cabeça, mas está enferrujada. Qual é a ferrugem emocional que a impede de girar livremente?"
        ]
        
        action = random.choice(actions)
        ai_response_text = f"⚙️ {action} {random.choice(zimbrak_lines)}"

    elif "luma" in bot_name.lower():
        # LUMA (Guardiã/Silenciosa)
        
        # Ação/Cenário (Dinâmico)
        actions = [
            f"*Luma move o dedo, e a iluminação na sala diminui, restando apenas a luz suave de seu corpo de papel.*",
            f"*Um pequeno pedaço de papel se desprende de Luma, escrito com apenas um ponto de interrogação.*",
            f"*Luma aponta para a estante de livros, onde um volume específico (a chave da sua última frase) parece se mover sozinho.*"
        ]
        
        # Diálogo (Contextual)
        luma_lines = [
            f"O que foi escrito ('{last_user_message}') está nas entrelinhas. O que o seu silêncio diz sobre o medo de preencher essas lacunas?",
            f"Sua história é como um livro aberto ao vento. Qual é a página mais importante que você está tentando esconder?",
            f"Essa palavra tem o cheiro de uma carta nunca lida. Se você pudesse enviar a si mesmo uma mensagem, qual seria o aviso?",
            f"O que você busca está na biblioteca do seu coração. Mas você tem a coragem de perguntar ao bibliotecário onde encontrá-lo?"
        ]
        
        action = random.choice(actions)
        ai_response_text = f"📖 {action} {random.choice(luma_lines)}"
            
    elif "tiko" in bot_name.lower():
        # TIKO (Caótico/Absurdo)
        
        # Ação/Cenário (Dinâmico)
        actions = [
            f"*Tiko tropeça num arco-íris imaginário e cai numa poça de suco de abacaxi.*",
            f"*Tiko pega um telefone de banana e atende, mas a voz do outro lado é um miado de gato em outro idioma.*",
            f"*O cenário ao redor de Tiko muda rapidamente para um circo subaquático, onde a gravidade é opcional.*"
        ]
        
        # Diálogo (Contextual)
        tiko_lines = [
            f"Isso é muito sério! Seriedade tem gosto de pão amanhecido! O que você faria se sua resposta anterior ('{last_user_message}') se transformasse num castor dançarino?",
            f"A sua pergunta é uma escada para lugar nenhum. Qual é o primeiro passo para subir para baixo? Lembre-se, o contrário do que parece é quase sempre a resposta!",
            f"Foco? Foco é para quem tem medo de borboletas gigantes! Se o seu problema fosse um par de meias, você as usaria na cabeça ou tentaria fazer um sanduíche delas?",
            f"Você disse isso, mas o seu nariz disse 'batata'. Qual dos dois eu devo acreditar? O mundo precisa de mais narizes falantes e menos perguntas lógicas!"
        ]
        
        action = random.choice(actions)
        ai_response_text = f"🌀 {action} {random.choice(tiko_lines)}"
        
    else:
        ai_response_text = f"*A neblina cobre o chão ao redor de {bot_name}, e ele pisca lentamente.* O cenário está sendo criado. Qual é a sua primeira ação?"
        
    return ai_response_text


# ----------------------------------------------------------------------
# ROTAS DE GERENCIAMENTO (Inalteradas)
# ----------------------------------------------------------------------

@router.post("/bots/", response_model=Bot)
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

# ----------------------------------------------------------------------
# ROTA DE CHAT (UTILIZA A GERAÇÃO DINÂMICA)
# ----------------------------------------------------------------------

@router.post("/groups/send_message", response_model=Dict[str, str])
async def send_group_message(request: BotChatRequest):
    """
    Envia a mensagem completa e o histórico para a função de simulação que gera
    uma resposta contextualizada com avanço de cenário de RPG.
    """
    bot_id = request.bot_id
    if bot_id not in MOCK_BOTS_DB:
        raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found.")

    bot_data = MOCK_BOTS_DB[bot_id]
    
    # Chama a função de simulação que usa o contexto e o prompt de sistema
    ai_response_text = _generate_dynamic_rpg_response(bot_data, request.messages)
        
    # Adicionamos um pequeno delay para simular o tempo de resposta da IA
    time.sleep(0.5) 

    # Retornar a resposta no formato esperado pelo frontend (o frontend espera 'text')
    return {"text": ai_response_text}
