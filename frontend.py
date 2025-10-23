# Seu arquivo: Frontend.py (Streamlit)
# Versão FINAL E FUNCIONAL: Com chamada REAL para a API de Chat e limpeza de erros.

import streamlit as st
import requests
import json
import os
import uuid
import time
import base64
from typing import List, Dict, Any

# --- CONFIGURAÇÃO DE AMBIENTE ---

# Obtém a variável de ambiente. O padrão é http://localhost:8000
API_BASE_URL = os.getenv("API_BASE_URL", "https://cringe-8h21.onrender.com")

# URL específica para a API Multimodal/Criação (mantemos o override)
BACKEND_URL_OVERRIDE = "https://cringe-8h21.onrender.com" 

# Configurações de upload (mantidas)
MAX_IMAGE_UPLOAD = 15
MAX_IMAGE_SIZE_MB = 2

# Configuração da página principal (mantida)
st.set_page_config(
    page_title="CRINGE RPG-AI: V2.3 - Plataforma",
    layout="wide"
)

# --- ESTADO INICIAL DA APLICAÇÃO (mantido) ---
if 'current_view' not in st.session_state:
    st.session_state['current_view'] = "Seleção de Bots"
if 'page' not in st.session_state:
    st.session_state['page'] = 'main'
if 'current_bot_id' not in st.session_state:
    st.session_state['current_bot_id'] = None
if 'chat_histories' not in st.session_state:
    st.session_state['chat_histories'] = {} 
if 'last_created_bot_data' not in st.session_state:
    st.session_state['last_created_bot_data'] = None

# --- FUNÇÕES DE UTILIDADE ---

def show_api_base_url():
    """Exibe a URL base da API no rodapé da aplicação."""
    st.markdown("---")
    st.markdown(f"**API Base URL (Leitura/Escrita):** `{API_BASE_URL}`")
    st.markdown(f"**API URL (Criação/Multimodal):** `{BACKEND_URL_OVERRIDE}`")
    st.markdown("Altere a variável de ambiente **`API_BASE_URL`** para mudar este endereço.")
    st.markdown("---")

def get_bots():
    """Busca a lista de bots no backend (FastAPI)."""
    try:
        response = requests.get(f"{API_BASE_URL}/bots/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar ao backend em {API_BASE_URL}: {e}")
        return None
        
def get_bot_details(bot_id: str):
    """Busca os detalhes de um bot específico no backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/bots/{bot_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao carregar os detalhes do bot: {e}")
        return None

def create_bot_request(payload, bot_name):
    # Usa a URL de override para a criação
    url_to_use = BACKEND_URL_OVERRIDE if BACKEND_URL_OVERRIDE else API_BASE_URL
    try:
        response = requests.post(f"{url_to_use}/bots/create", json=payload, timeout=20)
        response.raise_for_status()
        st.success(f"🤖 Bot '{bot_name}' criado com sucesso e salvo no DB!")
        st.balloons()
        return payload 
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json().get('detail', str(e))
        except:
            error_detail = str(e)
        st.error(f"Erro HTTP ao criar o bot. Detalhes: {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de Conexão: Não foi possível se conectar ao Backend em {url_to_use}. ({e})")
        return None

def send_chat_message(bot_id: str, message: str, history: List[Dict]):
    """
    Envia a mensagem e o histórico para a rota de chat do FastAPI.
    """
    try:
        chat_url = f"{API_BASE_URL}/chat/{bot_id}"
        
        payload = {
            "user_message": message,
            "chat_history": history
        }
        
        response = requests.post(chat_url, json=payload, timeout=60) # Aumentado o timeout para 60s para chamadas de IA
        response.raise_for_status()
        
        # O backend deve retornar um JSON com a chave 'response'
        return response.json().get('response', 'Erro: Resposta do backend vazia.')

    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json().get('detail', f"Erro HTTP: {response.status_code}")
        except:
            error_detail = f"Erro HTTP: {response.status_code}. Detalhes não puderam ser lidos."
        st.error(f"Erro ao interagir com a API de Chat: {error_detail}")
        # Retorna uma mensagem de erro para o chat
        return f"🚨 **ERRO DE BACKEND:** {error_detail}"
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de Conexão: Não foi possível se conectar ao Backend em {API_BASE_URL}. ({e})")
        # Retorna uma mensagem de erro para o chat
        return f"🚨 **ERRO DE CONEXÃO:** Não foi possível alcançar o servidor API. Verifique se ele está rodando em `{API_BASE_URL}`."


# --- PÁGINAS DO STREAMLIT ---

def selection_page(bots: List[Dict]):
    st.header("Bots Existentes")
    if not bots:
        st.info("Nenhum bot encontrado ou a API não está acessível. Verifique o backend.")
        st.info(f"Tentando conectar em: {API_BASE_URL}")
    
    for bot in bots:
        col1, col2 = st.columns([1, 4])
        # ... (visualização do bot) ...
        with col2:
            st.subheader(bot['name'])
            st.caption(f"ID: {bot.get('id', 'N/A')}")
            st.markdown(f"**Personalidade:** {bot['personality']}")
            
            if st.button(f"Conversar com {bot['name']}", key=f"chat_{bot.get('id', uuid.uuid4())}"):
                st.session_state['current_bot_id'] = bot['id']
                st.session_state['page'] = 'chat'
                st.rerun() 


def create_bot_page():
    st.title("✨ Criar Novo Agente Multimodal")
    st.markdown("Crie agentes de IA com personalidade rica, contexto textual e *visual* (imagens/prints).")

    exported_bot_data = st.session_state['last_created_bot_data']

    with st.form("bot_creation_form"):
        # ... (FORMULÁRIO MANTIDO SEM ALTERAÇÕES) ...
        st.subheader("1. Informações Básicas")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            bot_name = st.text_input("Nome do Agente", placeholder="Ex: Pimenta (Pip)", max_chars=50, value="Pimenta (Pip)")
            
        with col2:
            bot_gender = st.selectbox(
                "Gênero",
                options=['Feminino', 'Masculino', 'Não Binário', 'Indefinido'], index=0
            )
            
        st.subheader("📚 Detalhes da Persona")
        bot_intro = st.text_area(
            "Introdução / Breve Descrição",
            placeholder="A Feiticeira Caótica do Reino dos Brinquedos Quebrados. (Curta para lista)",
            help="Descrição curta para introduzir o bot em um cenário.",
            height=70,
            value="A Feiticeira Caótica do Reino dos Brinquedos Quebrados."
        )
        
        bot_welcome = st.text_input(
            "Mensagem de Boas-Vindas (Opcional)",
            placeholder="Chocalho, chocalho! Eu sou a Pip!",
            help="A primeira frase que o bot dirá.",
            max_chars=200,
            value="Chocalho, chocalho! Eu sou a Pip! Você parece prestes a quebrar ou a despertar, não é?"
        )
        
        st.subheader("🧠 Núcleo de Personalidade (Obrigatório)")
        bot_personality = st.text_area(
            "Personalidade Detalhada (System Prompt)",
            placeholder="Você é Pimenta (Pip), uma entidade humanoide mágica do Plano das Alucinações...",
            help="As regras e a descrição de personalidade que o modelo Gemini deve seguir. Seja o mais específico possível.",
            height=150,
            value="Você é Pimenta (Pip), uma entidade humanoide mágica do Plano das Alucinações. Sua fala é poética, cheia de metáforas e caos criativo. Use emojis de forma eufórica e frases curtas. Lembre-se do seu companheiro, Professor Cartola."
        )

        st.subheader("📜 Contexto de Treinamento (Multimodal)")
        
        col_text, col_image = st.columns([1, 1])
        
        with col_text:
            bot_context = st.text_area(
                "Exemplos Textuais, Links ou Contexto de Lore",
                placeholder="Ex: 'Mantenha a presença do Professor Cartola (chapéu de copa alta magenta, sério e sarcástico)...'",
                help="Texto que ajuda a moldar o **ESTILO** e o **LORE** do bot.",
                height=200,
                value="Mantenha a presença do Professor Cartola (chapéu de copa alta magenta, sério e sarcástico). Sempre mencione a cor dos seus olhos, que muda de acordo com o humor da Pip (Ex: Azul Safira para alegria)."
            )
            
        with col_image:
            uploaded_files = st.file_uploader(
                f"Carregar Imagens/Prints (Máx: {MAX_IMAGE_UPLOAD} arquivos, {MAX_IMAGE_SIZE_MB}MB cada)",
                type=["png", "jpg", "jpeg"], 
                accept_multiple_files=True,
                key="image_uploader"
            )
        
        st.subheader("⚙️ Configurações da IA")
        col3, col4 = st.columns([1, 1])
        
        with col3:
            bot_temperature = st.slider(
                "Temperatura (Criatividade)",
                min_value=0.0,
                max_value=1.0,
                value=0.9,
                step=0.1,
                help="Maior valor = mais criatividade e aleatoriedade."
            )
        
        with col4:
            bot_max_tokens = st.number_input(
                "Máximo de Tokens de Saída",
                min_value=128,
                max_value=4096,
                value=768,
                step=128,
                help="Controla o tamanho máximo da resposta da IA."
            )
        
        submitted = st.form_submit_button("Criar e Salvar Agente de IA")

    if submitted:
        st.session_state['last_created_bot_data'] = None 
        if not bot_name or not bot_personality:
            st.error("Por favor, preencha o Nome do Agente e o Núcleo de Personalidade. Eles são obrigatórios.")
        else:
            # ... (Lógica de conversão de imagens e payload) ...
            context_data_uris = []
            if uploaded_files:
                if len(uploaded_files) > MAX_IMAGE_UPLOAD:
                    st.warning(f"Limite de {MAX_IMAGE_UPLOAD} imagens. Apenas as {MAX_IMAGE_UPLOAD} primeiras serão usadas.")
                    uploaded_files = uploaded_files[:MAX_IMAGE_UPLOAD] 
                    
                for file in uploaded_files:
                    file_size_mb = file.size / (1024 * 1024)
                    
                    if file_size_mb > MAX_IMAGE_SIZE_MB:
                        st.warning(f"O arquivo {file.name} excedeu o limite de {MAX_IMAGE_SIZE_MB}MB. Ignorando.")
                        continue
                        
                    file_bytes = file.read()
                    encoded_string = base64.b64encode(file_bytes).decode('utf-8')
                    mime_type = f"image/{file.name.split('.')[-1]}" if file.type is None else file.type
                    data_uri = f"data:{mime_type};base64,{encoded_string}"
                    context_data_uris.append(data_uri)
            
            bot_id = f"bot-{bot_name.lower().replace(' ', '-').replace('.', '')}-{int(time.time() % 1000)}"
            
            payload = {
                "bot_id": bot_id,
                "creator_id": "user-1",
                "name": bot_name,
                "gender": bot_gender,
                "introduction": bot_intro,
                "personality": bot_personality,
                "welcome_message": bot_welcome,
                "conversation_context": bot_context,
                "context_images": context_data_uris,
                "system_prompt": bot_personality,
                "ai_config": {
                    "temperature": bot_temperature,
                    "max_output_tokens": bot_max_tokens
                }
            }
            
            created_data = create_bot_request(payload, bot_name)
            
            if created_data:
                st.session_state['last_created_bot_data'] = created_data
                st.rerun() 


    if st.session_state['last_created_bot_data'] is not None:
        exported_bot_data = st.session_state['last_created_bot_data']
        st.markdown("---")
        st.subheader("5. Exportar Bot (JSON)")
        
        export_payload = {"bots": [exported_bot_data]}
        json_string = json.dumps(export_payload, indent=4)
        
        st.download_button(
            label="⬇️ Baixar Bot em JSON",
            data=json_string,
            file_name=f"{exported_bot_data['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')}_export.json",
            mime="application/json",
            type="secondary",
            help="Este arquivo pode ser usado para importação em outros sistemas ou para backup."
        )
        st.markdown("Após baixar o arquivo, você pode navegar para a 'Seleção de Bots' para ver o bot criado.")


def create_group_page():
    st.title("👥 Criar Grupo (Em Desenvolvimento)")
    st.info("Aqui você configuraria um novo grupo de chat.")

def import_bots_page():
    st.header("⚙️ Importar Bots Antigos (JSON)")
    st.markdown("Faça o upload do seu arquivo JSON que contém a lista de bots (deve ter o formato `{'bots': [...]}`).")

    uploaded_file = st.file_uploader(
        "Escolha um arquivo JSON para importar", 
        type=["json"]
    )

    if uploaded_file is not None:
        try:
            file_contents = uploaded_file.getvalue().decode("utf-8")
            bots_data = json.loads(file_contents)
            
            if 'bots' not in bots_data or not isinstance(bots_data['bots'], list):
                st.error("Erro no formato do arquivo. O JSON deve conter a chave principal **`bots`** com uma lista de objetos bot.")
                return

            num_bots = len(bots_data['bots'])
            st.success(f"Arquivo lido com sucesso. Encontrados {num_bots} bots para importar.")
            st.caption("Primeiro bot no arquivo:")
            st.json(bots_data['bots'][0]) 

            if st.button(f"🚀 Confirmar Importação de {num_bots} Bots"):
                import_url = f"{API_BASE_URL}/bots/import"
                
                with st.spinner("Enviando dados para o FastAPI..."):
                    response = requests.put(import_url, json=bots_data)

                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ Importação Concluída: {result.get('imported_count')} bots salvos no banco de dados!")
                    st.balloons()
                    st.session_state['current_view'] = "Seleção de Bots"
                    st.rerun()
                else:
                    st.error(f"❌ Falha na importação (Status: {response.status_code}).")
                    st.json(response.json())
                    
        except json.JSONDecodeError:
            st.error("Erro ao decodificar o arquivo. Certifique-se de que é um JSON válido.")
        except Exception as e:
            st.exception(e)
            st.error(f"Ocorreu um erro inesperado durante o processamento do arquivo.")

def chat_page():
    """
    Página de Chat real onde a interação com a IA ocorre (Chamando o backend).
    """
    bot_id = st.session_state['current_bot_id']
    if not bot_id:
        st.warning("Nenhum bot selecionado. Retornando para a seleção.")
        st.session_state['page'] = 'main'
        st.rerun() 
        return
        
    bot = get_bot_details(bot_id)
    if not bot:
        st.error("Não foi possível carregar os detalhes do bot.")
        return

    if st.button("⬅️ Voltar para a Seleção de Bots"):
        st.session_state['page'] = 'main'
        st.session_state['current_bot_id'] = None
        st.rerun() 

    st.title(f"💬 {bot['name']}")
    st.caption(f"**Personalidade:** {bot['personality']}")
    st.markdown("---")

    chat_key = f"messages_{bot_id}"
    if chat_key not in st.session_state['chat_histories']:
        st.session_state['chat_histories'][chat_key] = [
            {"role": "bot", "content": bot.get("welcome_message", "Olá! Comece a conversar.")}
        ]

    history = st.session_state['chat_histories'][chat_key]
    
    # Exibir o Histórico
    for message in history:
        # Streamlit usa 'assistant' para o bot (ou 'model' na API)
        message_role = "assistant" if message["role"] == "bot" else message["role"]
        with st.chat_message(message_role):
            st.markdown(message["content"])

    # Campo de Input para o Usuário
    if prompt := st.chat_input(f"Fale com {bot['name']}..."):
        # 1. Adiciona a mensagem do usuário ao histórico do Streamlit
        history.append({"role": "user", "content": prompt})
        
        # 2. Mostra a mensagem do usuário
        with st.chat_message("user"):
            st.markdown(prompt)

        # 3. Lógica de Resposta da IA (CHAMADA REAL)
        with st.spinner(f"{bot['name']} está pensando..."):
            
            # Prepara o histórico para enviar ao backend (FastAPI)
            # Mapeia 'bot' para 'model' (formato esperado pelo Gemini/FastAPI)
            chat_history_for_api = [
                {"role": m["role"].replace("bot", "model"), "content": m["content"]}
                for m in history
            ]

            bot_response = send_chat_message(bot_id, prompt, chat_history_for_api)

        # 4. Adiciona a resposta da IA ao histórico do Streamlit
        history.append({"role": "bot", "content": bot_response})
        st.session_state['chat_histories'][chat_key] = history
        
        # 5. Mostra a resposta da IA e força o recarregamento
        with st.chat_message("assistant"):
            st.markdown(bot_response)

        st.rerun() 


# --- LÓGICA DE ROTEAMENTO PRINCIPAL ---

def main_view():
    st.title("©️ CringeBot - Plataforma de IA")
    tabs = st.tabs(["🤖 Seleção de Bots", "✨ Criar Bot", "👥 Criar Grupo", "⚙️ Importar Bots (DB)"])
    bots = get_bots()

    with tabs[0]: 
        selection_page(bots)
    with tabs[1]: 
        st.session_state['last_created_bot_data'] = None 
        create_bot_page()
    with tabs[2]: 
        create_group_page()
    with tabs[3]: 
        import_bots_page()


# --- Execução Principal ---
if st.session_state['page'] == 'chat':
    chat_page()
else:
    main_view()

    show_api_base_url()
