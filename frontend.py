# frontend.py (Streamlit App)

import streamlit as st
import requests
import json
from typing import List, Dict, Any

# --- Configuração ---
API_BASE_URL = st.secrets.get("API_BASE_URL", "https://cringe-8h21.onrender.com")
BOT_API_URL = f"{API_BASE_URL}/bots"
CHAT_API_URL_TEMPLATE = f"{API_BASE_URL}/bots/chat" # Corrigido para a rota no routers/bots

# --- Funções de API ---

@st.cache_data(ttl=3600)
def fetch_bots():
    """Busca a lista de bots da API."""
    try:
        response = requests.get(BOT_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao conectar ao backend (API: {API_BASE_URL}). Verifique se o backend está rodando: {e}")
        return []

def send_chat_message(bot_id: int, user_message: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Envia a mensagem do usuário e o histórico para a rota de chat do bot."""
    
    payload = {
        "user_message": user_message,
        "chat_history": chat_history 
    }
    
    # Rota correta: /bots/chat/{bot_id}
    chat_url = f"{CHAT_API_URL_TEMPLATE}/{bot_id}" 
    
    try:
        response = requests.post(chat_url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Erro na API do Chat ({e.response.status_code}): {e.response.text}")
        return {"error": True, "message": "Falha na comunicação com a API de AI."}
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro de conexão ao enviar mensagem: {e}")
        return {"error": True, "message": "Falha de rede ou backend indisponível."}


# --- Funções de Estado e UI ---

def reset_chat():
    """Reinicia o chat atual."""
    if st.session_state.get('selected_bot_id') is not None:
        bot_id = st.session_state.selected_bot_id
        st.session_state.messages[bot_id] = []
        st.rerun() # CORREÇÃO: st.rerun()
    else:
        st.warning("Nenhum bot selecionado para reiniciar.")


def initialize_session_state(bots: List[Dict[str, Any]]):
    """Inicializa as variáveis de estado da sessão."""
    if 'messages' not in st.session_state:
        st.session_state.messages = {bot['id']: [] for bot in bots}
    
    if 'selected_bot_id' not in st.session_state:
        st.session_state.selected_bot_id = bots[0]['id'] if bots else None

    if 'current_bot' not in st.session_state:
        st.session_state.current_bot = next((bot for bot in bots if bot['id'] == st.session_state.selected_bot_id), None)

def switch_bot():
    """Função chamada ao mudar o bot no selectbox."""
    new_bot_id = st.session_state.bot_selector
    st.session_state.selected_bot_id = new_bot_id
    bots = fetch_bots()
    st.session_state.current_bot = next((bot for bot in bots if bot['id'] == new_bot_id), None)
    st.rerun() # CORREÇÃO: st.rerun()

# --- Layout Principal ---

st.set_page_config(
    page_title="Cringe Bot RPG AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Cringe Bot RPG AI")

bots_list = fetch_bots()
initialize_session_state(bots_list)


# --- SIDEBAR (Seleção de Bot) ---

st.sidebar.title("Configurações do Bot")

if not bots_list:
    st.sidebar.error("Nenhum bot encontrado ou a API não está acessível.")
else:
    bot_options = {bot['name']: bot['id'] for bot in bots_list}
    current_name = st.session_state.current_bot['name'] if st.session_state.current_bot else list(bot_options.keys())[0]
    
    st.sidebar.selectbox(
        "Selecione seu Bot:",
        options=list(bot_options.keys()),
        index=list(bot_options.keys()).index(current_name),
        key="bot_selector_name",
        on_change=lambda: st.session_state.__setitem__('bot_selector', bot_options[st.session_state.bot_selector_name])
    )
    
    if 'bot_selector' in st.session_state and st.session_state.bot_selector != st.session_state.selected_bot_id:
        switch_bot()

    current_bot = st.session_state.current_bot
    
    if current_bot:
        st.sidebar.markdown(f"**Persona:** {current_bot['persona']}")
        st.sidebar.markdown(f"**Instruções de Estilo:** {current_bot['ai_config']['style']}")
        st.sidebar.markdown("---")
        
        st.sidebar.button("🗑️ Reiniciar Chat", on_click=reset_chat)

        st.sidebar.caption(f"Modelo: {current_bot['ai_config']['model_id']}")


# --- Área Principal (Chat) ---

if st.session_state.selected_bot_id is not None and current_bot:
    
    st.subheader(f"Conversando com: {current_bot['name']} ({current_bot['role']})")
    
    current_chat_history = st.session_state.messages[current_bot['id']]

    for message in current_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Diga algo ao seu bot..."):
        
        with st.chat_message("user"):
            st.markdown(prompt)
            # Salva o prompt na sessão ANTES de chamar a API
            current_chat_history.append({"role": "user", "content": prompt})

        with st.spinner(f"Aguardando a resposta de {current_bot['name']}..."):
            
            # Envia o histórico completo (incluindo o prompt atual)
            api_history = [{"role": msg["role"], "content": msg["content"]} for msg in current_chat_history]
            
            # O backend espera o histórico ANTES da última mensagem (o prompt).
            # Por isso, enviamos o histórico [:-1]
            response_data = send_chat_message(
                bot_id=current_bot['id'], 
                user_message=prompt, 
                chat_history=api_history[:-1] 
            )
            
            ai_response_content = response_data.get("ai_response")

        if not response_data.get("error"):
            with st.chat_message("assistant"):
                st.markdown(ai_response_content)
                current_chat_history.append({"role": "assistant", "content": ai_response_content})
        else:
             # Remove o prompt do histórico da UI se a API falhar.
             if current_chat_history[-1]["role"] == "user":
                 current_chat_history.pop()

else:
    st.info("Carregando bots ou falha na conexão. Verifique o status da API.")
