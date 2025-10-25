import streamlit as st
import requests
import json
import uuid
from typing import List, Dict, Optional

# Configuração da página
st.set_page_config(
    page_title="CRINGE - Personagens Interativos",
    page_icon="🤖",
    layout="wide"
)

# Configurações da API
API_URL = "https://cringe-5jmi.onrender.com"

# Inicialização do session_state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"
if 'current_bot' not in st.session_state:
    st.session_state.current_bot = None
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'message_counter' not in st.session_state:
    st.session_state.message_counter = 0

# Funções da API
def load_bots_from_db() -> List[Dict]:
    """Carrega bots do banco de dados"""
    try:
        response = requests.get(f"{API_URL}/bots")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro ao carregar bots: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return []

def chat_with_bot(bot_id: str, message: str, conversation_id: Optional[str] = None):
    """Envia mensagem para um bot"""
    try:
        payload = {
            "message": message,
            "conversation_id": conversation_id
        }
        
        print(f"🔍 FRONTEND: Enviando mensagem para {bot_id}")
        response = requests.post(f"{API_URL}/bots/chat/{bot_id}", json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro no servidor: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None

# Componentes da UI
def show_chat_interface():
    """Interface de chat simplificada"""
    if not st.session_state.current_bot:
        st.error("❌ Nenhum bot selecionado")
        if st.button("🏠 Voltar para Início", key="back_from_no_bot"):
            st.session_state.current_page = "home"
            st.rerun()
        return
    
    bot = st.session_state.current_bot
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"💬 {bot['name']}")
    with col2:
        if st.button("🏠 Início", key="back_home_chat"):
            st.session_state.current_page = "home"
            st.rerun()
    
    st.markdown(f"*{bot['introduction']}*")
    st.markdown("---")
    
    # Inicializar conversa
    if bot['id'] not in st.session_state.conversations:
        st.session_state.conversations[bot['id']] = {
            'conversation_id': None,
            'messages': []
        }
    
    current_conversation = st.session_state.conversations[bot['id']]
    
    # Exibir mensagem de boas-vindas se não houver mensagens
    if not current_conversation['messages']:
        with st.chat_message("assistant"):
            st.write(bot['welcome_message'])
        current_conversation['messages'].append({
            'content': bot['welcome_message'],
            'is_user': False
        })
    
    # Exibir histórico
    for msg in current_conversation['messages']:
        if msg['is_user']:
            with st.chat_message("user"):
                st.write(msg['content'])
        else:
            with st.chat_message("assistant"):
                st.write(msg['content'])
    
    # Input de mensagem
    user_message = st.chat_input("Digite sua mensagem...")
    
    if user_message and user_message.strip():
        # Adicionar mensagem do usuário
        current_conversation['messages'].append({
            'content': user_message,
            'is_user': True
        })
        
        # Obter resposta
        with st.spinner(f"{bot['name']} está pensando..."):
            response = chat_with_bot(
                bot['id'], 
                user_message, 
                current_conversation['conversation_id']
            )
            
            if response:
                current_conversation['conversation_id'] = response['conversation_id']
                current_conversation['messages'].append({
                    'content': response['response'],
                    'is_user': False
                })
                st.rerun()
            else:
                st.error("❌ Não foi possível obter resposta")

def show_bots_list():
    """Lista de bots simplificada"""
    st.title("🤖 Personagens Disponíveis")
    
    bots = load_bots_from_db()
    
    if not bots:
        st.info("Nenhum personagem encontrado. Verifique se o backend está rodando.")
        return
    
    for i, bot in enumerate(bots):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.subheader(bot['name'])
            st.write(f"*{bot['introduction']}*")
            st.caption(f"Personalidade: {bot['personality']}")
        
        with col2:
            if st.button("💬 Conversar", key=f"chat_{i}"):
                st.session_state.current_bot = bot
                st.session_state.current_page = "chat"
                st.rerun()
        
        st.markdown("---")

def show_home_page():
    """Página inicial simplificada"""
    st.title("🎭 CRINGE - Personagens Interativos")
    st.markdown("---")
    
    bots = load_bots_from_db()
    
    # Estatísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Personagens", len(bots))
    with col2:
        st.metric("Status Backend", "✅ Online" if bots else "❌ Offline")
    with col3:
        active_convos = len([c for c in st.session_state.conversations.values() if c['messages']])
        st.metric("Conversas Ativas", active_convos)
    
    st.markdown("---")
    
    # Botões principais
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Ver Personagens", key="view_bots_btn"):
            st.session_state.current_page = "bots"
            st.rerun()
    
    # Personagens em destaque
    if bots:
        st.subheader("🚀 Personagens em Destaque")
        cols = st.columns(min(3, len(bots)))
        
        for idx, bot in enumerate(bots[:3]):
            with cols[idx]:
                st.image(bot['avatar_url'], use_column_width=True)
                st.subheader(bot['name'])
                st.write(bot['introduction'][:100] + "...")
                if st.button(f"Conversar com {bot['name']}", key=f"home_chat_{idx}"):
                    st.session_state.current_bot = bot
                    st.session_state.current_page = "chat"
                    st.rerun()

# Barra lateral
with st.sidebar:
    st.title("🎭 CRINGE")
    st.markdown("---")
    
    # Navegação simples
    if st.button("🏠 Início", key="nav_home"):
        st.session_state.current_page = "home"
        st.rerun()
    
    if st.button("🤖 Personagens", key="nav_bots"):
        st.session_state.current_page = "bots"
        st.rerun()
    
    st.markdown("---")
    
    # Status
    try:
        health = requests.get(f"{API_URL}/health", timeout=5)
        if health.status_code == 200:
            st.success("✅ Backend Online")
        else:
            st.error("❌ Backend Offline")
    except:
        st.error("❌ Backend Inacessível")
    
    if st.button("🗑️ Limpar Conversas", key="clear_chats"):
        st.session_state.conversations = {}
        st.success("Conversas limpas!")
        st.rerun()

# Roteamento
if st.session_state.current_page == "home":
    show_home_page()
elif st.session_state.current_page == "bots":
    show_bots_list()
elif st.session_state.current_page == "chat":
    show_chat_interface()

# Rodapé
st.markdown("---")
st.caption("CRINGE - Personagens Interativos | Desenvolvido com Streamlit & FastAPI")
