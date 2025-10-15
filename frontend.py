import streamlit as st
import requests
import json

# --- CONFIGURAÇÃO ---
# O endereço do seu backend CRINGE (FastAPI)
BACKEND_URL = "http://127.0.0.1:8080"
TEST_GROUP_ID = "group-123"
TEST_USER_ID = "user-1"

st.set_page_config(
    page_title="CRINGE RPG-AI: Interface de Teste",
    layout="wide"
)

# Título da Aplicação
st.title("🎲 CRINGE RPG-AI: Teste de Grupo")

# --- GERENCIAMENTO DE ESTADO ---
if 'messages' not in st.session_state:
    # 1. Tenta carregar o histórico inicial do Backend
    try:
        response = requests.get(f"{BACKEND_URL}/groups/{TEST_GROUP_ID}")
        response.raise_for_status() # Lança erro para 4xx/5xx
        group_data = response.json()
        
        # Converte a lista de mensagens do JSON para o estado
        st.session_state.messages = group_data.get('messages', [])
        st.session_state.error_loading = False
    except requests.exceptions.RequestException as e:
        st.session_state.messages = []
        st.session_state.error_loading = True
        st.error(f"Erro ao conectar com o Backend: Certifique-se de que o Uvicorn está rodando em {BACKEND_URL}. Detalhes: {e}")
    
# Se houve erro ao carregar, exibe e para
if st.session_state.error_loading:
    st.stop()


# --- FUNÇÃO PRINCIPAL ---

def send_message_to_backend(prompt: str):
    """Envia a mensagem do usuário para o endpoint da API e atualiza o histórico."""
    
    # 1. Adiciona a mensagem do usuário ao histórico local
    st.session_state.messages.append({
        "sender_id": TEST_USER_ID,
        "sender_type": "user",
        "text": prompt,
        "timestamp": 0 # Temporário
    })
    
    # 2. Constrói o corpo da requisição POST
    payload = {
        "group_id": TEST_GROUP_ID,
        "sender_id": TEST_USER_ID,
        "text": prompt
    }
    
    # 3. Envia para o Backend (FastAPI)
    try:
        response = requests.post(f"{BACKEND_URL}/groups/send_message", json=payload)
        response.raise_for_status()
        
        # 4. Processa a resposta do Backend
        api_data = response.json()
        
        # O backend retorna as respostas dos bots em 'ai_responses'
        ai_responses = api_data.get("ai_responses", [])
        
        # 5. Adiciona as respostas dos bots ao histórico
        for msg in ai_responses:
             st.session_state.messages.append(msg)
             
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao enviar mensagem para a API: {e}")
    except json.JSONDecodeError:
        st.error("Erro: O backend retornou uma resposta inválida (não-JSON).")


# --- INTERFACE DE CHAT ---

# 1. Exibir Histórico de Mensagens
st.subheader(f"Grupo ID: {TEST_GROUP_ID}")
chat_container = st.container(height=500, border=True)

for message in st.session_state.messages:
    sender_type = message['sender_type']
    
    # Define o ícone e a posição do chat
    if sender_type == 'user':
        avatar = "👤"
        is_user = True
        nome = "Você"
    else: # type == 'bot'
        avatar = "🤖"
        is_user = False
        nome = message['sender_id'] # Use o ID como nome temporário
        
        # Tenta pegar o nome do bot (melhor UX)
        try:
             # Isso é uma forma de buscar o nome do bot para a UI
             bot_info = requests.get(f"{BACKEND_URL}/groups/{TEST_GROUP_ID}").json()
             for member_id in bot_info.get('member_ids', []):
                 if member_id == message['sender_id']:
                      # Precisamos de uma rota GET para bots ou usuários no FastAPI
                      # Por simplicidade, usaremos o ID completo ou pegaremos o nome do bot-mestre/bardo
                      nome = message['sender_id'].replace("bot-", "").capitalize()
        except:
             pass # Falha silenciosa, usa o ID
        
        
    with chat_container:
        st.chat_message(name=sender_type, avatar=avatar).write(message['text'])


# 2. Entrada do Usuário
prompt = st.chat_input("Digite sua ação ou mensagem para o grupo...")

if prompt:
    # 3. Processar a mensagem
    send_message_to_backend(prompt)
    
    # 4. Forçar o re-render (necessário para atualizar a lista de mensagens)
    st.rerun()