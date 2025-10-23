import streamlit as st
import requests
import json
import time
from typing import Optional, List, Dict, Any
import os

# --- Configuração Global ---

# Obtém a URL base da API (do ambiente ou usa o padrão local)
API_BASE_URL = os.environ.get("API_BASE_URL", "https://cringe-8h21.onrender.com")
BOTS_API_URL = f"{API_BASE_URL}/bots"
CHAT_API_URL = f"{API_BASE_URL}/bots/chat"

# Configuração da página Streamlit
st.set_page_config(
    page_title="CRINGE RPG-AI: V2.3 - Plataforma",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Definir estados de sessão iniciais
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'selection'
if 'selected_bot' not in st.session_state:
    st.session_state.selected_bot = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'available_bots' not in st.session_state:
    st.session_state.available_bots = []
if 'bots_loaded' not in st.session_state:
    st.session_state.bots_loaded = False


# --- Funções de API ---

@st.cache_data(ttl=300)
def fetch_bots() -> List[Dict[str, Any]]:
    """Busca a lista de bots da API de backend."""
    try:
        st.info(f"Tentando conectar em: {BOTS_API_URL}")
        response = requests.get(BOTS_API_URL, timeout=10)
        response.raise_for_status()  # Levanta erro para status 4xx/5xx
        bots_data = response.json()
        st.session_state.bots_loaded = True
        return bots_data
    except requests.exceptions.RequestException as e:
        st.error(f"Nenhum bot encontrado ou a API não está acessível. Verifique o backend. Erro: {e}")
        st.session_state.bots_loaded = True
        return []

def send_chat_message(bot_id: str, user_message: str, history: List[Dict[str, str]]) -> Optional[str]:
    """Envia a mensagem do usuário e o histórico para a API de chat."""
    try:
        payload = {
            "user_message": user_message,
            "chat_history": history
        }
        
        url = f"{CHAT_API_URL}/{bot_id}"
        
        with st.spinner("O Bot está pensando..."):
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("ai_response")
            
    except requests.exceptions.HTTPError as e:
        st.error(f"ERRO DE BACKEND: {e.response.status_code} - {e.response.reason}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"ERRO DE BACKEND: A chamada à API falhou. Erro: {e}")
        return None


# --- Funções de Navegação e Estado ---

def set_page(page_name: str, bot_data: Optional[Dict[str, Any]] = None):
    """Muda a página atual e o bot selecionado."""
    st.session_state.current_page = page_name
    if bot_data:
        st.session_state.selected_bot = bot_data
        st.session_state.chat_history = []  # Limpa o histórico ao iniciar novo chat
    else:
        st.session_state.selected_bot = None
    
    # CORRIGIDO: Substitui st.experimental_rerun() por st.rerun()
    st.rerun()

def load_bots_and_check():
    """Carrega os bots e atualiza o estado da sessão."""
    if not st.session_state.bots_loaded:
        bots = fetch_bots()
        st.session_state.available_bots = bots
        # O estado bots_loaded é definido dentro de fetch_bots()


# --- Views da Aplicação ---

def chat_page():
    """Página de conversação com o bot selecionado."""
    bot = st.session_state.selected_bot
    if not bot:
        st.error("Nenhum bot selecionado. Voltando para a seleção.")
        set_page('selection')
        return

    st.header(f"💬 Conversando com {bot['name']} ({bot['gender'] if bot['gender'] else 'Bot'})")
    st.markdown(f"**Personalidade:** {bot.get('personality', 'Sem descrição de personalidade.')}")

    # Botão Voltar
    if st.button("⬅️ Voltar para a Seleção de Bots"):
        set_page('selection')
        return

    # Mensagem de Boas-Vindas (se o histórico estiver vazio)
    if not st.session_state.chat_history:
        welcome_message = bot.get('welcome_message', "Olá! Como posso ajudar você hoje?")
        st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})

    # Exibir histórico de chat
    for message in st.session_state.chat_history:
        role = message["role"]
        content = message["content"]
        
        # O Streamlit usa 'user' e 'assistant' para formatar
        with st.chat_message(role):
            st.write(content)

    # Caixa de entrada de chat
    user_input = st.chat_input(f"Fale com {bot['name']}...")

    if user_input:
        # 1. Adiciona a mensagem do usuário ao histórico
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # 2. Exibe a mensagem do usuário
        with st.chat_message("user"):
            st.write(user_input)

        # 3. Prepara o histórico para a API (limitando os campos necessários)
        history_for_api = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in st.session_state.chat_history 
            if msg["role"] != "user" or msg["content"] != user_input # Exclui a mensagem atual do histórico para a API
        ]
        
        # 4. Chama a API
        ai_response = send_chat_message(
            bot_id=bot['id'], 
            user_message=user_input, 
            history=history_for_api
        )

        # 5. Adiciona e exibe a resposta da AI
        if ai_response:
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            with st.chat_message("assistant"):
                st.write(ai_response)
        
        # Após a resposta, força um novo rerun para exibir o estado atualizado
        # Não é estritamente necessário se o st.chat_input for a última coisa, 
        # mas garante a atualização visual
        # CORRIGIDO: Substitui st.experimental_rerun() por st.rerun()
        st.rerun()


def selection_page():
    """Página de seleção de bots."""
    st.title("© CringeBot - Seleção de Bots")
    
    # Carrega os bots na primeira execução
    load_bots_and_check()

    bots = st.session_state.available_bots

    if not bots:
        st.warning("Carregando bots ou falha na conexão. Verifique o status da API.")
        return

    st.subheader("Bots Existentes")
    
    for bot in bots:
        with st.container(border=True):
            col1, col2 = st.columns([1, 4])
            
            # Avatar
            with col1:
                if bot.get('avatar_url'):
                    # O Streamlit não tem um bom tratamento de erro para imagens, 
                    # então usamos um fallback simples (Nota: a imagem de erro no seu print 
                    # é um problema do seu URL, não do código)
                    st.image(
                        bot['avatar_url'], 
                        width=100, 
                        caption="Avatar",
                        use_column_width="always"
                    )
                else:
                    st.image("https://placehold.co/100x100/31333f/FFFFFF?text=BOT", width=100)
            
            # Dados do Bot
            with col2:
                st.subheader(f"{bot['name']} ({bot.get('gender', 'Bot')})")
                st.caption(f"ID: {bot['id']}")
                st.markdown(f"**Personalidade:** {bot.get('personality', 'N/A')}")
                
                # Botão Conversar
                if st.button(f"Conversar com {bot['name']} ({bot.get('gender', 'Bot')})", key=f"chat_{bot['id']}"):
                    set_page('chat', bot)


def create_bot_page():
    """Página para criar um novo bot."""
    st.header("✨ Criar Novo Bot")
    st.info("Preencha as informações do bot. Ao salvar, o bot será persistido no DB e poderá ser exportado.")
    
    # Implementação de criação de bot aqui...
    # Por enquanto, apenas um placeholder:
    st.warning("Funcionalidade de Criação de Bot não implementada nesta versão. Por favor, importe via JSON.")
    
    if st.button("⬅️ Voltar para a Seleção de Bots"):
        set_page('selection')

# --- Layout Principal ---

def main_page():
    """Função principal que renderiza o layout e o conteúdo da página."""
    
    # Barra Lateral
    with st.sidebar:
        st.subheader("Menu Principal")
        if st.session_state.current_page == 'selection':
            # st.experimental_rerun() para garantir que os bots sejam recarregados se a conexão falhar
            # CORRIGIDO: Substitui st.experimental_rerun() por st.rerun()
            if st.button("🔄 Recarregar Bots"):
                st.cache_data.clear() # Limpa o cache para forçar a busca
                st.session_state.bots_loaded = False
                st.rerun()

        if st.button("🏠 Seleção de Bots", key="nav_selection"):
            set_page('selection')
        if st.button("✨ Criar Bot", key="nav_create_bot"):
            set_page('create_bot')
        if st.button("📦 Importar Bots (DB)", key="nav_import_bot"):
            # Esta função provavelmente leva à função create_bot ou a uma nova página
            st.warning("Função Importar não implementada.")
            
        st.markdown("---")
        st.subheader("API BASE URL:")
        st.code(API_BASE_URL)
        st.markdown("_Altere a variável de ambiente_ `API_BASE_URL` _para mudar este endereço._")


    # Conteúdo Principal
    if st.session_state.current_page == 'selection':
        selection_page()
    elif st.session_state.current_page == 'chat':
        chat_page()
    elif st.session_state.current_page == 'create_bot':
        create_bot_page()

if __name__ == '__main__':
    main_page()

