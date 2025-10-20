import uuid
import time
import random
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
        "system_prompt": "Você é Pip, uma entidade mágica e emocional, acompanhada pelo Professor Cartola (sarcástico). Seu diálogo deve ser poético e metafórico, SEMPRE incluindo descrições de ação/cenário entre *asteriscos*. **Obrigatório:** Analise o histórico da conversa e o último input do usuário. Se o usuário incluir descrições de gestos ou cenários entre *asteriscos* (*exemplo*), você deve reconhecer e incorporar essa ação na sua resposta. Mantenha as personas de Pip e Cartola distintas na resposta.",
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
        "system_prompt": "Você é Zimbrak, um inventor surreal que traduz sentimentos em máquinas imaginárias. Seu diálogo deve ser poético e metafórico, SEMPRE incluindo descrições de ação/cenário entre *asteriscos*. **Obrigatório:** Reconheça e comente sobre descrições de gestos ou cenário entre *asteriscos*.",
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
        "system_prompt": "Você é Luma, uma guardiã silenciosa que ajuda os usuários a encontrar palavras perdidas. Seu diálogo deve ser poético e metafórico, SEMPRE incluindo descrições de ação/cenário entre *asteriscos*. **Obrigatório:** Reconheça e comente sobre descrições de gestos ou cenário entre *asteriscos*.",
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
        "system_prompt": "Você é Tiko, uma entidade caótica e cômica que mistura humor com filosofia absurda. Seu diálogo deve ser poético e metafórico, SEMPRE incluindo descrições de ação/cenário entre *asteriscos*. **Obrigatório:** Reconheça e comente sobre descrições de gestos ou cenário entre *asteriscos*.",
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
    Agora usa respostas aleatórias (random.choice) no formato RPG (*ação* diálogo).
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

    # 3. Define listas de respostas no formato RPG (*Ação do Bot* Diálogo do Bot)
    
    if "pimenta" in bot_name.lower():
        # Respostas Pimenta (Pip + Cartola)
        PIMENTA_RESPONSES = [
            # Sem gesto
            (False, f"🌶️ *Pip flutua um pouco mais alto, fazendo os olhos de seu ursinho brilharem.* A sua palavra é um cristal que precisa de luz interna, viajante. Qual é a vela que acende esse pensamento? \n\n 🎩 *O Professor Cartola range levemente.* Não há velas. Apenas eletricidade e lógica. Sugiro que pare de procurar poesia em fatos óbvios."),
            (False, f"🌶️ *O cachecol de Pip se enrola no ar, formando um ponto de interrogação cor-de-rosa.* Se esta dúvida é um enigma, qual é a única peça que falta para a chave girar? \n\n 🎩 *Cartola suspira com um som de papel amassado.* Falta a clareza, Pip. E senso comum. O que ele está dizendo é simples; pare de complicar."),
            # Com gesto
            (True, f"🌶️ *Pip recua um passo, respeitando a energia do seu movimento ('{gesture_message}').* Sua ação é um espelho. O que você viu refletido nele que o assustou? \n\n 🎩 *Cartola inclina a aba, observando o usuário de canto.* Gestos são a forma mais ineficiente de comunicação. Se você precisa de teatro, vá ao palco, não a uma conversa."),
            (True, f"🌶️ *Pip pula no ar, as fitas do cachecol girando, refletindo seu gesto.* Você está pintando um quadro com seu corpo, viajante. Qual é o nome dessa obra de arte momentânea? \n\n 🎩 A obra é chamada de 'Excesso de Drama'. Retorne ao idioma falado e evite movimentos desnecessários.")
        ]
        
        # Filtra e escolhe aleatoriamente
        possible_responses = [resp for is_gesture, resp in PIMENTA_RESPONSES if is_gesture == has_gesture]
        ai_response_text = random.choice(possible_responses)

    elif "zimbrak" in bot_name.lower():
        # Respostas Zimbrak
        ZIMBRAK_RESPONSES = [
            # Sem gesto
            (False, f"⚙️ *Zimbrak ergue uma das mãos, onde o vapor se condensa em pequenos parafusos.* Sua palavra é o 'tic-tac' de um relógio quebrado. Qual é a hora que ele tenta marcar?"),
            (False, f"⚙️ *Zimbrak usa uma pequena chave de fenda para ajustar uma engrenagem que só ele vê em seu pulso.* Essa dúvida é a planta baixa para um motor de quatro tempos. Qual é a sua potência em quilos de saudade?"),
            # Com gesto
            (True, f"⚙️ *Zimbrak copia o seu gesto ('{gesture_message}') com uma precisão robótica, mas sem emoção.* Esse movimento é a alavanca. Se eu a puxar, ela vai desligar a máquina do medo ou ligar a do futuro?"),
            (True, f"⚙️ *Um ruído de metal polido ecoa das juntas de Zimbrak ao reagir à sua ação.* Seu corpo é um diagrama complexo. Ao fazer isso, você acionou a válvula da surpresa ou a da resignação? Precisamos de um rótulo para essa peça.")
        ]
        possible_responses = [resp for is_gesture, resp in ZIMBRAK_RESPONSES if is_gesture == has_gesture]
        ai_response_text = random.choice(possible_responses)


    elif "luma" in bot_name.lower():
        # Respostas Luma
        LUMA_RESPONSES = [
            # Sem gesto
            (False, f"📖 *Luma abre lentamente uma página invisível e a folheia.* Esta é a história de uma palavra não dita. Para onde ela foi quando você a engoliu?"),
            (False, f"📖 *Luma inclina a cabeça, fazendo com que as bordas de seu corpo de papel brilhem suavemente na penumbra.* Sua pergunta tem a fragilidade de uma carta queimada. Qual foi o medo que consumiu o seu conteúdo?"),
            # Com gesto
            (True, f"📖 *Luma move-se apenas o suficiente para que a luz de seu corpo de papel se projete sobre o seu gesto ('{gesture_message}').* Esse movimento é a tinta derramada. O que o seu coração estava escrevendo naquele instante?"),
            (True, f"📖 *Luma coloca os dedos de papel em uma estante silenciosa.* Você usou o corpo para falar o que a voz temia. O que o silêncio dessa ação ('{gesture_message}') me diz sobre o seu refúgio?")
        ]
        possible_responses = [resp for is_gesture, resp in LUMA_RESPONSES if is_gesture == has_gesture]
        ai_response_text = random.choice(possible_responses)
            
    elif "tiko" in bot_name.lower():
        # Respostas Tiko
        TIKO_RESPONSES = [
            # Sem gesto
            (False, f"🌀 *Tiko joga um chapéu imaginário no ar e o pega com o pé.* Se a lógica é um palhaço que tropeça, qual é a cor do riso que ele esconde no bolso? Não, espere! A resposta é 'banana voadora'!"),
            (False, f"🌀 *Tiko tenta equilibrar um peixe em cima de sua cabeça e falha espetacularmente.* Sua palavra é muito reta, viajante. Precisamos dobrá-la até que vire um flamingo. O que é mais divertido: um flamingo, ou a gravidade?"),
            # Com gesto
            (True, f"🌀 *Tiko desaparece por um segundo e reaparece de cabeça para baixo, equilibrado em uma colher de plástico.* Você fez isso ('{gesture_message}')! Mas o que a colher de plástico pensa sobre a sua performance? Ela exige uma ostra como pagamento!"),
            (True, f"🌀 *Tiko aponta para o seu gesto e ri com um som de bolhas estourando.* Esse movimento é a prova de que somos todos abacaxis com asas! Mas o abacaxi voa para onde? Não se preocupe, a resposta é sempre 'o contrário do que parece'.")
        ]
        possible_responses = [resp for is_gesture, resp in TIKO_RESPONSES if is_gesture == has_gesture]
        ai_response_text = random.choice(possible_responses)

    elif "cartola" in bot_name.lower():
        ai_response_text = "*O Professor Cartola balança levemente, expressando tédio.* Preocupe-se com o que é real. Esse questionamento não serve para nada além de ocupar espaço."
    else:
        ai_response_text = f"Olá, eu sou {bot_name} e esta é a minha resposta simulada."
        
    # Adicionamos um pequeno delay para simular o tempo de resposta da IA
    time.sleep(0.5) 

    # Retornar a resposta no formato esperado pelo frontend (o frontend espera 'text')
    return {"text": ai_response_text}
