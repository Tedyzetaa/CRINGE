import streamlit as st
import requests
import time

# 🚨 API_URL deve apontar para o servidor FastAPI, geralmente na porta 8000
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="CRINGE RPG-AI", page_icon="🧙", layout="wide")

# 🔹 Estilo personalizado
st.markdown("""
    <style>
    .main { background-color: #1e1e2f; color: #f0f0f0; }
    .block-container { padding-top: 2rem; }
    .stTextInput > div > input { background-color: #2e2e3e; color: white; }
    .stButton > button { background-color: #6c63ff; color: white; border-radius: 5px; }
    .stSelectbox > div { background-color: #2e2e3e; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🧙 CRINGE RPG-AI")
st.subheader("Converse com seus bots em cenários épicos")

# --- FUNÇÕES DE CHAMADA À API ---

def api_post(endpoint, payload):
    """Função auxiliar para POST requests com tratamento de erro básico."""
    try:
        res = requests.post(f"{API_URL}/{endpoint}", json=payload)
        res.raise_for_status() # Lança HTTPError para status 4xx/5xx
        return res.json()
    except requests.exceptions.ConnectionError:
        st.sidebar.error("❌ Erro: API do FastAPI não está rodando. Inicie o uvicorn.")
        return None
    except requests.exceptions.HTTPError as e:
        st.sidebar.error(f"❌ Erro HTTP ao enviar para /{endpoint}: {e}")
        return None

def api_get(endpoint):
    """Função auxiliar para GET requests com tratamento de erro básico."""
    try:
        res = requests.get(f"{API_URL}/{endpoint}")
        res.raise_for_status()
        return res.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Erro de Conexão: O backend (FastAPI) deve estar rodando em http://127.0.0.1:8000.")
        return []
    except requests.exceptions.HTTPError:
        return []

# --- SIDEBAR: JOGADOR ---
st.sidebar.header("🎭 Jogador")
username = st.sidebar.text_input("Nome do jogador", value="Aventureiro")
user_id = f"user-{username.lower().replace(' ', '-')}"
is_admin = st.sidebar.checkbox("Sou administrador")

# Cria/Atualiza usuário (Agora usa a lógica "Find or Create" no backend)
if username:
    api_post("users", {
        "name": username
    })

# --- SIDEBAR: CRIAÇÃO DE BOT ---
st.sidebar.header("🤖 Criar Bot")
with st.sidebar.expander("Novo Bot"):
    bot_name = st.text_input("Nome do Bot")
    bot_personality = st.text_area("Personalidade")
    bot_intro = st.text_area("Introdução")
    if st.button("Criar Bot"):
        bot_payload = {
            "creator_id": user_id,
            "name": bot_name,
            "gender": "Indefinido",
            "introduction": bot_intro,
            "personality": bot_personality,
            "welcome_message": "Saudações, aventureiro!",
            "conversation_context": "",
            "context_images": [],
            "system_prompt": f"Você é {bot_name}, um bot com personalidade: {bot_personality}",
            "ai_config": {"temperature": 0.7, "max_output_tokens": 512}
        }
        if api_post("bots", bot_payload):
            st.sidebar.success(f"Bot '{bot_name}' criado com sucesso!")
            # CORRIGIDO
            st.rerun() 

# --- SIDEBAR: CRIAÇÃO DE GRUPO ---
st.sidebar.header("🌍 Criar Grupo")
with st.sidebar.expander("Novo Grupo"):
    group_name = st.text_input("Nome do Grupo")
    group_scenario = st.text_area("Cenário")
    
    # 💡 BUSCA DE BOTS PARA O MULTISELECT
    all_bots = api_get("bots")
    bot_options = {b.get("name"): b.get("id") for b in all_bots if b.get("name")} 
    
    selected_bot_names = st.multiselect(
        "Bots no grupo", 
        list(bot_options.keys()),
        default=[]
    )
    
    # Mapeia nomes selecionados de volta para IDs
    selected_bot_ids = [bot_options[name] for name in selected_bot_names if name in bot_options]
    
    if st.button("Criar Grupo"):
        if not selected_bot_ids:
            st.sidebar.warning("Selecione pelo menos um bot para criar o grupo.")
        else:
            group_payload = {
                "name": group_name,
                "scenario": group_scenario,
                "bot_ids": selected_bot_ids 
            }
            if api_post("groups", group_payload):
                st.sidebar.success(f"Grupo '{group_name}' criado com sucesso!")
                # CORRIGIDO
                st.rerun() 

# --- SELEÇÃO DE GRUPO ---
st.subheader("🌍 Escolha o grupo")

all_groups = api_get("groups")

group_name_to_id = {g.get("name"): g.get("id") for g in all_groups if g.get("name")}
group_names = list(group_name_to_id.keys())

placeholder_text = "Nenhuma opção para selecionar. Crie um grupo na sidebar."
display_options = group_names if group_names else [placeholder_text]

group_choice = st.selectbox(
    "Selecione um grupo para continuar a conversa:",
    options=display_options,
    index=0 if group_names else None, 
    placeholder=placeholder_text
)

group_id = None
if group_choice and group_choice != placeholder_text:
    group_id = group_name_to_id.get(group_choice)

# --- CONVERSA ---
st.markdown("### 💬 Conversa")

if not group_id:
    st.info("Selecione ou crie um grupo para começar a conversar.")
else:
    # Busca o histórico de mensagens (Endpoint corrigido)
    msg_resp_data = api_get(f"groups/{group_id}/messages")
    
    if msg_resp_data and isinstance(msg_resp_data, list):
        for msg in msg_resp_data:
            sender_id = msg.get("sender_id", "unknown")
            text = msg.get('text', 'Mensagem vazia')

            # LÓGICA DE EXIBIÇÃO: Verifica se o ID começa com 'bot-'
            if sender_id.startswith("bot-"):
                # Tenta extrair o nome ou ID do bot
                # Nota: Em um sistema real, você buscaria o nome do bot pelo ID.
                sender_display = f"🤖 Bot (ID: {sender_id.split('-')[-1]})" 
                st.markdown(f"**{sender_display}**: {text}")
            else:
                # Caso contrário, assume que é o jogador
                sender_display = "🧑 Jogador" 
                st.markdown(f"**{sender_display}**: {text}")
    else:
           st.warning("Não há histórico de mensagens para este grupo.")

# --- ENVIAR NOVA MENSAGEM ---
st.markdown("---")
st.markdown("### ✉️ Enviar mensagem")

# Cria um form/container para garantir que o input e o botão sejam atualizados juntos
with st.form("message_form", clear_on_submit=True):
    text = st.text_input("Digite sua mensagem", key="message_input")
    submitted = st.form_submit_button("Enviar")

    if submitted:
        if not group_id:
            st.error("Selecione um grupo antes de enviar a mensagem.")
        elif text:
            message_payload = {
                "group_id": group_id,
                "sender_id": user_id,
                "text": text
            }
            if api_post("groups/send_message", message_payload):
                # Pequena pausa para garantir que o banco atualizou e recarrega
                time.sleep(0.1) 
                # CORRIGIDO
                st.rerun()