# Frontend.py (Streamlit)

import streamlit as st
import requests
import os # Importação necessária para acessar variáveis de ambiente
from typing import Optional, List, Dict, Any

# --- Configurações Iniciais ---
st.set_page_config(
    page_title="CringeBot - Interface Principal",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 💡 CORREÇÃO: Usar variável de ambiente para API_BASE_URL
# O valor padrão é a URL que você usava, mas agora ele respeita o que for configurado no ambiente.
API_BASE_URL = os.getenv("API_BASE_URL", "https://cringe-8h21.onrender.com")

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
        # Melhoria no feedback de erro na barra lateral
        st.sidebar.error(f"Erro de comunicação com API: {url}")
        st.sidebar.caption(f"Detalhes: {e}")
        return None

def api_post(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Função para fazer requisições POST à API."""
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.post(url, json=data)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        # Mantém o erro na tela principal, mas adiciona detalhes na sidebar
        st.error(f"Erro de comunicação/HTTP com a API ({url}): {e}")
        st.sidebar.error("Falha ao enviar POST.")
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
    
    A API precisará:
    1. Se group_id for None, criar um novo grupo (chat) usando o bot_id e o player_id.
    2. Enviar a mensagem para o grupo/bot e receber a resposta.
    """
    
    # 1. Adiciona a mensagem do usuário ao histórico (UI imediata)
    st.session_state['chat_history'].append({"role": "user", "name": player_name, "message": message})
    
    # 2. Prepara os dados para a API
    # Assumindo que a API tem um endpoint que gerencia a criação/envio de mensagem
    data = {
        "bot_id": bot_id,
        "group_id": st.session_state['group_id'], # Pode ser None na primeira mensagem
        "player_id": player_id,
        "message_text": message
    }
    
    # 3. Faz o POST para a API
    with st.spinner("Bot pensando..."):
        # Endpoint simulado: groups/send_message
        # Você deve ter esta rota criada no seu backend FastAPI
        response = api_post("groups/send_message", data)

    # 4. Processa a resposta da API
    if response and response.get('success'):
        # Atualiza o group_id se for a primeira mensagem e um novo grupo foi criado
        if st.session_state['group_id'] is None:
            st.session_state['group_id'] = response.get('group_id')
            
        # Adiciona a resposta do Bot ao histórico (Assumindo que a API retorna o texto da resposta)
        bot_response_text = response.get('bot_response', "Desculpe, não consegui responder.")
        
        st.session_state['chat_history'].append({
            "role": "bot", 
            "name": get_bot_details(bot_id)['name'], 
            "message": bot_response_text
        })
        
    else:
        # Se falhar, e for a primeira mensagem, o group_id permanece None
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
        # Use o key para garantir que o botão não cause colisões
        if st.button("⬅️ Voltar", on_click=exit_chat, key="chat_back_button"): pass
    
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
            elif role == "bot":
                avatar = bot.get('avatar_url', "🤖")
                # Garante que o avatar do bot seja um ícone/emoji se a URL for inválida
                display_avatar = avatar if (avatar and avatar.startswith("http")) else "🤖"
                with st.chat_message("assistant", avatar=display_avatar):
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
            # st.switch_page("pages/1_Criar_Bot.py") # Descomente e ajuste se usar Multi-Page App
            st.warning("A navegação para Criar Bot requer um Streamlit Multi-Page App. Por enquanto, a função está desabilitada.")


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
                    if avatar_url and avatar_url.startswith("http"):
                        st.image(avatar_url, width=100)
                    else:
                        st.image("https://via.placeholder.com/100x100?text=Bot", width=100)
                        
                    st.subheader(bot['name'])
                    st.markdown(f"**Gênero:** {bot['gender']}")
                    # Exibindo a introdução em vez da personalidade (mais amigável para a lista)
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
        st.caption(f"Tentando conectar em: {API_BASE_URL}")


# --- Lógica de Renderização Principal ---

# Exibe o URL da API na barra lateral para debug
with st.sidebar:
    st.markdown("---")
    st.caption(f"API Base URL: {API_BASE_URL}")
    st.caption("Altere a variável de ambiente `API_BASE_URL` para mudar este endereço.")
    st.markdown("---")


if st.session_state['selected_bot_id']:
    # Se um bot estiver selecionado, exibe a tela de chat
    render_chat_screen(st.session_state['selected_bot_id'])
else:
    # Caso contrário, exibe a tela de seleção de bots
    render_selection_screen()
