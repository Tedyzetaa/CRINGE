# frontend.py (COMPLETO COM A CORREÇÃO CRÍTICA: st.rerun() no lugar de st.experimental_rerun())

import streamlit as st
import requests
import json
import os
import time

# --- Variáveis de Configuração ---

# Tenta carregar a URL base da API (do ambiente ou usa localhost como fallback)
API_BASE_URL = os.getenv("API_BASE_URL", "https://cringe-8h21.onrender.com")

# --- Funções de API ---

@st.cache_data(ttl=60)
def api_get(endpoint: str):
    """Função genérica para fazer requisições GET à API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar à API: {e}")
        return None

def api_post(endpoint: str, data: dict):
    """Função genérica para fazer requisições POST à API."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Erro HTTP {e.response.status_code} na API: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar à API: {e}")
        return None

def api_put(endpoint: str, data: dict):
    """Função genérica para fazer requisições PUT à API."""
    try:
        response = requests.put(f"{API_BASE_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Erro HTTP {e.response.status_code} na API: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar à API: {e}")
        return None

# --- Páginas/Views do Streamlit ---

def selection_page(bots):
    st.header("🤖 CringeBot - Seleção de Bots")
    
    # Botão para criar novo bot
    if st.button("Criar Novo Bot", type="primary"):
        st.session_state.current_view = "create_bot"
        st.rerun() # CORREÇÃO: Usando st.rerun()

    st.divider()

    if not bots:
        st.warning(f"Nenhum bot encontrado ou a API não está acessível. Verifique o backend.")
        st.info(f"Tentando conectar em: {API_BASE_URL}/bots/")
        return

    st.subheader("Bots Existentes")
    
    cols = st.columns(4)
    for i, bot in enumerate(bots):
        with cols[i % 4]:
            st.markdown(f"**{bot['name']} ({bot['gender']})**")
            st.caption(bot.get('introduction', ''))
            
            # Botão para conversar com o bot
            if st.button(f"Conversar com {bot['name']} ({bot['gender']})", key=f"chat_{bot['id']}"):
                st.session_state.current_view = "chat_bot"
                st.session_state.selected_bot_id = bot['id']
                st.rerun() # CORREÇÃO: Usando st.rerun()

def chat_page(bot_id: str, bot_data: dict):
    st.title(f"Conversando com {bot_data['name']} ({bot_data['personality']})")
    st.caption(f"Personalidade: {bot_data['personality']}. {bot_data['introduction']}")
    
    if st.button("Voltar para a Seleção de Bots"):
        st.session_state.current_view = "selection_page"
        st.session_state.chat_history = []
        st.rerun() # CORREÇÃO: Usando st.rerun()

    # Inicializa o histórico de chat para o bot selecionado
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        # Adiciona a mensagem de boas-vindas do bot
        st.session_state.chat_history.append({"role": "bot", "content": bot_data['welcome_message']})

    # Exibe o histórico de chat
    for message in st.session_state.chat_history:
        role = "user" if message["role"] == "user" else "assistant"
        st.chat_message(role).write(message["content"])

    # Entrada de nova mensagem
    user_message = st.chat_input(f"Fale com {bot_data['name']} ({bot_data['personality']})...")

    if user_message:
        # 1. Adiciona a mensagem do usuário ao histórico
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        
        # 2. Exibe a mensagem do usuário imediatamente
        with st.chat_message("user"):
            st.write(user_message)

        # 3. Prepara a requisição para o backend
        history_for_api = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in st.session_state.chat_history if msg["role"] != "bot"
        ] # Exclui a mensagem de boas vindas, se necessário, ou ajusta a lógica de histórico

        request_payload = {
            "user_message": user_message,
            "chat_history": history_for_api
        }
        
        # 4. Chama o endpoint do backend
        with st.spinner(f"🤖 {bot_data['name']} está pensando..."):
            endpoint = f"/chat/{bot_id}"
            response_data = api_post(endpoint, request_payload)

        # 5. Processa a resposta
        if response_data and "response" in response_data:
            ai_response = response_data["response"]
        else:
            ai_response = "ERRO DE BACKEND: Resposta inválida ou nula."
            if response_data and "detail" in response_data:
                 ai_response = f"ERRO DE BACKEND: {response_data['detail']}"

        # 6. Adiciona e exibe a resposta do bot
        st.session_state.chat_history.append({"role": "bot", "content": ai_response})
        with st.chat_message("assistant"):
            st.write(ai_response)
        
        # A API é síncrona, então não precisa de rerun, mas em caso de erro, pode ser útil
        # st.rerun() # Removido para evitar piscar constante.

def create_bot_page():
    st.header("✨ Criar Novo Bot")
    st.info("Preencha as informações do bot. Ao salvar, o bot será persistido no DB e poderá ser exportado.")

    if st.button("Voltar para a Seleção de Bots"):
        st.session_state.current_view = "selection_page"
        st.rerun() # CORREÇÃO: Usando st.rerun()

    # Implementação dos formulários (simplificado)
    with st.form("bot_creation_form"):
        st.subheader("1. Identificação e Aparência")
        name = st.text_input("Nome do Bot", value="NovoBot")
        gender = st.selectbox("Gênero", ["Feminino", "Masculino", "Neutro"])
        creator_id = st.text_input("ID do Criador (Usuário)", value="user-default-id")
        avatar_url = st.text_input("URL do Avatar (imagem)", value="URL/padrao.png")

        st.subheader("2. Personalidade e Mensagens")
        introduction = st.text_area("Introdução (Descrição curta para a lista)", value="Um novo bot esperando para ser descoberto.")
        personality = st.text_area("Personalidade", value="Calmo, lógico e prestativo.")
        welcome_message = st.text_area("Mensagem de Boas-Vindas", value="Olá! Como posso ajudar?")
        system_prompt = st.text_area("System Prompt (Instrução para a IA)", value="Você é um assistente útil e amigável.")

        st.subheader("3. Configurações de IA")
        temperature = st.slider("Temperatura (Criatividade)", 0.0, 1.0, 0.7, 0.01)
        max_output_tokens = st.slider("Tokens Máximo de Saída", 128, 4096, 512, 128)
        
        # Campos Tags e Contexto (simplificado)
        tags_input = st.text_input("Tags (separadas por vírgula)", value="teste,novo")
        
        submitted = st.form_submit_button("Criar Bot")

        if submitted:
            tags_list = [t.strip() for t in tags_input.split(',')]
            
            bot_payload = {
                "creator_id": creator_id,
                "name": name,
                "gender": gender,
                "introduction": introduction,
                "personality": personality,
                "welcome_message": welcome_message,
                "avatar_url": avatar_url,
                "tags": tags_list,
                "conversation_context": "", # Não incluído no formulário simplificado
                "context_images": "", # Não incluído no formulário simplificado
                "system_prompt": system_prompt,
                "ai_config": {
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens
                }
            }

            response = api_post("/bots/", bot_payload)
            if response and "id" in response:
                st.success(f"Bot '{name}' criado com sucesso! ID: {response['id']}")
                st.session_state.current_view = "selection_page"
                st.rerun() # CORREÇÃO: Usando st.rerun()
            else:
                st.error("Falha ao criar o bot. Verifique o console do backend.")


def import_bots_page():
    st.header("Importar Bots (DB)")
    st.warning("Esta funcionalidade exige um arquivo JSON no formato esperado para importação em massa.")
    
    if st.button("Voltar para a Seleção de Bots"):
        st.session_state.current_view = "selection_page"
        st.rerun() # CORREÇÃO: Usando st.rerun()
        
    # --- Simulação de Importação de Arquivo (Você pode adaptar para o seu script) ---
    st.info("Para este frontend, a importação via API PUT é mais robusta.")
    
    uploaded_file = st.file_uploader("Escolha um arquivo JSON para Importar Bots", type=["json"])
    
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            
            # Garante que a estrutura principal seja a BotListFile
            if 'bots' not in data:
                st.error("O arquivo JSON deve conter uma chave principal chamada 'bots'.")
                return
            
            if st.button(f"Confirmar Importação de {len(data['bots'])} Bots"):
                with st.spinner("Importando bots para o banco de dados..."):
                    response = api_put("/bots/import", data)
                    
                if response and response.get('success'):
                    st.success(f"Importação concluída. {response.get('imported_count', 0)} bots importados/atualizados.")
                    st.session_state.current_view = "selection_page"
                    st.rerun() # CORREÇÃO: Usando st.rerun()
                else:
                    st.error(f"Falha na importação: {response.get('message', 'Erro desconhecido.')}")

        except json.JSONDecodeError:
            st.error("Erro: Arquivo JSON inválido.")
            
def create_group_page():
    st.header("Criar Grupo (Em Desenvolvimento)")
    st.info("Funcionalidade de chat em grupo a ser implementada.")
    
    if st.button("Voltar para a Seleção de Bots"):
        st.session_state.current_view = "selection_page"
        st.rerun() # CORREÇÃO: Usando st.rerun()

# --- Estrutura Principal da Aplicação ---

def main_view():
    st.set_page_config(
        page_title="CRINGE RPG-AI: V2.3 - Plataforma",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # 1. Inicializa o estado da sessão
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "selection_page"
    if 'selected_bot_id' not in st.session_state:
        st.session_state.selected_bot_id = None
        
    # 2. Sidebar de Navegação
    with st.sidebar:
        st.title("frontend")
        st.divider()

        # Seleção de Páginas
        st.subheader("Menu Principal")
        if st.button("Seleção de Bots", key="nav_select"):
            st.session_state.current_view = "selection_page"
            st.rerun() # CORREÇÃO: Usando st.rerun()
        if st.button("Criar Bot", key="nav_create"):
            st.session_state.current_view = "create_bot"
            st.rerun() # CORREÇÃO: Usando st.rerun()
        if st.button("Criar Grupo", key="nav_group"):
            st.session_state.current_view = "create_group"
            st.rerun() # CORREÇÃO: Usando st.rerun()
        if st.button("Importar Bots (DB)", key="nav_import"):
            st.session_state.current_view = "import_bots"
            st.rerun() # CORREÇÃO: Usando st.rerun()
            
        st.divider()
        st.subheader("API Base URL:")
        st.markdown(f"[{API_BASE_URL}](http://localhost:8000)")
        st.caption("Altere a variável de ambiente `API_BASE_URL` para mudar este endereço.")


    # 3. Renderiza o conteúdo principal
    if st.session_state.current_view == "selection_page":
        # Chama a API para obter a lista de bots
        bots = api_get("/bots/")
        if bots is not None:
            selection_page(bots)
        else:
            selection_page(None) # Exibe a mensagem de erro da API
            
    elif st.session_state.current_view == "chat_bot" and st.session_state.selected_bot_id:
        bot_data = api_get(f"/bots/{st.session_state.selected_bot_id}")
        if bot_data:
            chat_page(st.session_state.selected_bot_id, bot_data)
        else:
            st.error("Bot não encontrado no backend. Voltando para a seleção.")
            st.session_state.current_view = "selection_page"
            st.session_state.selected_bot_id = None
            st.rerun() # CORREÇÃO: Usando st.rerun()

    elif st.session_state.current_view == "create_bot":
        create_bot_page()
        
    elif st.session_state.current_view == "create_group":
        create_group_page()

    elif st.session_state.current_view == "import_bots":
        import_bots_page()

if __name__ == "__main__":
    main_view()

