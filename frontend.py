import streamlit as st
import requests
import json
import time

# --- CONFIGURAÇÃO ---
# URL do seu backend CRINGE no Render.
BACKEND_URL = "https://cringe-8h21.onrender.com" 

TEST_GROUP_ID = "group-123"
TEST_USER_ID = "user-1"

st.set_page_config(
    page_title="CRINGE RPG-AI: Interface de Teste",
    layout="wide"
)

# Título da Aplicação
st.title("🎲 CRINGE RPG-AI: Teste de Grupo")

# --- GERENCIAMENTO DE ESTADO E INICIALIZAÇÃO ---

# Função para carregar dados do grupo e membros
def load_initial_data(url):
    """Carrega o histórico de mensagens e os nomes dos membros do backend."""
    try:
        # Aumenta o timeout para evitar erro na primeira conexão
        response = requests.get(f"{url}/groups/{TEST_GROUP_ID}", timeout=10) 
        response.raise_for_status()
        group_data = response.json()
        
        # Armazena os nomes dos membros (usuários e bots)
        member_names = {}
        for member_id in group_data.get('member_ids', []):
            if member_id.startswith("user-"):
                user_res = requests.get(f"{url}/users/{member_id}")
                member_names[member_id] = user_res.json().get('username', 'Usuário Desconhecido')
            elif member_id.startswith("bot-"):
                if member_id == "bot-mestre":
                    member_names[member_id] = "Mestre da Masmorra"
                elif member_id == "bot-npc-1":
                    member_names[member_id] = "Bardo Errante"
                else:
                    member_names[member_id] = member_id
                    
        st.session_state.member_names = member_names
        st.session_state.messages = group_data.get('messages', [])
        st.session_state.error_loading = False
    except requests.exceptions.RequestException as e:
        st.session_state.messages = []
        st.session_state.error_loading = True
        st.session_state.member_names = {}
        st.error(f"Erro ao conectar com o Backend: Certifique-se de que o backend está ativo em {url}. Detalhes: {e}")

# Garante que os dados sejam carregados apenas uma vez
if 'messages' not in st.session_state:
    load_initial_data(BACKEND_URL)
    
# Se houve erro ao carregar, exibe e para
if st.session_state.error_loading:
    st.stop()


# --- FUNÇÃO PRINCIPAL: ENVIO ---

def send_message_to_backend(prompt: str):
    """Envia a mensagem do usuário para o endpoint da API e atualiza o histórico."""
    
    # 1. Adiciona a mensagem do usuário ao histórico local
    st.session_state.messages.append({
        "sender_id": TEST_USER_ID,
        "sender_type": "user",
        "text": prompt,
        "timestamp": time.time()
    })
    
    # 2. Constrói o corpo da requisição POST
    payload = {
        "group_id": TEST_GROUP_ID,
        "sender_id": TEST_USER_ID,
        "text": prompt
    }
    
    # 3. Envia para o Backend (FastAPI)
    with st.spinner("🤖 Os Agentes de IA estão pensando..."):
        try:
            # 30 segundos de timeout para dar tempo para as chamadas de IA
            response = requests.post(f"{BACKEND_URL}/groups/send_message", json=payload, timeout=30) 
            response.raise_for_status()
            
            # 4. Processa a resposta do Backend
            api_data = response.json()
            
            # O backend retorna as respostas dos bots em 'ai_responses'
            ai_responses = api_data.get("ai_responses", [])
            
            # 5. Adiciona as respostas dos bots ao histórico
            for msg in ai_responses:
                 if msg['text'] and not msg['text'].startswith("Erro de IA:"):
                    st.session_state.messages.append(msg)
                 elif msg['text'].startswith("Erro de IA:"):
                    bot_name = st.session_state.member_names.get(msg['sender_id'], msg['sender_id'])
                    st.error(f"O agente {bot_name} falhou: {msg['text'].split('(Detalhe: ')[-1].replace(')', '')}")

            st.rerun() 
                 
        except requests.exceptions.Timeout:
            st.error("Erro de Timeout: O Backend demorou demais para responder. Tente novamente.")
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de Conexão com a API: {e}")
        except json.JSONDecodeError:
            st.error("Erro: O backend retornou uma resposta inválida (não-JSON).")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")


# --- INTERFACE DE CHAT ---

st.subheader(f"Grupo ID: {TEST_GROUP_ID}")
chat_container = st.container(height=500, border=True)

for message in st.session_state.messages:
    sender_id = message['sender_id']
    sender_type = message['sender_type']
    
    # Define o nome e avatar usando o dicionário carregado
    nome = st.session_state.member_names.get(sender_id, sender_id)
    
    if sender_type == 'user':
        avatar = "👤"
    elif sender_id == "bot-mestre":
        avatar = "👑"
    elif sender_id == "bot-npc-1":
        avatar = "🎶"
    else: # Outros bots
        avatar = "🤖"
        
    with chat_container:
        st.chat_message(name=nome, avatar=avatar).write(message['text'])


# 2. Entrada do Usuário
prompt = st.chat_input("Digite sua ação ou mensagem para o grupo...")

if prompt:
    # 3. Processar a mensagem
    send_message_to_backend(prompt)
    
# 4. Exibir o URL do Backend para referência
st.sidebar.markdown("---")
st.sidebar.caption(f"Backend CRINGE rodando em: **{BACKEND_URL}**")