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
        'last_update': None,
        'last_user_message': None,
        'waiting_for_response': False
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
    """Função para debug do status da IA"""
    try:
        response = requests.get(f"{API_URL}/debug/ai-status", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def debug_test_ai():
    """Teste direto da IA"""
    try:
        response = requests.get(f"{API_URL}/debug/test-ai", timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except:
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
                key=f"chat_button_{bot['id']}",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.current_bot = bot
                st.session_state.current_page = "chat"
                st.session_state.last_user_message = None
                st.rerun()

def show_chat_interface():
    if not st.session_state.current_bot:
        st.error("❌ Nenhum personagem selecionado")
        if st.button("🏠 Voltar para Início", 
                    key="back_home_from_error",
                    use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
        return
    
    bot = st.session_state.current_bot
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title(f"💬 {bot['name']}")
        st.caption(f"*{bot['introduction']}*")
    with col2:
        if st.button("📋 Personagens", 
                    key="back_to_bots_from_chat",
                    use_container_width=True):
            st.session_state.current_page = "bots"
            st.rerun()
    with col3:
        if st.button("🏠 Início", 
                    key="back_home_from_chat",
                    use_container_width=True):
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
    
    st.markdown("#### 💬 Conversa")
    chat_container = st.container()
    
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
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Limpar Chat", 
                    key=f"clear_chat_{bot['id']}",
                    use_container_width=True):
            st.session_state.conversations[bot['id']] = {
                'conversation_id': None,
                'messages': [],
                'started_at': datetime.now().isoformat()
            }
            st.session_state.last_user_message = None
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.get('waiting_for_response', False):
        user_message = st.chat_input(
            f"⏳ Aguardando resposta de {bot['name']}...",
            key=f"chat_input_disabled_{bot['id']}",
            disabled=True
        )
    else:
        user_message = st.chat_input(
            f"Digite sua mensagem para {bot['name']}...",
            key=f"chat_input_{bot['id']}"
        )
    
    if user_message and user_message.strip() and not st.session_state.get('waiting_for_response', False):
        if len(user_message) > 1000:
            st.warning("⚠️ Mensagem muito longa. Limite: 1000 caracteres.")
            st.rerun()
            return
        
        if st.session_state.last_user_message == user_message.strip():
            st.warning("⚠️ Você já enviou esta mensagem. Tente dizer algo diferente!")
            st.rerun()
            return
        
        st.session_state.waiting_for_response = True
        st.session_state.last_user_message = user_message.strip()
        
        current_conversation['messages'].append({
            'content': user_message,
            'is_user': True,
            'timestamp': datetime.now().isoformat()
        })
        
        with chat_container:
            with st.chat_message("user"):
                st.write(user_message)
                st.caption(f"🕒 {datetime.now().strftime('%H:%M')}")
        
        with st.spinner(f"**{bot['name']}** está pensando... 💫"):
            response = chat_with_bot(
                bot['id'], 
                user_message, 
                current_conversation['conversation_id']
            )
            
            st.session_state.waiting_for_response = False
            
            if response and response.get('response'):
                last_bot_message = None
                for msg in reversed(current_conversation['messages']):
                    if not msg['is_user']:
                        last_bot_message = msg['content']
                        break
                
                if not last_bot_message or last_bot_message != response['response']:
                    current_conversation['conversation_id'] = response['conversation_id']
                    current_conversation['messages'].append({
                        'content': response['response'],
                        'is_user': False,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    current_conversation['messages'].append({
                        'content': "🔄 Vamos mudar de assunto! O que mais gostaria de conversar?",
                        'is_user': False,
                        'timestamp': datetime.now().isoformat()
                    })
                
                st.rerun()
            else:
                error_fallbacks = {
                    "Pimenta (Pip)": "💫 *Chocalho, chocalho!* Minhas magias estão um pouco desalinhadas no momento. Vamos tentar novamente?",
                    "Zimbrak": "⚙️ *Engrenagens rangendo* Hmm, meus circuitos precisam de ajustes. Podemos recomeçar?",
                    "Luma": "📖 *Letras tremulam suavemente* Meus textos estão se reorganizando... Tente novamente.",
                    "Tiko": "🎪 *Cores piscando* OPA! Meus circuitos estão dançando! Vamos tentar de novo?"
                }
                
                fallback = error_fallbacks.get(
                    bot['name'], 
                    "🤖 Estou tendo dificuldades técnicas no momento. Podemos tentar novamente?"
                )
                
                current_conversation['messages'].append({
                    'content': fallback,
                    'is_user': False,
                    'timestamp': datetime.now().isoformat()
                })
                st.rerun()

def show_bots_list():
    st.title("🤖 Personagens Disponíveis")
    st.markdown("---")
    
    bots = load_bots_from_db()
    
    if not bots:
        st.error("🚫 Nenhum personagem encontrado.")
        st.info("""
        **Solução de problemas:**
        1. Verifique se o backend está rodando em: `{API_URL}`
        2. Confirme se a API Key do OpenRouter está configurada
        3. Verifique os logs do backend para mais detalhes
        """)
        
        if st.button("🔄 Tentar Novamente", 
                    key="retry_load_bots",
                    use_container_width=True):
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
    
    # Inicializar ai_status para evitar o NameError
    ai_status = debug_ai_status() or {}
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Personagens", len(bots) if bots else 0)
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
    
    # Status da IA - CORRIGIDO: apenas Mistral
    st.subheader("🔧 Status do Serviço de IA")
    
    if ai_status:
        current_model = ai_status.get('current_model', 'mistralai/mistral-7b-instruct:free')
        
        if ai_status.get('connection_test'):
            st.success("✅ Serviço de IA: Conectado e Funcionando")
            st.info(f"**Modelo Atual:** {current_model}")
        else:
            st.error("❌ Serviço de IA: Problemas de Conexão")
            
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**API Key Configurada:** {'✅ Sim' if ai_status.get('api_key_set') else '❌ Não'}")
            if ai_status.get('api_key_set'):
                st.write(f"**Comprimento da Key:** {ai_status.get('api_key_length', 0)} caracteres")
        with col2:
            st.write(f"**Modelo:** Mistral 7B Instruct")
            st.write(f"**Status:** {'✅ OK' if ai_status.get('connection_test') else '❌ Falhou'}")
        
        # Botão para testar o modelo
        if st.button("🧪 Testar Modelo Mistral", key="test_mistral_model"):
            with st.spinner("Testando modelo Mistral..."):
                test_results = debug_test_ai()
                if test_results:
                    if test_results.get('response_type') == 'success':
                        st.success(f"✅ Teste bem-sucedido! Resposta: {test_results.get('response')}")
                    else:
                        st.error(f"❌ Teste falhou: {test_results.get('response')}")
                else:
                    st.error("Falha ao testar o modelo")
    else:
        st.warning("⚠️ Não foi possível obter status do serviço de IA")
        st.info("O backend pode estar indisponível ou a rota de debug não está funcionando.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Explorar Personagens", 
                    key="explore_bots_home",
                    use_container_width=True, 
                    type="primary"):
            st.session_state.current_page = "bots"
            st.rerun()
    with col2:
        if st.button("🔄 Atualizar Dados", 
                    key="refresh_data_home",
                    use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.subheader("ℹ️ Como Usar")
    st.info("""
    1. **Escolha um personagem** na página de Personagens
    2. **Inicie uma conversa** clicando em "Conversar"
    3. **Interaja naturalmente** - os personagens têm personalidades únicas!
    4. **Powered by:** Mistral AI via OpenRouter
    """)
    
    if bots:
        st.subheader("🚀 Personagens em Destaque")
        featured_bots = bots[:4]
        
        cols = st.columns(min(4, len(featured_bots)))
        for idx, bot in enumerate(featured_bots):
            with cols[idx]:
                st.image(bot['avatar_url'], use_column_width=True)
                st.subheader(bot['name'])
                st.write(bot['introduction'][:80] + "...")
                if st.button(f"Conversar", 
                           key=f"featured_chat_{bot['id']}",
                           use_container_width=True):
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
        if st.button("🏠 Início", 
                    key="nav_home_sidebar",
                    use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    with nav_col2:
        if st.button("🤖 Personagens", 
                    key="nav_bots_sidebar",
                    use_container_width=True):
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
        
        ai_status_health = health_data.get('ai_service', 'unknown')
        if ai_status_health == 'available':
            st.success("🤖 Serviço de IA: Disponível")
        else:
            st.error(f"🤖 Serviço de IA: {ai_status_health}")
    
    st.markdown("---")
    
    st.subheader("Gerenciamento")
    
    if st.button("🗑️ Limpar Todas Conversas", 
                key="clear_all_chats_sidebar",
                use_container_width=True):
        st.session_state.conversations = {}
        st.session_state.last_user_message = None
        st.success("✅ Todas as conversas foram limpas!")
        st.rerun()
    
    if st.button("🧹 Limpar Cache", 
                key="clear_cache_sidebar",
                use_container_width=True):
        st.cache_data.clear()
        st.session_state.last_user_message = None
        st.success("✅ Cache limpo!")
        st.rerun()
    
    st.markdown("---")
    
    if st.checkbox("🔍 Debug Avançado", key="debug_toggle"):
        st.write("**Debug Info:**")
        st.write(f"- Página: {st.session_state.current_page}")
        st.write(f"- Bot: {st.session_state.current_bot['name'] if st.session_state.current_bot else 'None'}")
        st.write(f"- Última msg: {st.session_state.last_user_message}")
        st.write(f"- Esperando: {st.session_state.waiting_for_response}")
        
        # Teste de status da IA
        if st.button("Testar Conexão IA", key="test_ai_connection"):
            ai_status_debug = debug_ai_status()
            if ai_status_debug:
                st.json(ai_status_debug)
            else:
                st.error("Falha ao testar conexão IA")
    
    st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    st.caption("🤖 Powered by Mistral AI")

# Roteamento principal
if st.session_state.current_page == "home":
    show_home_page()
elif st.session_state.current_page == "bots":
    show_bots_list()
elif st.session_state.current_page == "chat":
    show_chat_interface()

st.markdown("---")
st.caption("🎭 CRINGE - Personagens Interativos | Desenvolvido com Streamlit & FastAPI")
st.caption("🤖 Powered by Mistral AI via OpenRouter")