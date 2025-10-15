import streamlit as st
import requests
import json
import uuid
import time

# --- CONFIGURAÇÃO ---
BACKEND_URL = "https://cringe-8h21.onrender.com"
# Se estiver usando URL local: BACKEND_URL = "http://127.0.0.1:8080"

st.set_page_config(
    page_title="CRINGE RPG-AI: V2.1 - Criador de Bots",
    layout="wide"
)

st.title("🤖 CRINGE RPG-AI: V2.1 - Criador de Agentes")
st.markdown("Use este formulário para criar um novo agente (Mestre ou NPC) com personalidade e contexto ricos. Os bots criados são salvos permanentemente no banco de dados SQLite.")
st.markdown("---")

# Função para enviar a requisição de criação
def create_bot(payload):
    try:
        response = requests.post(f"{BACKEND_URL}/bots/create", json=payload, timeout=15)
        response.raise_for_status()
        
        st.success(f"🤖 Bot '{payload['name']}' criado com sucesso e salvo no SQLite!")
        st.balloons()
        
        # Limpa o formulário após o sucesso
        st.session_state.clear()
        st.rerun()

    except requests.exceptions.HTTPError as e:
        # Tenta extrair a mensagem de erro do JSON
        try:
            error_detail = response.json().get('detail', str(e))
        except:
            error_detail = str(e)
            
        st.error(f"Erro HTTP ao criar o bot. Detalhes: {error_detail}")
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de Conexão: Não foi possível se conectar ao Backend em {BACKEND_URL}. ({e})")

# --------------------------
# --- FORMULÁRIO STREAMLIT ---
# --------------------------

with st.form("bot_creation_form"):
    
    # 1. Informações Básicas
    col1, col2 = st.columns([1, 1])
    
    with col1:
        bot_name = st.text_input("Nome do Agente", placeholder="Ex: Grog, o Bárbaro", max_chars=50)
        
    with col2:
        bot_gender = st.selectbox(
            "Gênero",
            options=['Masculino', 'Feminino', 'Não Binário', 'Indefinido']
        )
        
    # 2. Introdução e Boas-Vindas
    st.subheader("📚 Detalhes da Persona")
    bot_intro = st.text_area(
        "Introdução / Breve Descrição",
        placeholder="Um Bárbaro de dois metros de altura, irritadiço e com um senso de humor duvidoso. Não gosta de elfos.",
        help="Esta é uma descrição curta usada para introduzir o bot em um cenário.",
        height=70
    )
    
    bot_welcome = st.text_input(
        "Mensagem de Boas-Vindas (Opcional)",
        placeholder="Por que vocês estão me incomodando? Falem logo!",
        help="A primeira frase que o bot dirá quando for acionado ou no início de um chat.",
        max_chars=200
    )
    
    # 3. Personalidade (System Prompt Core)
    st.subheader("🧠 Núcleo de Personalidade (Obrigatório)")
    bot_personality = st.text_area(
        "Personalidade Detalhada (System Prompt)",
        placeholder="Você é um Mestre de Masmorra que valoriza a ação e a brutalidade. Seu tom é cínico e sarcástico, e você só narra eventos violentos.",
        help="As regras e a descrição de personalidade que o modelo Gemini deve seguir em todas as interações. **Seja o mais específico possível.**",
        height=150
    )

    # 4. Contexto de Conversação (Few-Shot/Grounding)
    st.subheader("📜 Exemplos de Conversa (Melhora a Performance)")
    bot_context = st.text_area(
        "Exemplos, Links ou Contexto de Lore",
        placeholder="Ex: 'Usuário: Eu ataco o dragão. Agente: Você erra miseravelmente, seu tolo!' Inclua trechos de diálogo ou links para contexto de lore.",
        help="Qualquer texto que ajude a moldar o **ESTILO** de resposta do bot. Isso é usado para Few-Shot Learning. O conteúdo não será repetido.",
        height=200
    )
    
    # 5. Configurações da IA
    st.subheader("⚙️ Configurações da IA")
    col3, col4 = st.columns([1, 1])
    
    with col3:
        bot_temperature = st.slider(
            "Temperatura (Criatividade)",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            help="Maior valor = mais criatividade e aleatoriedade."
        )
    
    with col4:
        bot_max_tokens = st.number_input(
            "Máximo de Tokens de Saída",
            min_value=128,
            max_value=4096,
            value=1024,
            step=128,
            help="Controla o tamanho máximo da resposta da IA."
        )
    
    submitted = st.form_submit_button("Criar e Salvar Agente de IA")

if submitted:
    if not bot_name or not bot_personality:
        st.error("Por favor, preencha o Nome do Agente e o Núcleo de Personalidade. Eles são obrigatórios.")
    else:
        # Cria um ID único (usando nome e timestamp para evitar colisão)
        bot_id = f"bot-{bot_name.lower().replace(' ', '-').replace('.', '')}-{int(time.time() % 1000)}"
        
        payload = {
            "bot_id": bot_id,
            "creator_id": "user-1", # Marcamos como criado pelo usuário
            "name": bot_name,
            "gender": bot_gender,
            "introduction": bot_intro,
            "personality": bot_personality,
            "welcome_message": bot_welcome,
            "conversation_context": bot_context,
            "system_prompt": "", # O backend constrói o prompt final
            "ai_config": {
                "temperature": bot_temperature,
                "max_output_tokens": bot_max_tokens
            }
        }
        
        create_bot(payload)