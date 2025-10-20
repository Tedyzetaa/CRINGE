# Frontend.py (Streamlit)

import streamlit as st
import requests
import json
from typing import Optional, List, Dict, Any
from io import BytesIO

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
    
def api_put(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Função para fazer requisições PUT à API (útil para importação)."""
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.put(url, json=data)
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

# --- Funções de Importação e Exportação ---

def export_all_bots():
    """Busca todos os bots da API e retorna um arquivo JSON para download."""
    # Assume que a API tem um endpoint para listar todos os bots
    bots_data = api_get("bots/")
    
    if bots_data is None:
        st.error("Não foi possível carregar os dados dos bots para exportação.")
        return None

    # Envolve os dados no formato BotListFile (como definido no schemas)
    export_content = {"bots": bots_data}
    
    # Converte para string JSON formatada
    json_string = json.dumps(export_content, indent=4, ensure_ascii=False)
    
    # Retorna o conteúdo como BytesIO para o widget de download do Streamlit
    return BytesIO(json_string.encode('utf-8'))

def import_bots_from_json(uploaded_file):
    """Lê o arquivo JSON, envia para a API para importação e recarrega a UI."""
    if uploaded_file is not None:
        try:
            # 1. Lê o arquivo e carrega o JSON
            json_data = json.load(uploaded_file)
            
            # 2. Envia os dados para o endpoint de importação da API
            # Assume-se que o endpoint é 'bots/import' e usa o método PUT ou POST
            with st.spinner("Importando bots..."):
                # Usamos api_put, mas você pode mudar para api_post se preferir
                response = api_put("bots/import", json_data) 
            
            # 3. Verifica a resposta
            if response and response.get('success'):
                imported_count = response.get('imported_count', 0)
                st.success(f"Sucesso! {imported_count} bot(s) importado(s).")
                # Limpa o cache para garantir que a lista seja atualizada
                api_get.clear() 
                st.rerun()
            else:
                st.error(f"Falha na importação. Detalhes: {response.get('detail', 'Erro desconhecido da API')}")

        except json.JSONDecodeError:
            st.error("Erro: O arquivo não é um JSON válido.")
        except Exception as e:
            st.error(f"Ocorreu um erro durante o processamento do arquivo: {e}")

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
        # É importante limpar o cache de detalhes do bot para evitar erros de KeyError aqui
        bot_details = get_bot_details(bot_id)
        bot_name = bot_details['name'] if bot_details else "Bot"
        
        bot_response_text = response.get('bot_response', "Desculpe, não consegui responder.")
        
        st.session_state['chat_history'].append({
            "role": "bot", 
            "name": bot_name, 
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
            elif role == "bot":
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


    # --- Bloco de Importação e Exportação ---
    with st.expander("Importar/Exportar Bots", expanded=False):
        export_col, import_col = st.columns(2)
        
        with export_col:
            # Botão de Exportar
            export_file = export_all_bots()
            if export_file is not None:
                st.download_button(
                    label="⬇️ Exportar Todos os Bots (JSON)",
                    data=export_file,
                    file_name="cringebot_export.json",
                    mime="application/json",
                    use_container_width=True
                )
            else:
                st.warning("Não há dados de bots disponíveis para exportação.")
                
        with import_col:
            # Widget de Importar
            uploaded_file = st.file_uploader(
                "⬆️ Importar Bots (JSON)", 
                type=['json'], 
                key="bot_importer",
                help="Faça upload de um arquivo JSON contendo uma lista de bots.",
                accept_multiple_files=False
            )
            
            # Processa a importação após o upload
            if uploaded_file:
                import_bots_from_json(uploaded_file)
    # --- Fim do Bloco de Importação e Exportação ---


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
