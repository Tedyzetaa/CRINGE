import streamlit as st
import requests
import json
import time
from typing import Optional, List, Dict, Any
import os
import pandas as pd

# --- Configuração Global PARA LOCAL ---
if 'api_base_url' not in st.session_state:
    st.session_state.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

# URLs da API
BOTS_API_URL = f"{st.session_state.api_base_url}/bots"
CHAT_API_URL = f"{st.session_state.api_base_url}/bots/chat"
IMPORT_API_URL = f"{st.session_state.api_base_url}/bots/import"

# Configuração da página
st.set_page_config(
    page_title="CRINGE RPG-AI: IMPORTADOR",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Estados de sessão
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
if 'import_result' not in st.session_state:
    st.session_state.import_result = None

# --- Funções de API ---
@st.cache_data(ttl=300)
def fetch_bots(api_base_url: str) -> List[Dict[str, Any]]:
    """Busca a lista de bots da API de backend."""
    url = f"{api_base_url}/bots"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        bots_data = response.json()
        st.session_state.bots_loaded = True
        return bots_data
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Backend não encontrado em: {url}")
        st.session_state.bots_loaded = True
        return []

def send_chat_message(bot_id: str, user_message: str, history: List[Dict[str, str]]) -> Optional[str]:
    """Envia mensagem para a API de chat."""
    url = f"{st.session_state.api_base_url}/bots/chat/{bot_id}"
    try:
        payload = {"user_message": user_message, "chat_history": history}
        with st.spinner("🤖 O Bot está pensando..."):
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("ai_response")
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao enviar mensagem: {e}")
        return None

def import_bots_from_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Importa bots via JSON para a API."""
    try:
        response = requests.post(IMPORT_API_URL, json=json_data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao importar bots: {e}")
        return {"success": False, "message": str(e)}

# --- Funções de Navegação ---
def set_page(page_name: str, bot_data: Optional[Dict[str, Any]] = None):
    st.session_state.current_page = page_name
    if bot_data:
        st.session_state.selected_bot = bot_data
        st.session_state.chat_history = []
    else:
        st.session_state.selected_bot = None
    st.rerun()

def load_bots_and_check():
    if not st.session_state.bots_loaded:
        bots = fetch_bots(st.session_state.api_base_url)
        st.session_state.available_bots = bots

# --- Páginas da Aplicação ---
def chat_page():
    bot = st.session_state.selected_bot
    if not bot:
        st.error("Nenhum bot selecionado.")
        set_page('selection')
        return

    st.header(f"💬 Conversando com {bot['name']}")
    st.markdown(f"**Personalidade:** {bot.get('personality', 'Sem descrição.')}")

    if st.button("⬅️ Voltar para a Seleção"):
        set_page('selection')
        return

    if not st.session_state.chat_history:
        welcome_message = bot.get('welcome_message', "Olá! Como posso ajudar?")
        st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_input = st.chat_input(f"Fale com {bot['name']}...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        history_for_api = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in st.session_state.chat_history 
            if not (msg["role"] == "user" and msg["content"] == user_input)
        ]
        
        ai_response = send_chat_message(bot['id'], user_input, history_for_api)
        if ai_response:
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            with st.chat_message("assistant"):
                st.write(ai_response)
        st.rerun()

def selection_page():
    st.title("© CringeBot - Bots Disponíveis")
    load_bots_and_check()
    bots = st.session_state.available_bots

    if not bots:
        st.warning("Nenhum bot encontrado. Importe bots via JSON na página de Importação.")
        return

    st.subheader(f"📊 {len(bots)} Bots Encontrados")
    
    for bot in bots:
        with st.container(border=True):
            col1, col2 = st.columns([1, 4])
            with col1:
                avatar = bot.get('avatar_url') or "https://placehold.co/100x100/31333f/FFFFFF?text=BOT"
                st.image(avatar, width=100, caption="Avatar")
            with col2:
                st.subheader(f"{bot['name']} ({bot.get('gender', 'Bot')})")
                st.caption(f"ID: {bot['id']}")
                st.markdown(f"**Personalidade:** {bot.get('personality', 'N/A')}")
                if st.button(f"Conversar com {bot['name']}", key=f"chat_{bot['id']}"):
                    set_page('chat', bot)

def import_bots_page():
    st.title("📥 Importar Bots via JSON")
    
    st.markdown("""
    ### Como importar bots:
    1. **Prepara seu JSON** no formato correto
    2. **Faz upload** do arquivo ou cola o conteúdo
    3. **Visualiza a prévia** dos bots
    4. **Confirma a importação**
    """)
    
    # Exemplo de JSON
    with st.expander("📋 Exemplo de Formato JSON"):
        st.code("""{
  "bots": [
    {
      "creator_id": "seu-user-id",
      "name": "Nome do Bot",
      "gender": "Gênero",
      "introduction": "Introdução...",
      "personality": "Personalidade...",
      "welcome_message": "Mensagem de boas-vindas",
      "avatar_url": "https://...",
      "tags": ["tag1", "tag2"],
      "conversation_context": "Contexto...",
      "context_images": "[]",
      "system_prompt": "Prompt do sistema...",
      "ai_config": {
        "temperature": 0.9,
        "max_output_tokens": 768
      }
    }
  ]
}""", language="json")
    
    # Upload de arquivo
    uploaded_file = st.file_uploader("Escolha um arquivo JSON", type=['json'])
    
    json_content = st.text_area("Ou cole o conteúdo JSON aqui:", height=300, 
                               placeholder='{"bots": [{...}]}')
    
    json_data = None
    bots_to_import = []
    
    # Processa o JSON
    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ Arquivo {uploaded_file.name} carregado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {e}")
    
    elif json_content.strip():
        try:
            json_data = json.loads(json_content)
            st.success("✅ JSON válido!")
        except Exception as e:
            st.error(f"❌ JSON inválido: {e}")
    
    # Mostra prévia dos bots
    if json_data and 'bots' in json_data:
        bots_to_import = json_data['bots']
        st.subheader(f"👁️ Prévia dos Bots ({len(bots_to_import)} encontrados)")
        
        for i, bot in enumerate(bots_to_import):
            with st.expander(f"Bot {i+1}: {bot.get('name', 'Sem nome')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Nome:**", bot.get('name', 'N/A'))
                    st.write("**Gênero:**", bot.get('gender', 'N/A'))
                    st.write("**Criador:**", bot.get('creator_id', 'N/A'))
                with col2:
                    st.write("**Tags:**", ", ".join(bot.get('tags', [])))
                    st.write("**Temperatura:**", bot.get('ai_config', {}).get('temperature', 'N/A'))
                
                st.write("**Personalidade:**", bot.get('personality', 'N/A')[:200] + "...")
        
        # Botão de importação
        if st.button("🚀 Importar Bots", type="primary", use_container_width=True):
            with st.spinner("Importando bots..."):
                result = import_bots_from_json(json_data)
                
                if result.get('success'):
                    st.success(f"✅ {result.get('message', 'Bots importados com sucesso!')}")
                    st.session_state.import_result = result
                    
                    # Mostra estatísticas
                    if 'imported' in result and 'failed' in result:
                        st.metric("Bots Importados", result['imported'])
                        if result['failed'] > 0:
                            st.metric("Falhas", result['failed'])
                    
                    # Limpa cache e recarrega bots
                    st.cache_data.clear()
                    st.session_state.bots_loaded = False
                    
                    # Opção para ver bots
                    if st.button("📋 Ver Bots Importados"):
                        set_page('selection')
                else:
                    st.error(f"❌ Falha na importação: {result.get('message', 'Erro desconhecido')}")
    
    elif json_data and 'bots' not in json_data:
        st.error("❌ Formato inválido: O JSON deve conter uma chave 'bots' com a lista de bots.")
    
    # Botão voltar
    if st.button("⬅️ Voltar para Seleção"):
        set_page('selection')

def main_page():
    with st.sidebar:
        st.subheader("🧭 Navegação")
        
        # Menu principal
        if st.button("🏠 Seleção de Bots", use_container_width=True):
            set_page('selection')
        if st.button("📥 Importar Bots", use_container_width=True):
            set_page('import_bots')
        
        st.markdown("---")
        st.subheader("🌐 Configuração")
        
        new_api_url = st.text_input(
            "URL do Backend:", 
            st.session_state.api_base_url,
            help="URL da API do backend"
        )

        if new_api_url != st.session_state.api_base_url:
            st.session_state.api_base_url = new_api_url
            st.cache_data.clear()
            st.session_state.bots_loaded = False
            st.rerun()
            
        # Status da conexão
        try:
            response = requests.get(f"{st.session_state.api_base_url}/", timeout=5)
            if response.status_code == 200:
                st.success("✅ Backend Online")
            else:
                st.error("❌ Backend com problemas")
        except:
            st.error("❌ Backend Offline")
        
        st.markdown("---")
        st.info(f"Bots carregados: {len(st.session_state.available_bots)}")

    # Renderiza página atual
    if st.session_state.current_page == 'selection':
        selection_page()
    elif st.session_state.current_page == 'chat':
        chat_page()
    elif st.session_state.current_page == 'import_bots':
        import_bots_page()

if __name__ == '__main__':
    main_page()