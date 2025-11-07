import streamlit as st
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import time
import hashlib

# Configuração da página
st.set_page_config(
    page_title="CRINGE - Personagens Interativos",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações da API
API_URL = "https://cringe-5jmi.onrender.com"

# Inicialização do session_state
def initialize_session_state():
    defaults = {
        'current_page': "home",
        'current_bot': None,
        'conversations': {},
        'selected_bot_id': None,
        'api_health': "checking",
        'last_update': None,
        'last_user_message': None,
        'waiting_for_response': False,
        'force_rerun': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# Função para gerar chaves únicas
def generate_unique_key(prefix=""):
    """Gera uma chave única baseada no timestamp e prefixo"""
    timestamp = str(time.time())
    unique_string = f"{prefix}_{timestamp}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:10]

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
            return []
    except Exception as e:
        st.session_state.api_health = "unreachable"
        return []

def chat_with_bot(bot_id: str, message: str, conversation_id: Optional[str] = None):
    try:
        payload = {
            "message": message,
            "conversation_id": conversation_id
        }
        
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

def debug_ai_status():
    try:
        response = requests.get(f"{API_URL}/debug/ai-status", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def debug_conversation(conversation_id: str):
    try:
        response = requests.get(f"{API_URL}/debug/conversation/{conversation_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# CORREÇÃO RADICAL: Nova função para navegação
def navigate_to_page(page_name, bot=None):
    """Função centralizada para navegação entre páginas"""
    st.session_state.current_page = page_name
    if bot:
        st.session_state.current_bot = bot
        st.session_state.selected_bot_id = bot['id']
    else:
        st.session_state.current_bot = None
        st.session_state.selected_bot_id = None
    
    # Forçar rerun usando um truque do Streamlit
    st.session_state.force_rerun = not st.session_state.get('force_rerun', False)

# Componentes da UI
def create_bot_card(bot, column):
    with column:
        with st.container():
            # Imagem com CSS customizado
            st.markdown(
                f"""
                <div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 1rem;">
                    <img src="{bot['avatar_url']}" style="width: 100%; max-width: 280px; height: auto; border-radius: 10px; border: 2px solid #4CAF50;">
                    <p style="text-align: center; margin-top: 0.5rem; font-style: italic;">🎭 {bot['name']}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            st.subheader(bot['name'])
            st.caption(f"⚧ {bot.get('gender', 'Não especificado')}")
            
            with st.expander("📖 Sobre este personagem"):
                st.write(bot['introduction'])
                st.write(f"**Personalidade:** {bot['personality']}")
                
                if bot.get('tags'):
                    tags = " ".join([f"`{tag}`" for tag in bot['tags']])
                    st.write(f"**Tags:** {tags}")
            
            # CORREÇÃO: Botão usando a nova função de navegação
            if st.button(
                "💬 Conversar", 
                key=f"chat_btn_{bot['id']}_{generate_unique_key()}",
                use_container_width=True,
                type="primary"
            ):
                navigate_to_page("chat", bot)

def show_chat_interface():
    # Verificação mais robusta do bot atual
    if not st.session_state.current_bot:
        # Tentar carregar bots e encontrar pelo ID selecionado
        bots = load_bots_from_db()
        if st.session_state.selected_bot_id:
            for bot in bots:
                if bot['id'] == st.session_state.selected_bot_id:
                    st.session_state.current_bot = bot
                    break
        
        # Se ainda não encontrou, mostrar erro
        if not st.session_state.current_bot:
            st.error("❌ Nenhum personagem selecionado ou personagem não encontrado")
            st.info("💡 Tente selecionar um personagem novamente da lista")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Ver Todos os Personagens", 
                            key=generate_unique_key("goto_bots_from_chat_error"),
                            use_container_width=True):
                    navigate_to_page("bots")
            with col2:
                if st.button("🏠 Voltar para Início", 
                            key=generate_unique_key("goto_home_from_chat_error"),
                            use_container_width=True):
                    navigate_to_page("home")
            return
    
    bot = st.session_state.current_bot
    
    # Header do chat
    st.markdown(f"## 💬 Conversando com **{bot['name']}**")
    
    # Avatar e informações
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; align-items: center;">
                <img src="{bot['avatar_url']}" style="width: 100%; max-width: 150px; height: auto; border-radius: 10px; border: 3px solid #FF6B6B;">
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col2:
        st.write(f"**{bot['introduction']}**")
        st.caption(f"💫 {bot['personality']}")
    
    # Botões de navegação
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🏠 Página Inicial", 
                    key=generate_unique_key("home_from_chat"),
                    use_container_width=True):
            navigate_to_page("home")
    with col2:
        if st.button("📋 Todos Personagens", 
                    key=generate_unique_key("bots_from_chat"),
                    use_container_width=True):
            navigate_to_page("bots")
    with col3:
        if st.button("🔄 Reiniciar Chat", 
                    key=generate_unique_key("restart_chat"),
                    use_container_width=True):
            if bot['id'] in st.session_state.conversations:
                st.session_state.conversations[bot['id']] = {
                    'conversation_id': None,
                    'messages': [],
                    'started_at': datetime.now().isoformat()
                }
            st.session_state.last_user_message = None
            st.rerun()
    
    st.markdown("---")
    
    # Inicializar conversa se não existir
    if bot['id'] not in st.session_state.conversations:
        st.session_state.conversations[bot['id']] = {
            'conversation_id': None,
            'messages': [],
            'started_at': datetime.now().isoformat()
        }
    
    current_conversation = st.session_state.conversations[bot['id']]
    
    # Área de mensagens
    chat_container = st.container()
    with chat_container:
        # Mensagem de boas-vindas se não houver mensagens
        if not current_conversation['messages']:
            with st.chat_message("assistant", avatar=bot['avatar_url']):
                st.write(bot['welcome_message'])
                st.caption("✨ Mensagem de boas-vindas")
            
            current_conversation['messages'].append({
                'content': bot['welcome_message'],
                'is_user': False,
                'timestamp': datetime.now().isoformat()
            })
        
        # Exibir histórico de mensagens
        for i, msg in enumerate(current_conversation['messages']):
            avatar = None if msg['is_user'] else bot['avatar_url']
            with st.chat_message("user" if msg['is_user'] else "assistant", avatar=avatar):
                st.write(msg['content'])
                if 'timestamp' in msg:
                    try:
                        time_str = datetime.fromisoformat(msg['timestamp']).strftime("%H:%M")
                        st.caption(f"🕒 {time_str}")
                    except:
                        pass
    
    # Input de mensagem
    st.markdown("---")
    
    if st.session_state.get('waiting_for_response', False):
        user_message = st.chat_input(
            f"⏳ {bot['name']} está digitando...",
            key=generate_unique_key("disabled_input"),
            disabled=True
        )
    else:
        user_message = st.chat_input(
            f"Digite sua mensagem para {bot['name']}...",
            key=generate_unique_key("active_input")
        )
    
    # Processar mensagem do usuário
    if user_message and user_message.strip() and not st.session_state.get('waiting_for_response', False):
        if len(user_message) > 1000:
            st.warning("⚠️ Mensagem muito longa. Limite: 1000 caracteres.")
            return
        
        # Verificação de repetição
        if (st.session_state.last_user_message and 
            st.session_state.last_user_message.strip().lower() == user_message.strip().lower()):
            st.warning("⚠️ Você já enviou esta mensagem. Tente dizer algo diferente!")
            return
        
        st.session_state.waiting_for_response = True
        st.session_state.last_user_message = user_message.strip()
        
        # Adicionar mensagem do usuário
        current_conversation['messages'].append({
            'content': user_message,
            'is_user': True,
            'timestamp': datetime.now().isoformat()
        })
        
        # Exibir mensagem do usuário imediatamente
        with chat_container:
            with st.chat_message("user"):
                st.write(user_message)
                st.caption(f"🕒 {datetime.now().strftime('%H:%M')}")
        
        # Obter resposta da IA
        with st.spinner(f"**{bot['name']}** está pensando... 💫"):
            response = chat_with_bot(
                bot['id'], 
                user_message, 
                current_conversation['conversation_id']
            )
            
            st.session_state.waiting_for_response = False
            
            if response and response.get('response'):
                # Atualizar conversa com resposta
                current_conversation['conversation_id'] = response['conversation_id']
                current_conversation['messages'].append({
                    'content': response['response'],
                    'is_user': False,
                    'timestamp': datetime.now().isoformat()
                })
                st.rerun()
            else:
                # Mensagem de fallback
                error_fallbacks = {
                    "Pimenta (Pip)": "💫 *Chocalho!* Algo interrompeu minha conexão mágica... Mas sinto que você queria compartilhar algo importante!",
                    "Zimbrak": "⚙️ *Engrenagens se reajustando* Hmm, uma falha momentânea... Você estava dizendo algo interessante!",
                    "Luma": "📖 *Letras se reestabilizando* Um breve silêncio interrompeu nosso fluxo... Continue, por favor.",
                    "Tiko": "🎪 *Cores se recompondo* OPA! Um pequeno tremor na matrix! Conte mais sobre o que estava dizendo!"
                }
                
                fallback = error_fallbacks.get(
                    bot['name'], 
                    "🤖 Um momento de instabilidade... Mas quero ouvir mais do que você tem a dizer!"
                )
                
                current_conversation['messages'].append({
                    'content': fallback,
                    'is_user': False,
                    'timestamp': datetime.now().isoformat()
                })
                st.rerun()

def show_bots_list():
    st.title("🤖 Todos os Personagens")
    st.markdown("---")
    
    bots = load_bots_from_db()
    
    if not bots:
        st.error("🚫 Nenhum personagem encontrado.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Tentar Novamente", 
                        key=generate_unique_key("retry_bots"),
                        use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button("🏠 Voltar para Início", 
                        key=generate_unique_key("home_from_bots"),
                        use_container_width=True):
                navigate_to_page("home")
        return
    
    # Layout de cards
    cols = st.columns(2)
    for i, bot in enumerate(bots):
        create_bot_card(bot, cols[i % 2])

def show_home_page():
    st.title("🎭 CRINGE - Personagens Interativos")
    st.markdown("### Bem-vindo ao universo de personagens IA interativos! 🌟")
    st.markdown("---")
    
    bots = load_bots_from_db()
    health_data = check_api_health()
    ai_status = debug_ai_status() or {}
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Personagens", len(bots) if bots else 0)
    with col2:
        status_icon = "✅" if st.session_state.api_health == "healthy" else "❌"
        st.metric("Status API", f"{status_icon}")
    with col3:
        active_convos = len([c for c in st.session_state.conversations.values() if c['messages']])
        st.metric("Conversas Ativas", active_convos)
    with col4:
        total_messages = sum(len(conv['messages']) for conv in st.session_state.conversations.values())
        st.metric("Mensagens", total_messages)
    
    st.markdown("---")
    
    # Status do sistema
    st.subheader("🔧 Status do Sistema")
    
    if ai_status and ai_status.get('connection_test'):
        st.success("✅ Serviço de IA: Conectado e Funcionando")
    else:
        st.error("❌ Serviço de IA: Problemas de Conexão")
    
    # Botões de ação principais
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Explorar Todos os Personagens", 
                    key=generate_unique_key("explore_all"),
                    use_container_width=True, 
                    type="primary"):
            navigate_to_page("bots")
    with col2:
        if st.button("🔄 Atualizar Sistema", 
                    key=generate_unique_key("refresh_system"),
                    use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Instruções
    st.markdown("---")
    st.subheader("🎯 Como Começar")
    st.info("""
    1. **Clique em 'Explorar Todos os Personagens'** para ver a lista completa
    2. **Escolha um personagem** que mais te interessar
    3. **Clique em 'Conversar'** para iniciar uma conversa
    4. **Interaja naturalmente** - cada personagem tem personalidade única!
    """)
    
    # Personagens em destaque
    if bots:
        st.markdown("---")
        st.subheader("⭐ Personagens em Destaque")
        
        featured_bots = bots[:4]  # Primeiros 4 bots
        cols = st.columns(min(4, len(featured_bots)))
        
        for idx, bot in enumerate(featured_bots):
            with cols[idx]:
                # Card simplificado para destaque
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 1rem; border: 2px solid #6366F1; border-radius: 10px; margin: 0.5rem;">
                        <img src="{bot['avatar_url']}" style="width: 100%; max-width: 120px; height: auto; border-radius: 8px; margin-bottom: 0.5rem;">
                        <h4 style="margin: 0.5rem 0;">{bot['name']}</h4>
                        <p style="font-size: 0.9rem; color: #666;">{bot['introduction'][:60]}...</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                if st.button(f"Conversar com {bot['name']}", 
                           key=f"featured_{bot['id']}_{generate_unique_key()}",
                           use_container_width=True):
                    navigate_to_page("chat", bot)

# Barra lateral
with st.sidebar:
    st.title("🎭 CRINGE")
    st.markdown("---")
    
    st.subheader("📱 Navegação")
    
    # Botões de navegação principais
    if st.button("🏠 Página Inicial", 
                key=generate_unique_key("nav_home"),
                use_container_width=True):
        navigate_to_page("home")
    
    if st.button("🤖 Ver Personagens", 
                key=generate_unique_key("nav_bots"), 
                use_container_width=True):
        navigate_to_page("bots")
    
    st.markdown("---")
    
    st.subheader("📊 Status")
    health_status = st.session_state.api_health
    if health_status == "healthy":
        st.success("✅ Backend Online")
    elif health_status == "unhealthy":
        st.error("❌ Backend com Problemas")
    else:
        st.warning("⚠️ Backend Inacessível")
    
    # Estatísticas rápidas
    bots = load_bots_from_db()
    if bots:
        st.info(f"**{len(bots)}** personagens disponíveis")
    
    st.markdown("---")
    
    st.subheader("⚙️ Gerenciamento")
    
    if st.button("🗑️ Limpar Todas Conversas", 
                key=generate_unique_key("clear_all"),
                use_container_width=True):
        st.session_state.conversations = {}
        st.session_state.last_user_message = None
        st.success("Conversas limpas!")
        st.rerun()
    
    if st.button("🧹 Limpar Cache", 
                key=generate_unique_key("clear_cache"),
                use_container_width=True):
        st.cache_data.clear()
        st.success("Cache limpo!")
        st.rerun()
    
    st.markdown("---")
    
    # Debug info
    if st.checkbox("🔍 Mostrar Info de Debug", key=generate_unique_key("debug")):
        st.write("**Estado Atual:**")
        st.write(f"- Página: `{st.session_state.current_page}`")
        st.write(f"- Bot Selecionado: `{st.session_state.selected_bot_id}`")
        st.write(f"- Bot Atual: `{st.session_state.current_bot['name'] if st.session_state.current_bot else 'None'}`")
        st.write(f"- Conversas: `{len(st.session_state.conversations)}`")
    
    st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    st.caption("🤖 Powered by Mistral AI")

# Roteamento principal - SIMPLIFICADO
if st.session_state.current_page == "home":
    show_home_page()
elif st.session_state.current_page == "bots":
    show_bots_list()
elif st.session_state.current_page == "chat":
    show_chat_interface()

# Footer
st.markdown("---")
st.caption("🎭 CRINGE - Personagens Interativos | Desenvolvido com Streamlit & FastAPI")
st.caption("🤖 Powered by Mistral AI via OpenRouter")

# Forçar rerun se necessário
if st.session_state.get('force_rerun'):
    st.session_state.force_rerun = False
    st.rerun()