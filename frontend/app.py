import streamlit as st
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import time

# Configuração da página
st.set_page_config(
    page_title="CRINGE - Personagens Interativos",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações da API
API_URL = "https://cringe-5jmi.onrender.com"  # Altere para sua URL

# Inicialização do session_state
def initialize_session_state():
    defaults = {
        'current_page': "home",
        'current_bot': None,
        'conversations': {},
        'selected_bot_id': None,
        'api_health': "checking",
        'last_update': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# Funções da API
@st.cache_data(ttl=60)
def load_bots_from_db() -> List[Dict]:
    try:
        response = requests.get(f"{API_URL}/bots", timeout=10)
        if response.status_code == 200:
            st.session_state.api_health = "healthy"
            return response.json()
        else:
            st.session_state.api_health = "unhealthy"
            st.error(f"Erro ao carregar bots: {response.status_code}")
            return []
    except Exception as e:
        st.session_state.api_health = "unreachable"
        st.error(f"Erro de conexão: {str(e)}")
        return []

def chat_with_bot(bot_id: str, message: str, conversation_id: Optional[str] = None):
    try:
        payload = {
            "message": message,
            "conversation_id": conversation_id
        }
        
        with st.spinner("💭 O personagem está pensando..."):
            response = requests.post(
                f"{API_URL}/bots/chat/{bot_id}", 
                json=payload, 
                timeout=30
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro no servidor: {response.status_code}")
            return None
    except requests.Timeout:
        st.error("⏰ Timeout - O servidor demorou muito para responder")
        return None
    except Exception as e:
        st.error(f"🔌 Erro de conexão: {str(e)}")
        return None

def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            st.session_state.api_health = "healthy"
            return response.json()
        else:
            st.session_state.api_health = "unhealthy"
            return None
    except:
        st.session_state.api_health = "unreachable"
        return None

# Componentes da UI
def create_bot_card(bot, column):
    with column:
        with st.container():
            st.image(
                bot['avatar_url'], 
                use_column_width=True,
                caption=f"🎭 {bot['name']}"
            )
            
            st.subheader(bot['name'])
            st.caption(f"⚧ {bot.get('gender', 'Não especificado')}")
            
            with st.expander("📖 Sobre este personagem"):
                st.write(bot['introduction'])
                st.write(f"**Personalidade:** {bot['personality']}")
                
                if bot.get('tags'):
                    tags = " ".join([f"`{tag}`" for tag in bot['tags']])
                    st.write(f"**Tags:** {tags}")
            
            if st.button(
                "💬 Conversar", 
                key=f"chat_{bot['id']}",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.current_bot = bot
                st.session_state.current_page = "chat"
                st.rerun()

def show_chat_interface():
    if not st.session_state.current_bot:
        st.error("❌ Nenhum personagem selecionado")
        if st.button("🏠 Voltar para Início", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
        return
    
    bot = st.session_state.current_bot
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title(f"💬 {bot['name']}")
        st.caption(f"*{bot['introduction']}*")
    with col2:
        if st.button("📋 Personagens", use_container_width=True):
            st.session_state.current_page = "bots"
            st.rerun()
    with col3:
        if st.button("🏠 Início", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    
    st.markdown("---")
    
    if bot['id'] not in st.session_state.conversations:
        st.session_state.conversations[bot['id']] = {
            'conversation_id': None,
            'messages': [],
            'started_at': datetime.now().isoformat()
        }
    
    current_conversation = st.session_state.conversations[bot['id']]
    
    chat_container = st.container(height=400, border=True)
    
    with chat_container:
        if not current_conversation['messages']:
            with st.chat_message("assistant", avatar=bot['avatar_url']):
                st.write(bot['welcome_message'])
                st.caption("✨ Mensagem de boas-vindas")
            current_conversation['messages'].append({
                'content': bot['welcome_message'],
                'is_user': False,
                'timestamp': datetime.now().isoformat()
            })
        
        for msg in current_conversation['messages']:
            avatar = None if msg['is_user'] else bot['avatar_url']
            with st.chat_message("user" if msg['is_user'] else "assistant", avatar=avatar):
                st.write(msg['content'])
                if 'timestamp' in msg:
                    try:
                        time_str = datetime.fromisoformat(msg['timestamp']).strftime("%H:%M")
                        st.caption(f"🕒 {time_str}")
                    except:
                        pass
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Limpar Chat", use_container_width=True):
            st.session_state.conversations[bot['id']] = {
                'conversation_id': None,
                'messages': [],
                'started_at': datetime.now().isoformat()
            }
            st.rerun()
    
    st.markdown("---")
    user_message = st.chat_input(
        f"Digite sua mensagem para {bot['name']}...",
        key=f"input_{bot['id']}"
    )
    
    if user_message and user_message.strip():
        if len(user_message) > 1000:
            st.warning("⚠️ Mensagem muito longa. Limite: 1000 caracteres.")
            return
        
        current_conversation['messages'].append({
            'content': user_message,
            'is_user': True,
            'timestamp': datetime.now().isoformat()
        })
        
        with chat_container:
            with st.chat_message("user"):
                st.write(user_message)
                st.caption(f"🕒 {datetime.now().strftime('%H:%M')}")
        
        response = chat_with_bot(
            bot['id'], 
            user_message, 
            current_conversation['conversation_id']
        )
        
        if response:
            current_conversation['conversation_id'] = response['conversation_id']
            current_conversation['messages'].append({
                'content': response['response'],
                'is_user': False,
                'timestamp': datetime.now().isoformat()
            })
            st.rerun()
        else:
            st.error("❌ Não foi possível obter resposta")

def show_bots_list():
    st.title("🤖 Personagens Disponíveis")
    st.markdown("---")
    
    bots = load_bots_from_db()
    
    if not bots:
        st.error("🚫 Nenhum personagem encontrado.")
        st.info("Verifique se o backend está rodando corretamente.")
        if st.button("🔄 Tentar Novamente"):
            st.cache_data.clear()
            st.rerun()
        return
    
    cols = st.columns(2)
    for i, bot in enumerate(bots):
        create_bot_card(bot, cols[i % 2])

def show_home_page():
    st.title("🎭 CRINGE - Personagens Interativos")
    st.markdown("Bem-vindo ao universo de personagens IA interativos! 🌟")
    st.markdown("---")
    
    bots = load_bots_from_db()
    health_data = check_api_health()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Personagens", len(bots))
    with col2:
        status_icon = "✅" if st.session_state.api_health == "healthy" else "❌"
        st.metric("Status API", f"{status_icon} {st.session_state.api_health.title()}")
    with col3:
        active_convos = len([c for c in st.session_state.conversations.values() if c['messages']])
        st.metric("Conversas Ativas", active_convos)
    with col4:
        total_messages = sum(len(conv['messages']) for conv in st.session_state.conversations.values())
        st.metric("Mensagens", total_messages)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Explorar Personagens", use_container_width=True, type="primary"):
            st.session_state.current_page = "bots"
            st.rerun()
    with col2:
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    if bots:
        st.subheader("🚀 Personagens em Destaque")
        featured_bots = bots[:4]
        
        cols = st.columns(min(4, len(featured_bots)))
        for idx, bot in enumerate(featured_bots):
            with cols[idx]:
                st.image(bot['avatar_url'], use_column_width=True)
                st.subheader(bot['name'])
                st.write(bot['introduction'][:80] + "...")
                if st.button(f"Conversar", key=f"featured_{idx}", use_container_width=True):
                    st.session_state.current_bot = bot
                    st.session_state.current_page = "chat"
                    st.rerun()

# Barra lateral
with st.sidebar:
    st.title("🎭 CRINGE")
    st.markdown("---")
    
    st.subheader("Navegação")
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("🏠 Início", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    with nav_col2:
        if st.button("🤖 Personagens", use_container_width=True):
            st.session_state.current_page = "bots"
            st.rerun()
    
    st.markdown("---")
    
    st.subheader("Status do Sistema")
    
    health_status = st.session_state.api_health
    if health_status == "healthy":
        st.success("✅ Backend Online")
    elif health_status == "unhealthy":
        st.error("❌ Backend com Problemas")
    else:
        st.warning("⚠️ Backend Inacessível")
    
    health_data = check_api_health()
    if health_data and health_status == "healthy":
        st.info(f"**Estatísticas:**")
        stats = health_data.get('statistics', {})
        st.write(f"• {stats.get('bots', 0)} Personagens")
        st.write(f"• {stats.get('conversations', 0)} Conversas")
        st.write(f"• {stats.get('messages', 0)} Mensagens")
    
    st.markdown("---")
    
    st.subheader("Gerenciamento")
    
    if st.button("🗑️ Limpar Todas Conversas", use_container_width=True):
        st.session_state.conversations = {}
        st.success("✅ Todas as conversas foram limpas!")
        st.rerun()
    
    if st.button("🧹 Limpar Cache", use_container_width=True):
        st.cache_data.clear()
        st.success("✅ Cache limpo!")
        st.rerun()
    
    st.markdown("---")
    st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")

# Roteamento principal
if st.session_state.current_page == "home":
    show_home_page()
elif st.session_state.current_page == "bots":
    show_bots_list()
elif st.session_state.current_page == "chat":
    show_chat_interface()

# Rodapé
st.markdown("---")
st.caption("🎭 CRINGE - Personagens Interativos | Desenvolvido com Streamlit & FastAPI")