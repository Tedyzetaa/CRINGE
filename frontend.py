import streamlit as st
import requests
import json
import time
from typing import Optional, List, Dict, Any
import os

# --- Configuração Global ---

# Obtém a URL base da API (do ambiente ou usa o padrão local)
# Vamos usar uma chave de sessão para armazenar a URL base de forma dinâmica
if 'api_base_url' not in st.session_state:
    st.session_state.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

# As URLs da API são construídas com base no estado da sessão
BOTS_API_URL = f"{st.session_state.api_base_url}/bots"
CHAT_API_URL = f"{st.session_state.api_base_url}/bots/chat"

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

# O cache agora depende da API_BASE_URL para limpar o cache quando a URL muda
@st.cache_data(ttl=300)
def fetch_bots(api_base_url: str) -> List[Dict[str, Any]]:
    """Busca a lista de bots da API de backend."""
    # Recalculamos a URL dentro da função para que o cache_data use o argumento
    url = f"{api_base_url}/bots"
    try:
        st.info(f"Tentando conectar em: {url}")
        response = requests.get(url, timeout=10)
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
    # Usa a URL da API do estado da sessão
    url = f"{st.session_state.api_base_url}/bots/chat/{bot_id}"
    
    try:
        payload = {
            "user_message": user_message,
            "chat_history": history
        }
        
        with st.spinner("O Bot está pensando..."):
            # Aumentando o timeout para dar mais chance ao modelo de IA
            response = requests.post(url, json=payload, timeout=90) 
            response.raise_for_status()
            return response.json().get("ai_response")
            
    except requests.exceptions.HTTPError as e:
        st.error(f"ERRO DE BACKEND: {e.response.status_code} - {e.response.reason}")
        # Tenta mostrar o corpo do erro se possível
        try:
            error_body = e.response.json()
            st.code(json.dumps(error_body, indent=2))
        except:
            st.code(e.response.text)
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"ERRO DE BACKEND: A chamada à API falhou. Verifique se o backend está rodando em: {url}. Erro: {e}")
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
    
    st.rerun()

def load_bots_and_check():
    """Carrega os bots e atualiza o estado da sessão."""
    if not st.session_state.bots_loaded:
        # Passa a URL base como argumento
        bots = fetch_bots(st.session_state.api_base_url) 
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
        # Passa o histórico completo, exceto a última mensagem do usuário (que já está no input)
        history_for_api = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in st.session_state.chat_history 
            if not (msg["role"] == "user" and msg["content"] == user_input)
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
                    # então usamos um fallback simples
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
        st.subheader("Configuração da API")
        
        # Campo de entrada para a URL base da API
        new_api_url = st.text_input(
            "API Base URL:", 
            st.session_state.api_base_url, 
            key='api_url_input',
            help="Altere para 'http://localhost:8000' ou sua URL do Render."
        )

        # Atualiza o estado da sessão e força o rerun se a URL mudar
        if new_api_url != st.session_state.api_base_url:
            st.session_state.api_base_url = new_api_url
            st.cache_data.clear() # Limpa o cache para que a nova URL seja usada
            st.session_state.bots_loaded = False
            st.rerun()
            
        st.markdown("_Certifique-se de que o backend esteja rodando no endereço acima._")


    # Conteúdo Principal
    if st.session_state.current_page == 'selection':
        selection_page()
    elif st.session_state.current_page == 'chat':
        chat_page()
    elif st.session_state.current_page == 'create_bot':
        create_bot_page()

if __name__ == '__main__':
    main_page()
