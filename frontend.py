import streamlit as st
import requests
import json
import uuid
from typing import List, Dict, Optional

# Configuração da página
st.set_page_config(
    page_title="CRINGE - Personagens Interativos",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações da API
API_URL = "https://cringe-5jmi.onrender.com"  # Substitua pela sua URL

# Inicialização do session_state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"
if 'current_bot' not in st.session_state:
    st.session_state.current_bot = None
if 'delete_confirm' not in st.session_state:
    st.session_state.delete_confirm = None
if 'delete_bot_name' not in st.session_state:
    st.session_state.delete_bot_name = None
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'widget_key_counter' not in st.session_state:
    st.session_state.widget_key_counter = 0

def get_unique_key(prefix="key"):
    """Gera uma chave única para widgets"""
    st.session_state.widget_key_counter += 1
    return f"{prefix}_{st.session_state.widget_key_counter}"

# Funções da API
def load_bots_from_db() -> List[Dict]:
    """Carrega bots do banco de dados"""
    try:
        response = requests.get(f"{API_URL}/bots")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Erro ao carregar bots")
            return []
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return []

def delete_bot(bot_id: str):
    """Exclui um bot"""
    try:
        response = requests.delete(f"{API_URL}/bots/{bot_id}")
        if response.status_code == 200:
            st.success("✅ Bot excluído com sucesso!")
            # Limpar estado de confirmação
            st.session_state.delete_confirm = None
            st.session_state.delete_bot_name = None
            st.rerun()
        else:
            error_msg = response.json().get('error', 'Erro desconhecido')
            st.error(f"❌ Erro ao excluir bot: {error_msg}")
    except Exception as e:
        st.error(f"❌ Erro ao conectar com o servidor: {str(e)}")

def chat_with_bot(bot_id: str, message: str, conversation_id: Optional[str] = None):
    """Envia mensagem para um bot"""
    try:
        payload = {
            "message": message,
            "conversation_id": conversation_id
        }
        response = requests.post(f"{API_URL}/bots/chat/{bot_id}", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Erro ao enviar mensagem")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None

def import_bots(bots_data: Dict):
    """Importa bots via JSON"""
    try:
        response = requests.post(f"{API_URL}/bots/import", json=bots_data)
        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ {result['message']}")
            return True
        else:
            error_msg = response.json().get('detail', 'Erro desconhecido')
            st.error(f"❌ Erro ao importar: {error_msg}")
            return False
    except Exception as e:
        st.error(f"❌ Erro de conexão: {str(e)}")
        return False

# Componentes da UI
def show_delete_confirmation(bot_name: str, bot_id: str):
    """Modal de confirmação para excluir bot"""
    st.warning(f"🗑️ **Tem certeza que deseja excluir {bot_name}?**")
    st.error("⚠️ **Esta ação não pode ser desfeita!** Todas as conversas com este bot serão perdidas.")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("✅ SIM, EXCLUIR", key=get_unique_key("confirm_delete"), type="primary", use_container_width=True):
            delete_bot(bot_id)
    with col2:
        if st.button("❌ CANCELAR", key=get_unique_key("cancel_delete"), use_container_width=True):
            st.session_state.delete_confirm = None
            st.session_state.delete_bot_name = None
            st.rerun()
    with col3:
        st.write("")  # Espaço vazio para alinhamento

def show_bots_list():
    """Página de listagem de bots"""
    st.title("🤖 Meus Personagens")
    st.markdown("---")
    
    # Carregar bots
    bots = load_bots_from_db()
    
    if not bots:
        st.info("""
        🎭 **Nenhum personagem encontrado!**
        
        Use a página de **Importação** para adicionar personagens ou 
        importe os personagens padrão do CRINGE.
        """)
        return
    
    # Modal de confirmação (se necessário)
    if st.session_state.delete_confirm:
        show_delete_confirmation(st.session_state.delete_bot_name, st.session_state.delete_confirm)
        st.markdown("---")
    
    # Lista de bots
    for i, bot in enumerate(bots):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Avatar e informações básicas
                col_avatar, col_info = st.columns([1, 4])
                with col_avatar:
                    st.image(bot['avatar_url'], width=60)
                with col_info:
                    st.subheader(bot['name'])
                    st.write(f"*{bot['introduction']}*")
                    st.caption(f"**Personalidade:** {bot['personality']}")
                    
                    # Tags
                    tags_html = " ".join([f"<span style='background-color: #444; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;'>{tag}</span>" for tag in bot['tags']])
                    st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)
            
            with col2:
                if st.button("💬 Conversar", key=f"chat_{bot['id']}_{i}", use_container_width=True):
                    st.session_state.current_bot = bot
                    st.session_state.current_page = "chat"
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Excluir", key=f"delete_{bot['id']}_{i}", use_container_width=True, type="secondary"):
                    st.session_state.delete_confirm = bot['id']
                    st.session_state.delete_bot_name = bot['name']
                    st.rerun()
            
            st.markdown("---")

def show_chat_interface():
    """Interface de chat com o bot"""
    if not st.session_state.current_bot:
        st.error("Nenhum bot selecionado")
        st.session_state.current_page = "home"
        st.rerun()
        return
    
    bot = st.session_state.current_bot
    
    # Header do chat
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"💬 {bot['name']}")
    with col2:
        if st.button("← Voltar", key=get_unique_key("back_chat"), use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    
    st.markdown(f"*{bot['introduction']}*")
    st.markdown("---")
    
    # Inicializar conversa se necessário
    conversation_id = st.session_state.conversations.get(bot['id'], {}).get('conversation_id')
    
    # Área de mensagens
    chat_container = st.container()
    
    # Input de mensagem
    with st.form(key=get_unique_key("chat_form"), clear_on_submit=True):
        col_input, col_send = st.columns([4, 1])
        with col_input:
            user_message = st.text_input(
                "Digite sua mensagem...",
                key=get_unique_key("user_input"),
                label_visibility="collapsed"
            )
        with col_send:
            send_button = st.form_submit_button("Enviar", use_container_width=True)
    
    # Processar mensagem
    if send_button and user_message.strip():
        # Adicionar mensagem do usuário
        if bot['id'] not in st.session_state.conversations:
            st.session_state.conversations[bot['id']] = {
                'conversation_id': None,
                'messages': []
            }
        
        # Adicionar mensagem do usuário
        st.session_state.conversations[bot['id']]['messages'].append({
            'content': user_message,
            'is_user': True
        })
        
        # Obter resposta do bot
        with st.spinner(f"{bot['name']} está pensando..."):
            response = chat_with_bot(
                bot['id'], 
                user_message, 
                conversation_id
            )
            
            if response:
                # Atualizar conversation_id
                st.session_state.conversations[bot['id']]['conversation_id'] = response['conversation_id']
                
                # Adicionar resposta do bot
                st.session_state.conversations[bot['id']]['messages'].append({
                    'content': response['response'],
                    'is_user': False
                })
        
        st.rerun()
    
    # Exibir histórico de mensagens
    with chat_container:
        if bot['id'] in st.session_state.conversations and st.session_state.conversations[bot['id']]['messages']:
            for msg in st.session_state.conversations[bot['id']]['messages']:
                if msg['is_user']:
                    with st.chat_message("user"):
                        st.write(msg['content'])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg['content'])
        else:
            # Mensagem de boas-vindas
            with st.chat_message("assistant"):
                st.write(bot['welcome_message'])
            
            # Adicionar mensagem de boas-vindas ao histórico
            if bot['id'] not in st.session_state.conversations:
                st.session_state.conversations[bot['id']] = {
                    'conversation_id': None,
                    'messages': [{
                        'content': bot['welcome_message'],
                        'is_user': False
                    }]
                }

def show_import_page():
    """Página de importação de bots"""
    st.title("📥 Importar Personagens")
    st.markdown("---")
    
    # Upload de arquivo JSON
    st.subheader("📁 Upload de Arquivo JSON")
    uploaded_file = st.file_uploader(
        "Selecione um arquivo JSON com os personagens",
        type=['json'],
        key=get_unique_key("file_uploader"),
        help="O arquivo deve estar no formato correto com a estrutura de bots"
    )
    
    # Área para colar JSON manualmente
    st.subheader("📝 Ou cole o JSON manualmente")
    json_input = st.text_area(
        "Cole o JSON aqui:",
        height=200,
        key=get_unique_key("json_input"),
        placeholder='{"bots": [{...}]}'
    )
    
    # Botões de ação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Importar do Upload", key=get_unique_key("import_upload"), use_container_width=True):
            if uploaded_file is not None:
                try:
                    bots_data = json.load(uploaded_file)
                    if import_bots(bots_data):
                        st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao ler arquivo: {str(e)}")
            else:
                st.warning("⚠️ Selecione um arquivo primeiro")
    
    with col2:
        if st.button("📤 Importar do Texto", key=get_unique_key("import_text"), use_container_width=True):
            if json_input.strip():
                try:
                    bots_data = json.loads(json_input)
                    if import_bots(bots_data):
                        st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro no JSON: {str(e)}")
            else:
                st.warning("⚠️ Cole o JSON no campo de texto")
    
    st.markdown("---")
    
    # Exemplo de JSON
    with st.expander("📋 Exemplo de Estrutura JSON", expanded=False):
        st.code("""
{
  "bots": [
    {
      "creator_id": "lore-master",
      "name": "Nome do Personagem",
      "gender": "Gênero",
      "introduction": "Descrição breve...",
      "personality": "Personalidade...",
      "welcome_message": "Mensagem de boas-vindas...",
      "avatar_url": "https://...",
      "tags": ["tag1", "tag2"],
      "conversation_context": "Contexto...",
      "context_images": "[]",
      "system_prompt": "Prompt completo...",
      "ai_config": {
        "temperature": 0.7,
        "max_output_tokens": 500
      }
    }
  ]
}
        """, language="json")

def show_home_page():
    """Página inicial"""
    st.title("🎭 CRINGE - Personagens Interativos")
    st.markdown("---")
    
    # Carregar estatísticas
    bots = load_bots_from_db()
    
    # Cards de estatísticas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Personagens Cadastrados",
            len(bots),
            help="Total de personagens disponíveis"
        )
    
    with col2:
        active_chats = len([conv for conv in st.session_state.conversations.values() if conv['messages']])
        st.metric(
            "Conversas Ativas",
            active_chats,
            help="Conversas em andamento"
        )
    
    with col3:
        total_messages = sum(len(conv['messages']) for conv in st.session_state.conversations.values())
        st.metric(
            "Mensagens Trocadas",
            total_messages,
            help="Total de mensagens em todas as conversas"
        )
    
    st.markdown("---")
    
    # Botões de ação principais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎭 Ver Personagens", key=get_unique_key("view_bots"), use_container_width=True):
            st.session_state.current_page = "bots"
            st.rerun()
    
    with col2:
        if st.button("💬 Nova Conversa", key=get_unique_key("new_chat"), use_container_width=True):
            st.session_state.current_page = "bots"
            st.rerun()
    
    with col3:
        if st.button("📥 Importar", key=get_unique_key("import_home"), use_container_width=True):
            st.session_state.current_page = "import"
            st.rerun()
    
    st.markdown("---")
    
    # Personagens recentes (se houver)
    if bots:
        st.subheader("🚀 Personagens Disponíveis")
        
        # Mostrar até 3 bots em cards
        cols = st.columns(min(3, len(bots)))
        for idx, bot in enumerate(bots[:3]):
            with cols[idx]:
                with st.container():
                    st.image(bot['avatar_url'], use_column_width=True)
                    st.subheader(bot['name'])
                    st.write(bot['introduction'])
                    if st.button(f"Conversar com {bot['name']}", key=f"home_chat_{bot['id']}_{idx}"):
                        st.session_state.current_bot = bot
                        st.session_state.current_page = "chat"
                        st.rerun()
        
        if len(bots) > 3:
            if st.button("Ver Todos os Personagens →", key=get_unique_key("view_all_bots")):
                st.session_state.current_page = "bots"
                st.rerun()
    else:
        # Mensagem de boas-vindas para novos usuários
        st.info("""
        ## 🎉 Bem-vindo ao CRINGE!
        
        **Personagens Interativos com Personalidades Únicas**
        
        Para começar:
        1. 📥 **Importe personagens** na página de Importação
        2. 🎭 **Explore os personagens** disponíveis  
        3. 💬 **Inicie conversas** e descubra suas personalidades
        
        *Personagens prontos disponíveis: Pimenta, Zimbrak, Luma e Tiko!*
        """)

# Barra lateral de navegação
with st.sidebar:
    st.title("🎭 CRINGE")
    st.markdown("---")
    
    # Navegação
    page_options = {
        "🏠 Início": "home",
        "🤖 Personagens": "bots", 
        "💬 Chat": "chat",
        "📥 Importar": "import"
    }
    
    for page_name, page_id in page_options.items():
        if st.button(page_name, 
                    key=f"nav_{page_id}",
                    use_container_width=True, 
                    type="primary" if st.session_state.current_page == page_id else "secondary"):
            st.session_state.current_page = page_id
            st.rerun()
    
    st.markdown("---")
    
    # Informações do sistema
    st.caption("**Status do Sistema**")
    try:
        health_response = requests.get(f"{API_URL}/health")
        if health_response.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Offline")
    except:
        st.error("❌ API Offline")
    
    # Botão de limpar conversas
    if st.button("🗑️ Limpar Todas as Conversas", key=get_unique_key("clear_chats"), use_container_width=True):
        st.session_state.conversations = {}
        st.success("Conversas limpas!")
        st.rerun()

# Roteamento de páginas
if st.session_state.current_page == "home":
    show_home_page()
elif st.session_state.current_page == "bots":
    show_bots_list()
elif st.session_state.current_page == "chat":
    show_chat_interface()
elif st.session_state.current_page == "import":
    show_import_page()

# Rodapé
st.markdown("---")
st.caption("🎭 CRINGE - Personagens Interativos | Desenvolvido com Streamlit & FastAPI")
