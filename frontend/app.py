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
        'last_user_message': None,  # Para evitar repetição
        'waiting_for_response': False  # Para evitar múltiplos envios
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
            
            # Botão com chave baseada no ID do bot
            if st.button(
                "💬 Conversar", 
                key=f"chat_button_{bot['id']}",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.current_bot = bot
                st.session_state.current_page = "chat"
                st.session_state.last_user_message = None  # Resetar ao mudar de bot
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
    
    # Header do chat
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
    
    # Inicializar conversa se não existir
    if bot['id'] not in st.session_state.conversations:
        st.session_state.conversations[bot['id']] = {
            'conversation_id': None,
            'messages': [],
            'started_at': datetime.now().isoformat()
        }
    
    current_conversation = st.session_state.conversations[bot['id']]
    
    # Área de chat
    st.markdown("#### 💬 Conversa")
    chat_container = st.container()
    
    with chat_container:
        # Exibir mensagem de boas-vindas se não houver mensagens
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
    
    # Controles de conversa
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
    
    # Input de mensagem
    st.markdown("---")
    
    # Se estiver esperando resposta, desabilitar input
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
        # Validar comprimento da mensagem
        if len(user_message) > 1000:
            st.warning("⚠️ Mensagem muito longa. Limite: 1000 caracteres.")
            st.rerun()
            return
        
        # Verificar se a mensagem não é repetida
        if st.session_state.last_user_message == user_message.strip():
            st.warning("⚠️ Você já enviou esta mensagem. Tente dizer algo diferente!")
            st.rerun()
            return
        
        # Marcar que estamos esperando resposta
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
        
        # Obter resposta
        with st.spinner(f"**{bot['name']}** está pensando... 💫"):
            response = chat_with_bot(
                bot['id'], 
                user_message, 
                current_conversation['conversation_id']
            )
            
            # Remover flag de espera
            st.session_state.waiting_for_response = False
            
            if response and response.get('response'):
                # Verificar se a resposta não é repetida
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
                    # Se for repetida, adicionar mensagem alternativa
                    current_conversation['messages'].append({
                        'content': "🔄 Vamos mudar de assunto! O que mais gostaria de conversar?",
                        'is_user': False,
                        'timestamp': datetime.now().isoformat()
                    })
                
                st.rerun()
            else:
                # Adicionar mensagem de erro genérica
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
    
    # Layout de grid responsivo
    cols = st.columns(2)
    for i, bot in enumerate(bots):
        create_bot_card(bot, cols[i % 2])

def show_home_page():
    st.title("🎭 CRINGE - Personagens Interativos")
    st.markdown("Bem-vindo ao universo de personagens IA interativos! 🌟")
    st.markdown("---")
    
    bots = load_bots_from_db()
    health_data = check_api_health()
    
    # Métricas
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
    
    # Botões de ação principais
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
    
    # Informações do sistema
    st.subheader("ℹ️ Como Usar")
    st.info("""
    1. **Escolha um personagem** na página de Personagens
    2. **Inicie uma conversa** clicando em "Conversar"
    3. **Interaja naturalmente** - os personagens têm personalidades únicas!
    4. **Problemas?** Verifique se a API Key do OpenRouter está configurada no backend
    """)
    
    # Personagens em destaque
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
    
    # Navegação
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
    
    # Status do sistema
    st.subheader("Status do Sistema")
    
    health_status = st.session_state.api_health
    if health_status == "healthy":
        st.success("✅ Backend Online")
    elif health_status == "unhealthy":
        st.error("❌ Backend com Problemas")
    else:
        st.warning("⚠️ Backend Inacessível")
    
    # Informações adicionais de saúde
    health_data = check_api_health()
    if health_data and health_status == "healthy":
        st.info(f"**Estatísticas:**")
        stats = health_data.get('statistics', {})
        st.write(f"• {stats.get('bots', 0)} Personagens")
        st.write(f"• {stats.get('conversations', 0)} Conversas")
        st.write(f"• {stats.get('messages', 0)} Mensagens")
        
        # Informação da API Key
        ai_status = health_data.get('ai_service', 'unknown')
        if ai_status == 'available':
            st.success("🤖 Serviço de IA: Disponível")
        else:
            st.error(f"🤖 Serviço de IA: {ai_status}")
    
    st.markdown("---")
    
    # Gerenciamento de dados
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
    
    # Debug info (apenas desenvolvimento)
    if st.checkbox("🔍 Mostrar Informações de Debug", key="debug_toggle"):
        st.write("**Debug Info:**")
        st.write(f"- Página atual: {st.session_state.current_page}")
        st.write(f"- Bot atual: {st.session_state.current_bot['name'] if st.session_state.current_bot else 'None'}")
        st.write(f"- Última mensagem: {st.session_state.last_user_message}")
        st.write(f"- Esperando resposta: {st.session_state.waiting_for_response}")
        st.write(f"- Total conversas: {len(st.session_state.conversations)}")
    
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
footer_col1, footer_col2 = st.columns([3, 1])
with footer_col1:
    st.caption("🎭 CRINGE - Personagens Interativos | Desenvolvido com Streamlit & FastAPI")
with footer_col2:
    st.caption(f"v3.0.0 | {datetime.now().year}")