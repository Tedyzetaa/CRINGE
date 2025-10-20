import streamlit as st
import requests
import time
import os
import json
from typing import List, Dict, Any, Optional

# --- CONFIGURAÇÃO ---
# URL da sua API FastAPI (deve ser ajustada se a API não estiver no mesmo servidor/porta)
API_URL = os.getenv("API_URL", "http://localhost:8000")

# --- Modelos de Dados ---
class ChatMessage:
    def __init__(self, role: str, text: str):
        self.role = role
        self.text = text

# --- Funções do Backend (Polling) ---

@st.cache_data
def get_bots() -> List[Dict[str, Any]]:
    """Busca a lista de bots da API (Cacheado para não sobrecarregar a API)."""
    try:
        response = requests.get(f"{API_URL}/bots/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar bots do backend. Certifique-se de que a API está rodando em {API_URL}.")
        st.error(f"Detalhes: {e}")
        return []

def send_message_and_poll(bot_id: str, messages: List[ChatMessage], user_message: str):
    """
    Envia a mensagem e inicia a lógica de Polling para buscar o resultado (Ponto 5 da Athena).
    """
    # Adiciona a mensagem do usuário ao histórico ANTES de enviar
    messages.append(ChatMessage(role="user", text=user_message))

    # Prepara o payload para a API
    payload = {
        "bot_id": bot_id,
        "messages": [{"role": msg.role, "text": msg.text} for msg in messages]
    }

    st.session_state.chat_history.append({"role": "user", "content": user_message})

    # 1. POST para iniciar a Background Task
    try:
        response = requests.post(f"{API_URL}/groups/send_message", json=payload)
        response.raise_for_status()
        
        task_data = response.json()
        task_id = task_data.get("task_id")
        
        st.info(f"Mensagem enviada. ID da Tarefa: {task_id}. Aguardando resposta da IA (Background Task)...")

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de comunicação com a API ao enviar mensagem: {e}")
        return

    # 2. Polling Loop
    max_polls = 20 # Limita o polling para evitar ciclo infinito (20 segundos max)
    poll_interval = 1 # segundos
    
    for i in range(max_polls):
        time.sleep(poll_interval)
        
        try:
            # Rota de Polling (GET /tasks/{task_id})
            status_response = requests.get(f"{API_URL}/tasks/{task_id}")
            status_response.raise_for_status()
            status_data = status_response.json()
            
            current_status = status_data.get('status')
            
            if current_status == 'complete':
                ai_response = status_data.get('result', "Não foi possível extrair a resposta.")
                
                # Adiciona a resposta da IA ao histórico de chat
                st.session_state.chat_history.append({"role": "ai", "content": ai_response})
                st.rerun() # Força a atualização do Streamlit para mostrar a nova mensagem
                return
            
            if current_status == 'error':
                error_message = status_data.get('result', 'Erro desconhecido na tarefa de background.')
                st.error(f"A tarefa da IA falhou: {error_message}")
                return

            # Atualiza o status de espera
            st.info(f"Status: {current_status}. Tentativa {i+1}/{max_polls}. Aguardando...")
            
        except requests.exceptions.RequestException as e:
            st.warning(f"Erro de comunicação durante o polling. Tentando novamente... Detalhe: {e}")
            
    st.error("Tempo limite de espera pela IA excedido. Tente novamente mais tarde.")

# --- UI PRINCIPAL ---

st.set_page_config(layout="wide", page_title="CRINGE - Chat Assíncrono com Bots (FastAPI + Streamlit)")

st.title("🌌 CRINGE: Chat Assíncrono com Bots (FastAPI + Streamlit)")
st.caption("Arquitetura Async implementada para atender ao Ponto 5 da Revisão da Athena.")

# Inicialização do estado
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'selected_bot_id' not in st.session_state:
    st.session_state.selected_bot_id = None
if 'bots_data' not in st.session_state:
    st.session_state.bots_data = get_bots()
    if st.session_state.bots_data:
        # Define o primeiro bot como padrão
        st.session_state.selected_bot_id = st.session_state.bots_data[0]['id']


# Sidebar para seleção de Bot
with st.sidebar:
    st.header("Selecione um Bot")
    
    bot_options = {bot['id']: bot['name'] for bot in st.session_state.bots_data}
    selected_bot_name = st.selectbox(
        "Bot:",
        options=list(bot_options.values()),
        index=0 if st.session_state.bots_data else None,
        key="bot_selector"
    )

    if selected_bot_name:
        for bot_id, name in bot_options.items():
            if name == selected_bot_name:
                # Atualiza o ID do bot selecionado no estado da sessão
                if st.session_state.selected_bot_id != bot_id:
                    st.session_state.selected_bot_id = bot_id
                    st.session_state.chat_history = [] # Limpa histórico ao trocar de bot
                break

    # Exibe informações do bot selecionado
    current_bot = next((bot for bot in st.session_state.bots_data if bot['id'] == st.session_state.selected_bot_id), None)
    if current_bot:
        st.image(current_bot['avatar_url'], width=100, caption=current_bot['name'])
        st.write(f"**Gênero:** {current_bot['gender']}")
        st.markdown(f"**Introdução:** *{current_bot['introduction']}*")
        st.markdown(f"**Prompt Inicial:** *{current_bot['welcome_message']}*")
        st.warning(f"ID do Bot (use no DB): {current_bot['id']}")


# Área de Chat Principal
if st.session_state.selected_bot_id:
    # Mostra o histórico de chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Captura a nova mensagem do usuário
    user_input = st.chat_input("Diga algo ao seu bot de IA...", key="chat_input")

    if user_input:
        
        # Converte o histórico de exibição (Dict) para o formato de mensagens da API (ChatMessage)
        api_messages = [
            ChatMessage(
                role="user" if msg["role"] == "user" else "model",
                text=msg["content"]
            )
            for msg in st.session_state.chat_history
        ]
        
        # Limpa a área de input (visual)
        st.session_state.chat_input = "" 
        
        # Chama a função principal de envio e polling
        send_message_and_poll(st.session_state.selected_bot_id, api_messages, user_input)

else:
    st.warning("Nenhum bot carregado. Verifique se sua API FastAPI está rodando e acessível em " + API_URL)
