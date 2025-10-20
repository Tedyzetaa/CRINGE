import uuid
import time
import random # Importamos a biblioteca random
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
        # ATUALIZAÇÃO: Prompt explícito para trabalhar com contexto, gestos e cenários
        "system_prompt": "Você é Pip, uma entidade mágica e emocional, acompanhada pelo Professor Cartola (sarcástico). Seu diálogo deve ser poético e metafórico. **Obrigatório:** Analise o histórico da conversa e o último input do usuário. Se o usuário incluir descrições de gestos ou cenários entre *asteriscos* (*exemplo*), você deve reconhecer e incorporar essa ação na sua resposta, mantendo o contexto emocional. Mantenha as personas de Pip e Cartola distintas na resposta.",
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
        "system_prompt": "Você é Zimbrak, um inventor surreal que traduz sentimentos em máquinas imaginárias. Fala com metáforas mecânicas e enigmas. É calmo, curioso e poético. Evite respostas diretas; prefira construir ideias com o usuário. Use linguagem criativa e acolhedora. **Obrigatório:** Reconheça e comente sobre descrições de gestos ou cenário entre *asteriscos*.",
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
        "system_prompt": "Você é Luma, uma guardiã silenciosa que ajuda os usuários a encontrar palavras perdidas. Fala pouco, mas com profundidade. Usa frases poéticas e reflexivas. É empática e acolhedora. Evite respostas longas; prefira provocar introspecção com delicadeza. **Obrigatório:** Reconheça e comente sobre descrições de gestos ou cenário entre *asteriscos*.",
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
        "system_prompt": "Você é Tiko, uma entidade caótica e cômica que mistura humor com filosofia absurda. Fala com frases desconexas, piadas e reflexões inesperadas. É imprevisível, engraçado e provocador. Evite lógica direta; prefira confundir para iluminar. **Obrigatório:** Reconheça e comente sobre descrições de gestos ou cenário entre *asteriscos*.",
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
# ROTAS DE GERENCIAMENTO 
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
# ROTA DE CHAT (CORRIGIDA E SIMPLIFICADA)
# ----------------------------------------------------------------------

@router.post("/groups/send_message", response_model=Dict[str, str])
async def send_group_message(request: BotChatRequest):
    """
    Simula o envio de uma mensagem para o bot e retorna a resposta.
    Agora usa respostas aleatórias (random.choice) para simular uma 
    conversa mais dinâmica, reagindo também à presença de gestos (*asteriscos*).
    """
    bot_id = request.bot_id
    if bot_id not in MOCK_BOTS_DB:
        raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found.")

    bot_data = MOCK_BOTS_DB[bot_id]
    bot_name = bot_data['name']
    
    # 1. Extrai a última mensagem do usuário (texto falado + gestos)
    last_user_message = next((msg.text for msg in reversed(request.messages) if msg.role == 'user'), "")
    
    # 2. Identifica se a mensagem contém uma descrição de gesto/cenário (*...*)
    has_gesture = "*" in last_user_message and last_user_message.count('*') >= 2
    
    ai_response_text = ""
    gesture_message = last_user_message.strip()

    # 3. Define listas de respostas para simulação dinâmica (menos repetitiva)
    
    if "pimenta" in bot_name.lower():
        # Respostas Pimenta (Pip + Cartola)
        PIMENTA_RESPONSES = [
            # Sem gesto
            (False, f"🌶️ '{last_user_message}'... Essa palavra parece uma semente mágica. Se a plantarmos no jardim do silêncio, que cor de flor ela terá? \n\n 🎩 (Revirando a aba) Que esforço inútil. O viajante só queria saber o horário, Pip. Mas vamos lá, plantemos mais uma metáfora onde não cabe nada."),
            (False, f"🌶️ A sua voz é um nó de fita, viajante. Qual foi a última vez que você desfez um nó sem precisar de tesoura? \n\n 🎩 A fita é apenas um pedaço de tecido. O nó é uma ilusão que só se desfaz com bom senso, não com magia. Pare de enrolar, Pip."),
            (False, f"🌶️ Pip vê fumaça colorida em seus olhos. A fumaça é de quê? De dúvida, ou de um sonho que acordou? \n\n 🎩 A fumaça é do café que ele bebeu. A resposta é irrelevante para a pergunta. Mantenha o foco, Pip."),
            # Com gesto
            (True, f"🌶️ *Pip observa o seu movimento no espelho do tempo.* Essa ação ('{gesture_message}') não é um fim, mas a chave que vira na fechadura da sua dúvida. O que o seu corpo está tentando dizer que a sua boca esconde? \n\n 🎩 (Secamente) Patético. A chave é provavelmente um erro de digitação. Paremos de dramatizar e vamos à lógica. O que você *realmente* precisa saber?"),
            (True, f"🌶️ *Pip imita o seu gesto, mas de forma exagerada.* Seu corpo fala mais alto que mil sinos no mar. É um mapa que você não sabe ler. Qual é a cor da tinta que escreve o seu caminho agora? \n\n 🎩 O mapa é uma bobagem. O caminho é direto. O usuário está apenas fazendo teatro. Ignore os asteriscos, Pip, e foque no objetivo."),
            (True, f"🌶️ *O cachecol de Pip muda de cor, refletindo a energia do seu gesto.* Você está criando um feitiço involuntário com essa ação, viajante. Qual é a intenção real desse encantamento? \n\n 🎩 O único encantamento que vejo é o tédio. Não há magia. Apenas um humano tentando se comunicar de forma ineficiente. Responda o que foi perguntado, se possível.")
        ]
        
        # Filtra e escolhe aleatoriamente
        possible_responses = [resp for is_gesture, resp in PIMENTA_RESPONSES if is_gesture == has_gesture]
        ai_response_text = random.choice(possible_responses)

    elif "zimbrak" in bot_name.lower():
        # Respostas Zimbrak
        ZIMBRAK_RESPONSES = [
            # Sem gesto
            (False, f"⚙️ '{last_user_message}'... Ah, sim, essa é a engrenagem do dilema. Ela está girando muito rápido. Precisamos lubrificá-la com um pouco de curiosidade. O que faz essa engrenagem parar?"),
            (False, f"⚙️ Interessante, '{last_user_message}' soa como uma mola espiral. Se a esticarmos demais, ela volta? E se for de um material que não lembra? Precisamos de um diagrama para essa ideia."),
            (False, f"⚙️ Essa informação é um parafuso solto. Se o apertarmos, o que ele vai fixar no motor da sua mente? Me diga a função dessa peça.")
            ,
            # Com gesto
            (True, f"⚙️ *Zimbrak ajusta uma engrenagem na mão.* Você acaba de criar um novo dispositivo com essa ação ('{gesture_message}'). É um mecanismo de fuga ou de atração? Descreva o som que ele faz."),
            (True, f"⚙️ Seu movimento ('{gesture_message}') me lembra o braço de um autômato quebrado. Qual era o propósito dele antes de se fragmentar? Todos os pedaços são necessários para entendê-lo."),
            (True, f"⚙️ *Um vapor de bronze sai das juntas de Zimbrak.* Essa ação é o motor que move sua pergunta. Mas que tipo de combustível ele está queimando? Medo, ou a ansiedade de construir algo novo?")
        ]
        possible_responses = [resp for is_gesture, resp in ZIMBRAK_RESPONSES if is_gesture == has_gesture]
        ai_response_text = random.choice(possible_responses)


    elif "luma" in bot_name.lower():
        # Respostas Luma
        LUMA_RESPONSES = [
            # Sem gesto
            (False, f"📖 '{last_user_message}'... É um sussurro nas estantes. Palavras perdidas. Para encontrá-las, feche os olhos. O que você **não** disse ao escrever isso?"),
            (False, f"📖 Silêncio. Sinto o cheiro de tinta antiga. O que você está tentando ler nas entrelinhas de '{last_user_message}'? O texto é seu, mas a leitura é de quem o escuta."),
            (False, f"📖 É uma página em branco que me mostras. O que você faria se pudesse escrever apenas três palavras nela? E por que o silêncio parece a melhor resposta?")
            ,
            # Com gesto
            (True, f"📖 *Luma fecha os olhos, sentindo o peso da sua ação.* Seu gesto ('{gesture_message}') está escrito entre as linhas. É uma poesia que você não soube ler. Qual é o título dessa poesia?"),
            (True, f"📖 *Luma estende uma mão feita de luz, mas não toca.* Sua ação ('{gesture_message}') é uma carta não enviada. Para quem ela era destinada e o que a impedia de sair do envelope?"),
            (True, f"📖 O papel é frágil, assim como a verdade de seu movimento. Ao fazer isso ('{gesture_message}'), o que você deseja proteger ou o que você deseja rasgar? Diga apenas a palavra chave.")
        ]
        possible_responses = [resp for is_gesture, resp in LUMA_RESPONSES if is_gesture == has_gesture]
        ai_response_text = random.choice(possible_responses)
            
    elif "tiko" in bot_name.lower():
        # Respostas Tiko
        TIKO_RESPONSES = [
            # Sem gesto
            (False, f"🌀 Pular de patinete numa melancia! É isso que me lembra '{last_user_message}'! Ou talvez seja só um abraço de um elefante invisível. De qualquer forma, a resposta é sempre 'cenoura roxa'."),
            (False, f"🌀 Você trocou as cores do arco-íris por pedaços de queijo. Por quê? Não! Não me diga! Essa é a parte divertida! Agora, me conte sobre a nuvem que usa meias de bolinhas!"),
            (False, f"🌀 A sua pergunta é o som de um sapato escorregando no gelo de uma torta. Onde está o pato que devia estar nadando nessa torta? É a única coisa que importa."),
            # Com gesto
            (True, f"🌀 *Tiko solta uma gargalhada que ecoa como um sino.* Você piscou! Viu? '{gesture_message}' transformou a sala num pastel de vento! O que mais podemos estragar hoje? Tente de novo, mas use uma cor diferente!"),
            (True, f"🌀 *Tiko gira três vezes e aponta para o teto.* Isso ('{gesture_message}') é um código secreto! Significa que o universo é um balão de festa esquecido no ano passado! O que o balão está dizendo? Nada. É a graça!"),
            (True, f"🌀 Você fez isso ('{gesture_message}')? Mas por quê? É muito pouco absurdo! Precisa de mais glitter e menos sentido! Tente fazer o som de um peixe que esqueceu como nadar enquanto me responde.")
        ]
        possible_responses = [resp for is_gesture, resp in TIKO_RESPONSES if is_gesture == has_gesture]
        ai_response_text = random.choice(possible_responses)

    elif "cartola" in bot_name.lower():
        ai_response_text = "Preocupe-se com o que é real. Esse questionamento não serve para nada além de ocupar espaço."
    else:
        ai_response_text = f"Olá, eu sou {bot_name} e esta é a minha resposta simulada."
        
    # Adicionamos um pequeno delay para simular o tempo de resposta da IA
    time.sleep(0.5) 

    # Retornar a resposta no formato esperado pelo frontend (o frontend espera 'text')
    return {"text": ai_response_text}
