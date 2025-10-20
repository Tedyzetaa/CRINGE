import streamlit as st
import requests
from typing import Optional, List, Dict, Any

# --- Configurações Iniciais ---
st.set_page_config(
    page_title="CringeBot - Interface Principal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 💡 URL do seu Backend FastAPI no Render. SUBSTITUA SE NECESSÁRIO.
# A URL do Render deve ser a base da sua API
API_BASE_URL = "https://cringe-8h21.onrender.com" 

# Inicializa o estado de sessão se necessário
if 'selected_bot_id' not in st.session_state:
    st.session_state['selected_bot_id'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'group_id' not in st.session_state:
    st.session_state['group_id'] = None


# --- Funções de Comunicação com a API ---

@st.cache_data(ttl=60)
def api_get(endpoint: str) -> Optional[List[Dict[str, Any]]]:
    """Função para fazer requisições GET à API."""
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        # st.error(f"Erro de comunicação com a API ({url}): {e}")
        return None

def api_post(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Função para fazer requisições POST à API."""
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.post(url, json=data)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de comunicação/HTTP com a API ({url}): {e}")
        return None

# Função auxiliar para buscar detalhes de um bot
@st.cache_data(ttl=60)
def get_bot_details(bot_id: str) -> Optional[Dict[str, Any]]:
    return api_get(f"bots/{bot_id}")

# --- Funções de Estado e Navegação ---

def select_bot_and_start_chat(bot_id: str):
    """Define o bot selecionado e limpa o histórico para um novo chat."""
    st.session_state['selected_bot_id'] = bot_id
    st.session_state['chat_history'] = []
    st.session_state['group_id'] = None # O ID do grupo/chat será criado no primeiro envio de mensagem
    # Limpa o cache para recarregar os dados do bot, se necessário
    get_bot_details.clear()
    st.rerun()

def exit_chat():
    """Volta para a tela de seleção de bots."""
    st.session_state['selected_bot_id'] = None
    st.session_state['chat_history'] = []
    st.session_state['group_id'] = None
    st.rerun()

# --- Componente de Envio de Mensagem (Chat) ---

def send_message(bot_id: str, message: str, player_id: str = "jogador_mock_id", player_name: str = "Jogador"):
    """
    Envia a mensagem para a API e recebe a resposta do Bot.
    """
    
    # 1. Adiciona a mensagem do usuário ao histórico (UI imediata)
    # Isso é feito ANTES de chamar a API para que o histórico inclua o contexto completo
    st.session_state['chat_history'].append({"role": "user", "name": player_name, "message": message})
    
    # 2. Prepara os dados para a API (CORREÇÃO DE FORMATO AQUI)
    
    # Mapeia o histórico do Streamlit (com 'message') para o modelo da API (com 'text')
    api_messages = []
    for chat_item in st.session_state['chat_history']:
        # Adiciona apenas 'role' e 'text' (o campo 'message' do Streamlit)
        api_messages.append({
            "role": chat_item['role'], 
            "text": chat_item['message']
        })
        
    data = {
        "bot_id": bot_id,
        # Envia o histórico formatado, conforme o modelo BotChatRequest do FastAPI
        "messages": api_messages
    }
    
    # 3. Faz o POST para a API
    with st.spinner("Bot pensando..."):
        # Endpoint groups/send_message
        response = api_post("groups/send_message", data)

    # 4. Processa a resposta da API
    # Note: O backend simulado não usa group_id, mas mantemos a lógica de UI
    if response and 'text' in response: # A resposta do backend é {"text": "..."}
        
        # O backend não tem group_id, mas a UI pode simular um se necessário.
        # Por enquanto, removemos a lógica de group_id para simplificar a dependência do backend
        
        # Adiciona a resposta do Bot ao histórico (Assumindo que a API retorna o texto em 'text')
        bot_response_text = response['text']
        
        st.session_state['chat_history'].append({
            "role": "model", 
            "name": get_bot_details(bot_id)['name'], 
            "message": bot_response_text
        })
        
    else:
        st.error(f"Falha na comunicação com o Bot.")
        # Remove a última mensagem do usuário se a comunicação falhou
        st.session_state['chat_history'].pop() 
        
    st.rerun() # Recarrega a UI para mostrar a nova mensagem

# --- Layout da Tela de Chat ---

def render_chat_screen(bot_id: str):
    """Interface principal de chat com o Bot selecionado."""
    bot = get_bot_details(bot_id)

    if not bot:
        st.error("Não foi possível carregar os detalhes do Bot. Volte para a seleção.")
        if st.button("Voltar", on_click=exit_chat): pass
        return

    # Cabeçalho do Chat
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("⬅️ Voltar", on_click=exit_chat): pass
    
    with col_title:
        st.header(f"Conversando com {bot['name']}")
    
    st.markdown(f"*{bot['introduction']}*")
    st.divider()

    # Área de Histórico de Conversa
    chat_container = st.container(height=500, border=True)

    with chat_container:
        # Exibe o histórico (incluindo a mensagem de boas-vindas inicial)
        if not st.session_state['chat_history']:
            st.info(f"Bem-vindo! {bot['name']} diz: *{bot['welcome_message']}*")

        for message_data in st.session_state['chat_history']:
            role = message_data['role']
            name = message_data['name']
            message = message_data['message']
            
            # Formatação baseada no papel
            if role == "user":
                with st.chat_message("user", avatar="👤"):
                    st.write(f"**{name}:** {message}")
            elif role == "model":
                avatar = bot.get('avatar_url', "🤖")
                with st.chat_message("assistant", avatar=avatar):
                    st.write(f"**{name}:** {message}")

    # Formulário de Envio de Mensagem
    with st.form(key='chat_form', clear_on_submit=True):
        user_input = st.text_input("Sua Mensagem:", placeholder="Digite aqui...")
        submit_button = st.form_submit_button("Enviar", use_container_width=True, type="primary")

    if submit_button and user_input:
        # Chama a função de envio
        send_message(bot_id, user_input)
        
    # Exibe o ID do grupo (se já criado) para fins de debug
    if st.session_state['group_id']:
        st.caption(f"ID do Chat (Grupo): {st.session_state['group_id']}")

# --- Layout da Tela de Seleção de Bots ---

def render_selection_screen():
    """Interface para selecionar Bots disponíveis."""
    
    st.title("🤖 CringeBot - Seleção de Bots")
    
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Bots Existentes")
        bots_data = api_get("bots/")
        
    with col2:
        st.write("") 
        # Botão que navega para a página de criação
        if st.button("➕ Criar Novo Bot", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Criar_Bot.py")


    if bots_data:
        st.subheader(f"Total de Bots: {len(bots_data)}")
        
        # Exibe os bots em um layout de cartões
        num_columns = 4
        cols = st.columns(num_columns)
        
        for i, bot in enumerate(bots_data):
            with cols[i % num_columns]:
                with st.container(border=True):
                    # 🖼️ Exibe o Avatar (usa a URL do campo novo)
                    avatar_url = bot.get('avatar_url')
                    if avatar_url:
                        st.image(avatar_url, width=100)
                    else:
                        st.image("https://via.placeholder.com/100x100?text=Bot", width=100)
                        
                    st.subheader(bot['name'])
                    st.markdown(f"**Gênero:** {bot['gender']}")
                    st.markdown(f"**Personalidade:** {bot['personality']}")
                    st.caption(bot['introduction'])
                    
                    tags = bot.get('tags', [])
                    if tags:
                        st.markdown(f"**Tags:** {', '.join(tags)}")
                        
                    # Botão para iniciar o chat
                    if st.button(f"Iniciar Chat", key=f"chat_{bot['id']}", use_container_width=True):
                        # Chama a função de seleção que muda o estado e executa o rerun
                        select_bot_and_start_chat(bot['id'])
    else:
        st.warning("Nenhum bot encontrado ou a API não está acessível. Verifique o backend.")


# --- Lógica de Renderização Principal ---

if st.session_state['selected_bot_id']:
    # Se um bot estiver selecionado, exibe a tela de chat
    render_chat_screen(st.session_state['selected_bot_id'])
else:
    # Caso contrário, exibe a tela de seleção de bots
    render_selection_screen()
