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
API_URL = "https://cringe-5jmi.onrender.com"

# Inicialização do session_state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"
if 'current_bot' not in st.session_state:
    st.session_state.current_bot = None
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'widget_counter' not in st.session_state:
    st.session_state.widget_counter = 0

def get_unique_key(prefix="widget"):
    """Gera uma chave única para widgets"""
    st.session_state.widget_counter += 1
    return f"{prefix}_{st.session_state.widget_counter}"

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

def delete_bot(bot_id: str):
    """Exclui um bot"""
    try:
        response = requests.delete(f"{API_URL}/bots/{bot_id}")
        if response.status_code == 200:
            st.success("✅ Bot excluído com sucesso!")
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
        response = requests.post(f"{API_URL}/bots/chat/{bot_id}", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro ao enviar mensagem: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None

def import_bots(bots_data: Dict):
    """Importa bots via JSON"""
    try:
        response = requests.post(f"{API_URL}/bots/import", json=bots_data, timeout=30)
        
        if response.status_code == 200:
            return True, response.json().get('message', 'Importação realizada com sucesso!')
        else:
            error_detail = response.json().get('detail', 'Erro desconhecido')
            return False, f"Erro: {error_detail}"
    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"

# Componentes da UI
def show_chat_interface():
    """Interface de chat com o bot - CORRIGIDA"""
    if not st.session_state.current_bot:
        st.error("❌ Nenhum bot selecionado para conversar")
        if st.button("🏠 Voltar para Início", key=get_unique_key("back_from_no_bot")):
            st.session_state.current_page = "home"
            st.rerun()
        return
    
    bot = st.session_state.current_bot
    
    # Header do chat
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title(f"💬 {bot['name']}")
    with col2:
        if st.button("🏠 Início", key=get_unique_key("back_home"), use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    with col3:
        if st.button("🤖 Personagens", key=get_unique_key("back_bots"), use_container_width=True):
            st.session_state.current_page = "bots"
            st.rerun()
    
    st.markdown(f"*{bot['introduction']}*")
    st.markdown("---")
    
    # Inicializar conversa se necessário
    if bot['id'] not in st.session_state.conversations:
        st.session_state.conversations[bot['id']] = {
            'conversation_id': None,
            'messages': []
        }
    
    # Exibir mensagem de boas-vindas se não houver mensagens
    current_conversation = st.session_state.conversations[bot['id']]
    if not current_conversation['messages']:
        with st.chat_message("assistant"):
            st.write(bot['welcome_message'])
        current_conversation['messages'].append({
            'content': bot['welcome_message'],
            'is_user': False
        })
    
    # Exibir histórico de mensagens
    for msg in current_conversation['messages']:
        if msg['is_user']:
            with st.chat_message("user"):
                st.write(msg['content'])
        else:
            with st.chat_message("assistant"):
                st.write(msg['content'])
    
    # Input de mensagem usando st.chat_input (mais moderno)
    user_message = st.chat_input("Digite sua mensagem...", key=get_unique_key("chat_input"))
    
    if user_message and user_message.strip():
        # Adicionar mensagem do usuário ao histórico
        current_conversation['messages'].append({
            'content': user_message,
            'is_user': True
        })
        
        # Obter resposta do bot
        with st.spinner(f"{bot['name']} está pensando..."):
            response = chat_with_bot(
                bot['id'], 
                user_message, 
                current_conversation['conversation_id']
            )
            
            if response:
                # Atualizar conversation_id
                current_conversation['conversation_id'] = response['conversation_id']
                
                # Adicionar resposta do bot
                current_conversation['messages'].append({
                    'content': response['response'],
                    'is_user': False
                })
                
                st.rerun()

def show_bots_list():
    """Página de listagem de bots"""
    st.title("🤖 Meus Personagens")
    st.markdown("---")
    
    # Carregar bots
    bots = load_bots_from_db()
    
    if not bots:
        st.info("""
        🎭 **Nenhum personagem encontrado!**
        
        Os personagens padrão devem ser carregados automaticamente.
        Se você está vendo esta mensagem, verifique se o backend está funcionando.
        """)
        
        # Botão para verificar status
        if st.button("🔄 Verificar Status do Sistema", key=get_unique_key("check_status")):
            try:
                health = requests.get(f"{API_URL}/health")
                if health.status_code == 200:
                    health_data = health.json()
                    st.success(f"✅ API Online - {health_data.get('statistics', {}).get('bots', 0)} bots no sistema")
                else:
                    st.error(f"❌ API com problemas: {health.status_code}")
            except Exception as e:
                st.error(f"💥 Erro de conexão: {e}")
        return
    
    # Lista de bots
    for i, bot in enumerate(bots):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Avatar e informações básicas
                col_avatar, col_info = st.columns([1, 4])
                with col_avatar:
                    st.image(bot['avatar_url'], width=80)
                with col_info:
                    st.subheader(bot['name'])
                    st.write(f"*{bot['introduction']}*")
                    st.caption(f"**Personalidade:** {bot['personality']}")
                    
                    # Tags
                    if bot['tags']:
                        tags_text = " ".join([f"`{tag}`" for tag in bot['tags']])
                        st.caption(f"**Tags:** {tags_text}")
            
            with col2:
                if st.button("💬 Conversar", key=f"chat_{bot['id']}_{i}", use_container_width=True):
                    st.session_state.current_bot = bot
                    st.session_state.current_page = "chat"
                    st.rerun()
            
            with col3:
                # Não permitir excluir bots do sistema
                if bot.get('creator_id') != 'system':
                    if st.button("🗑️ Excluir", key=f"delete_{bot['id']}_{i}", use_container_width=True, type="secondary"):
                        if st.button(f"✅ Confirmar exclusão de {bot['name']}", key=f"confirm_delete_{bot['id']}"):
                            delete_bot(bot['id'])
                else:
                    st.caption("🔒 Bot do sistema")
            
            st.markdown("---")

def show_import_page():
    """Página de importação de bots"""
    st.title("📥 Importar Personagens")
    st.markdown("---")
    
    # Status da API
    try:
        health = requests.get(f"{API_URL}/health")
        if health.status_code == 200:
            health_data = health.json()
            st.success(f"✅ API Online - {health_data.get('statistics', {}).get('bots', 0)} bots no sistema")
        else:
            st.error(f"❌ API com problemas: {health.status_code}")
    except Exception as e:
        st.error(f"💥 Erro de conexão: {e}")
    
    st.markdown("---")
    
    # Área para colar JSON manualmente
    st.subheader("📝 Cole o JSON aqui")
    json_input = st.text_area(
        "Cole o conteúdo JSON dos personagens:",
        height=300,
        key=get_unique_key("json_input"),
        placeholder='{"bots": [{"creator_id": "user", "name": "Nome", ...}]}'
    )
    
    # JSON de exemplo
    json_exemplo = '''{
  "bots": [
    {
      "creator_id": "user",
      "name": "Meu Personagem",
      "gender": "Feminino",
      "introduction": "Um personagem personalizado",
      "personality": "Amigável e curioso",
      "welcome_message": "Olá! Sou seu novo personagem! 👋",
      "avatar_url": "https://i.imgur.com/07kI9Qh.jpeg",
      "tags": ["personalizado", "amigável"],
      "conversation_context": "Contexto personalizado",
      "context_images": "[]",
      "system_prompt": "Você é um personagem personalizado criado pelo usuário.",
      "ai_config": {
        "temperature": 0.7,
        "max_output_tokens": 500
      }
    }
  ]
}'''
    
    # Botão para usar exemplo
    if st.button("📋 Usar Exemplo", key=get_unique_key("use_example")):
        st.session_state[get_unique_key("json_input")] = json_exemplo
        st.rerun()
    
    # Botão de importação
    if st.button("🚀 IMPORTAR PERSONAGENS", type="primary", key=get_unique_key("import_button")):
        if json_input.strip():
            try:
                bots_data = json.loads(json_input)
                
                # Validar estrutura
                if "bots" not in bots_data:
                    st.error("❌ Estrutura inválida: falta a chave 'bots'")
                elif not isinstance(bots_data["bots"], list):
                    st.error("❌ Estrutura inválida: 'bots' deve ser uma lista")
                elif len(bots_data["bots"]) == 0:
                    st.error("❌ Nenhum personagem encontrado no JSON")
                else:
                    st.info(f"📋 Encontrados {len(bots_data['bots'])} personagem(s)")
                    
                    # Mostrar preview
                    with st.expander("👀 Visualizar Personagens"):
                        for i, bot in enumerate(bots_data["bots"][:3]):
                            st.write(f"**{i+1}. {bot.get('name', 'Sem nome')}**")
                            st.write(f"   {bot.get('introduction', 'Sem descrição')}")
                    
                    # Importar
                    with st.spinner("Importando personagens..."):
                        success, message = import_bots(bots_data)
                        
                    if success:
                        st.success(f"🎉 {message}")
                        st.balloons()
                        st.info("✅ Importação concluída! Verifique a lista de personagens.")
                    else:
                        st.error(f"❌ {message}")
                        
            except json.JSONDecodeError as e:
                st.error(f"❌ Erro no JSON: {str(e)}")
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")
        else:
            st.warning("⚠️ Cole o JSON no campo acima")
    
    st.markdown("---")
    
    # Informação sobre bots do sistema
    st.info("""
    **💡 Informação:** 
    - Os 4 personagens padrão (Pimenta, Zimbrak, Luma, Tiko) já estão pré-carregados no sistema
    - Use esta página para importar personagens adicionais ou personalizados
    - Bots do sistema não podem ser excluídos
    """)

def show_home_page():
    """Página inicial"""
    st.title("🎭 CRINGE - Personagens Interativos")
    st.markdown("---")
    
    # Carregar bots
    bots = load_bots_from_db()
    
    # Cards de estatísticas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Personagens Cadastrados", len(bots))
    
    with col2:
        active_conversations = len([conv for conv in st.session_state.conversations.values() if conv['messages']])
        st.metric("Conversas Ativas", active_conversations)
    
    with col3:
        total_messages = sum(len(conv['messages']) for conv in st.session_state.conversations.values())
        st.metric("Mensagens Trocadas", total_messages)
    
    st.markdown("---")
    
    # Botões de ação principais
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🤖 Ver Personagens", key=get_unique_key("view_bots"), use_container_width=True):
            st.session_state.current_page = "bots"
            st.rerun()
    
    with col2:
        if st.button("📥 Importar", key=get_unique_key("import_home"), use_container_width=True):
            st.session_state.current_page = "import"
            st.rerun()
    
    st.markdown("---")
    
    # Personagens disponíveis
    if bots:
        st.subheader("🚀 Personagens Disponíveis")
        
        # Mostrar bots em cards
        cols = st.columns(min(3, len(bots)))
        for idx, bot in enumerate(bots[:3]):
            with cols[idx]:
                with st.container():
                    st.image(bot['avatar_url'], use_column_width=True)
                    st.subheader(bot['name'])
                    st.write(bot['introduction'])
                    if st.button(f"💬 Conversar com {bot['name']}", key=f"home_chat_{bot['id']}_{idx}"):
                        st.session_state.current_bot = bot
                        st.session_state.current_page = "chat"
                        st.rerun()
        
        if len(bots) > 3:
            if st.button("📋 Ver Todos os Personagens →", key=get_unique_key("view_all_bots")):
                st.session_state.current_page = "bots"
                st.rerun()
    else:
        # Mensagem quando não há bots
        st.info("""
        ## 🎉 Bem-vindo ao CRINGE!
        
        **Personagens Interativos com Personalidades Únicas**
        
        Para começar, verifique se o sistema está carregado corretamente.
        Os personagens padrão devem aparecer automaticamente.
        
        *Personagens incluídos: Pimenta, Zimbrak, Luma e Tiko!*
        """)

# Barra lateral de navegação
with st.sidebar:
    st.title("🎭 CRINGE")
    st.markdown("---")
    
    # Navegação
    page_options = {
        "🏠 Início": "home",
        "🤖 Personagens": "bots", 
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
    
    # Se estiver em uma conversa, mostrar botão para voltar ao chat
    if st.session_state.current_page == "chat" and st.session_state.current_bot:
        if st.button("💬 Voltar ao Chat", key=get_unique_key("back_to_chat"), use_container_width=True):
            st.session_state.current_page = "chat"
            st.rerun()
    
    st.markdown("---")
    
    # Informações do sistema
    st.subheader("🔍 Status do Sistema")
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            st.success("✅ API Online")
            
            # Mostrar estatísticas
            stats = health_data.get('statistics', {})
            st.caption(f"**Bots:** {stats.get('bots', 0)}")
            st.caption(f"**Conversas:** {stats.get('conversations', 0)}")
            st.caption(f"**Mensagens:** {stats.get('messages', 0)}")
            
        else:
            st.error(f"❌ API Offline - Status {health_response.status_code}")
    except Exception as e:
        st.error(f"❌ Erro de conexão: {str(e)}")
    
    st.markdown("---")
    
    # Botão de limpar conversas locais
    if st.button("🗑️ Limpar Conversas Locais", key=get_unique_key("clear_local_chats")):
        st.session_state.conversations = {}
        st.success("✅ Conversas locais limpas!")
        st.rerun()
    
    # Debug info
    with st.expander("🔧 Debug Info"):
        st.write(f"Página atual: {st.session_state.current_page}")
        st.write(f"Bot atual: {st.session_state.current_bot['name'] if st.session_state.current_bot else 'Nenhum'}")
        st.write(f"Conversas: {len(st.session_state.conversations)}")

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
