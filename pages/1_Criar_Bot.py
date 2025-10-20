# c:\cringe\3.0\pages\1_Criar_Bot.py (NOVO ARQUIVO)

import streamlit as st
import requests
import time
import json
from typing import Optional, List, Dict, Any
from io import BytesIO

# --- CONFIGURAÇÕES E FUNÇÕES REPETIDAS ---
# REUTILIZE a API_URL e as funções api_post / api_get
API_URL = "https://cringe-8h21.onrender.com"

# --- Funções de Comunicação com a API ---

# Reimplementação da api_get para esta página
@st.cache_data(ttl=60)
def api_get(endpoint: str) -> Optional[List[Dict[str, Any]]]:
    """Função para fazer requisições GET à API."""
    url = f"{API_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        # st.error(f"Erro de comunicação com a API ({url}): {e}")
        return None

def api_post(endpoint, payload):
    # Código da api_post (igual ao main.py)
    try:
        res = requests.post(f"{API_URL}/{endpoint}", json=payload)
        res.raise_for_status() 
        return res.json()
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Erro de Conexão: O backend em {API_URL} não está respondendo.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Erro HTTP: {e}")
        return None

def api_put(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Função para fazer requisições PUT à API (útil para importação)."""
    url = f"{API_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.put(url, json=data)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de comunicação/HTTP com a API ({url}): {e}")
        return None

# --- Funções de Importação e Exportação (Duplicadas da Home) ---

def export_all_bots():
    """Busca todos os bots da API e retorna um arquivo JSON para download."""
    bots_data = api_get("bots/")
    
    if bots_data is None:
        return None

    export_content = {"bots": bots_data}
    json_string = json.dumps(export_content, indent=4, ensure_ascii=False)
    
    return BytesIO(json_string.encode('utf-8'))

def import_bots_from_json(uploaded_file):
    """Lê o arquivo JSON, envia para a API para importação e recarrega a UI."""
    if uploaded_file is not None:
        try:
            # 1. Lê o arquivo e carrega o JSON
            json_data = json.load(uploaded_file)
            
            # 2. Envia os dados para o endpoint de importação da API
            with st.spinner("Importando bots..."):
                response = api_put("bots/import", json_data) 
            
            # 3. Verifica a resposta
            if response and response.get('success'):
                imported_count = response.get('imported_count', 0)
                st.success(f"Sucesso! {imported_count} bot(s) importado(s).")
                # Limpa o cache para garantir que a lista seja atualizada na próxima navegação
                api_get.clear() 
                # Simplesmente recarrega a página de criação para limpar o uploader
                time.sleep(1)
                st.rerun() 
            else:
                st.error(f"Falha na importação. Detalhes: {response.get('detail', 'Erro desconhecido da API')}")

        except json.JSONDecodeError:
            st.error("Erro: O arquivo não é um JSON válido.")
        except Exception as e:
            st.error(f"Ocorreu um erro durante o processamento do arquivo: {e}")


# --- FORMULÁRIO DE CRIAÇÃO ---

st.header("🤖 Criação Detalhada de Bot")
st.markdown("Use esta página para dar vida ao seu novo personagem de RPG.")

# 💡 Obter user_id do Jogador (Simplesmente forçamos o valor padrão ou você pode usar st.session_state)
# Nota: Em um app maior, você usaria st.session_state para passar o ID do jogador.
username = st.text_input("Seu Nome de Jogador (Necessário para criar o bot)", value="admin")
user_id = f"user-{username.lower().replace(' ', '-')}"

with st.form("bot_creation_form"):
    
    # Informações Básicas
    col1, col2 = st.columns(2)
    with col1:
        bot_name = st.text_input("Nome do Bot", placeholder="Ex: Professor Cartola")
        bot_gender = st.selectbox("Gênero", ["Masculino", "Feminino", "Não Binário", "Indefinido"])
    with col2:
        bot_avatar = st.text_input("Avatar URL (Link para imagem)", 
                                   placeholder="https://exemplo.com/avatar.png")
        bot_tags = st.text_input("Tags (Separadas por vírgula)", 
                                 placeholder="ex: Mago, Sarcástico, NPCs, Cômico")

    # Informações de Personalidade e Contexto
    st.subheader("Personalidade e História")
    bot_personality = st.text_area("Personalidade (Descrição de comportamento e traços)", 
                                   placeholder="Ex: Teimoso, adora enigmas, tem medo de aranhas.")
    
    bot_intro = st.text_area("Introdução/História (Pode ser o Lore do personagem)", 
                             placeholder="A história de como o bot surgiu no cenário.")
    
    bot_welcome = st.text_input("Mensagem de Boas-Vindas", 
                                 placeholder="Saudações, aventureiro!")

    # Configurações Avançadas da IA
    st.subheader("Configurações da IA (Sistema)")
    system_prompt = st.text_area("System Prompt (Instrução para o Modelo Gemini)", 
                                 placeholder=f"Você é {bot_name}, um bot com a personalidade descrita...")
    
    col3, col4 = st.columns(2)
    with col3:
        temperature = st.slider("Temperatura (Criatividade)", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
    with col4:
        max_tokens = st.slider("Max Output Tokens", min_value=128, max_value=4096, value=512, step=128)

    submitted = st.form_submit_button("✅ Salvar Bot")

    if submitted:
        if not bot_name or not bot_personality or not system_prompt:
            st.error("Por favor, preencha o Nome, Personalidade e System Prompt.")
        else:
            bot_payload = {
                "creator_id": user_id,
                "name": bot_name,
                "gender": bot_gender,
                "introduction": bot_intro,
                "personality": bot_personality,
                "welcome_message": bot_welcome,
                "avatar_url": bot_avatar, 
                "tags": [t.strip() for t in bot_tags.split(',')] if bot_tags else [],
                "conversation_context": "", 
                "context_images": "",  
                "system_prompt": system_prompt,
                "ai_config": {"temperature": temperature, "max_output_tokens": max_tokens}
            }
            
            if api_post("bots", bot_payload):
                st.success(f"Bot '{bot_name}' criado com sucesso!")
                time.sleep(1.5)
                # Redireciona de volta para a Home Page
                st.switch_page("frontend.py")
                # Caso o st.switch_page não funcione (versão Streamlit antiga):
                # st.info("Voltando para a Home Page em instantes...")
                # st.rerun() 


# --- Bloco de Importação e Exportação (Adicionado) ---
st.divider()
with st.expander("Importar/Exportar Bots", expanded=False):
    st.subheader("Gerenciamento de Dados")
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
            key="bot_importer_page", # Chave única para evitar conflito com a Home
            help="Faça upload de um arquivo JSON contendo uma lista de bots.",
            accept_multiple_files=False
        )
        
        # Processa a importação após o upload
        if uploaded_file:
            import_bots_from_json(uploaded_file)
# --- Fim do Bloco de Importação e Exportação ---
