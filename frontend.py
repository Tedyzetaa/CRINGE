# main.py (Frontend Streamlit)

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
# Assumindo que esta é a URL do seu backend no Render
API_BASE_URL = "https://cringe-8h21.onrender.com" 

# --- Funções de Comunicação com a API (CORRIGIDAS) ---

@st.cache_data(ttl=60)
def api_get(endpoint: str) -> Optional[List[Dict[str, Any]]]:
    """
    Função para fazer requisições GET à API.
    Nota: O Streamlit roda no frontend, a API no Render.
    """
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url)
        response.raise_for_status() # Lança exceção para status 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de comunicação com a API ({url}): {e}")
        return None

def api_post(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Função para fazer requisições POST à API.
    Nota: NÃO usamos cache para POSTs.
    """
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    st.info(f"Tentando POST para: {url} com dados: {data}")
    try:
        response = requests.post(url, json=data)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Erro da API ao criar o Bot (Status: {response.status_code}): {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de comunicação com a API: {e}")
        return None

# --- Layout da Página Principal ---

st.title("🤖 CringeBot - Seleção de Bots")

# Colunas para o cabeçalho e o botão
col1, col2 = st.columns([3, 1])

with col1:
    st.header("Bots Existentes")
    # Tenta carregar os bots do backend
    bots_data = api_get("bots/")
    
with col2:
    st.write("") # Espaçamento
    # Botão que navega para a página de criação
    if st.button("➕ Criar Novo Bot", use_container_width=True, type="primary"):
        # O Streamlit usa o sistema de arquivos para navegação.
        # Ele muda a URL para a página /1_Criar_Bot
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
                if bot.get('avatar_url'):
                    st.image(bot['avatar_url'], width=100)
                else:
                    # Ícone genérico se não houver URL
                    st.image("https://via.placeholder.com/100x100?text=Bot", width=100)
                    
                st.subheader(bot['name'])
                st.markdown(f"**Gênero:** {bot['gender']}")
                st.markdown(f"**Personalidade:** {bot['personality']}")
                st.caption(bot['introduction'])
                
                # Exibe as Tags (novo campo)
                tags = bot.get('tags', [])
                if tags:
                    st.markdown(f"**Tags:** {', '.join(tags)}")
                    
                # Botão de Ação (A ser implementado depois)
                if st.button(f"Iniciar Chat com {bot['name']}", key=f"chat_{bot['id']}", use_container_width=True):
                    st.session_state['selected_bot_id'] = bot['id']
                    st.success(f"Iniciando chat com {bot['name']} (Em desenvolvimento...)")

else:
    st.warning("Nenhum bot encontrado ou a API não está acessível. Tente recarregar a página.")