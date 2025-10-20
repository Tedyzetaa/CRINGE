import streamlit as st
import httpx
import os
from typing import List, Dict, Any, Optional
import uuid # <-- CORREÇÃO: Mover a importação para o topo para uso em layout_criar_bot

# --- CONFIGURAÇÃO E VARIÁVEIS DE AMBIENTE ---
# CRÍTICO: Usa a variável de ambiente para determinar o URL do backend.
# O Streamlit DEVE ser configurado com esta variável (API_BASE_URL) para funcionar.
API_BASE_URL = os.getenv("API_BASE_URL", "https://cringe-8h21.onrender.com")
HTTP_CLIENT = httpx.Client(timeout=30.0)

# --- MODELOS DE DADOS SIMPLIFICADOS (Para tipagem local) ---
class Bot:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.name = data.get("name")
        self.gender = data.get("gender")
        self.introduction = data.get("introduction")
        self.personality = data.get("personality")
        self.welcome_message = data.get("welcome_message")
        self.avatar_url = data.get("avatar_url")
        self.tags = data.get("tags", [])
        self.system_prompt = data.get("system_prompt")
        self.ai_config = data.get("ai_config", {})

# --- FUNÇÕES DE API ---

@st.cache_data(ttl=60) # Cache para evitar chamadas repetitivas
def fetch_bots() -> List[Bot]:
    """Busca a lista de todos os bots do backend FastAPI."""
    try:
        response = HTTP_CLIENT.get(f"{API_BASE_URL}/bots/")
        response.raise_for_status()
        bot_list_data = response.json()
        return [Bot(data) for data in bot_list_data]
    except httpx.ConnectError as e:
        # Erro mais comum no Canvas: API não acessível ou URL incorreta
        st.error("❌ **Erro ao carregar bots do backend.**")
        
        # Mensagem de erro aprimorada para o ambiente Canvas
        st.caption(f"""
            **Endereço da API:** {API_BASE_URL}
            O Frontend não conseguiu se conectar. Se você estiver no Canvas, a causa é quase sempre:
            1. O Backend FastAPI não está rodando.
            2. A **Variável de Ambiente `API_BASE_URL`** no Streamlit está incorreta (deve ser o URL público do Render, não `localhost`).
            Detalhes: {e}
        """)
        return []
    except httpx.HTTPStatusError as e:
        st.error(f"❌ Erro HTTP ao buscar bots (Status: {e.response.status_code}). Verifique logs do FastAPI.")
        st.caption(f"Detalhes: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Erro inesperado ao carregar bots: {e}")
        return []

def send_chat_message(bot_id: str, messages: List[Dict[str, str]]) -> Dict[str, str]:
    """Envia uma mensagem de chat e retorna o task_id para polling."""
    try:
        payload = {
            "bot_id": bot_id,
            # Garantimos que a lista de mensagens tenha o formato correto para o FastAPI
            "messages": [{"role": msg["role"], "text": msg["text"]} for msg in messages]
        }
        
        response = HTTP_CLIENT.post(f"{API_BASE_URL}/groups/send_message", json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"❌ Erro ao enviar mensagem (Status: {e.response.status_code}).")
        st.caption(f"Resposta do Servidor: {e.response.text}")
        return {"error": f"HTTP Error: {e.response.status_code}"}
    except Exception as e:
        st.error(f"❌ Erro de conexão ou inesperado ao enviar mensagem: {e}")
        return {"error": "Connection or Unknown Error"}

def poll_task_result(task_id: str) -> Dict[str, Optional[str]]:
    """Verifica o status da tarefa de IA pelo task_id."""
    try:
        response = HTTP_CLIENT.get(f"{API_BASE_URL}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Se a tarefa expirar ou for um erro 404/500, tratamos como falha de polling
        return {"status": "error", "result": f"Falha no Polling: {e}"}

# --- LAYOUTS/PÁGINAS ---

def layout_chat_bot(bot: Bot):
    """Página de chat individual com um bot."""
    st.title(f"Conversando com {bot.name} ({bot.gender[0]})") # Ajuste na exibição do gênero
    st.info(f"Bem-vindo(a)! **{bot.name}**: {bot.welcome_message}")
    
    # Inicializa o histórico de chat
    if "messages" not in st.session_state or st.session_state.get("current_bot_id") != bot.id:
        st.session_state.messages = []
        st.session_state.current_bot_id = bot.id
        st.session_state.polling_task_id = None

    # Exibe o histórico de mensagens
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["text"])

    # Tratamento de Polling (para a resposta da IA)
    if st.session_state.polling_task_id:
        with st.spinner("🤖 O bot está pensando... (Processamento Assíncrono)"):
            import time
            
            # Limita o polling para evitar loop infinito
            for _ in range(20): # Tenta 20 vezes
                time.sleep(1) # Espera 1 segundo entre as checagens
                
                task_status = poll_task_result(st.session_state.polling_task_id)

                if task_status["status"] == "complete":
                    ai_response = task_status["result"]
                    
                    # 1. Adiciona a resposta da IA ao histórico
                    st.session_state.messages.append({"role": "model", "text": ai_response})
                    
                    # 2. Reseta o ID da tarefa para o próximo turno
                    st.session_state.polling_task_id = None
                    
                    # 3. Exibe a resposta final e recarrega a página
                    st.experimental_rerun()
                    return

                elif task_status["status"] == "error":
                    st.error(f"❌ Erro durante o processamento da tarefa: {task_status.get('result', 'Detalhes desconhecidos.')}")
                    st.session_state.polling_task_id = None
                    return
            
            # Se o loop terminar sem resposta, exibe timeout
            st.warning("⚠️ Tempo de espera esgotado. A API demorou demais para responder.")
            st.session_state.polling_task_id = None


    # Caixa de entrada do usuário
    if prompt := st.chat_input("Diga algo ao bot..."):
        # 1. Adiciona a mensagem do usuário ao histórico
        st.session_state.messages.append({"role": "user", "text": prompt})
        
        # 2. Chama a API do FastAPI (que inicia a tarefa em background)
        response_data = send_chat_message(bot.id, st.session_state.messages)
        
        if "task_id" in response_data:
            # 3. Salva o task_id para iniciar o polling
            st.session_state.polling_task_id = response_data["task_id"]
            
            # 4. Recarrega a página para iniciar o spinner de polling
            st.experimental_rerun()
        else:
            # Erro na API
            st.error(f"Não foi possível iniciar a tarefa de chat: {response_data.get('error', 'Erro desconhecido')}")


def layout_listagem_bots(bots: List[Bot]):
    """Página de listagem de bots existentes (página inicial preferida)."""
    st.title("CríngeBot - Bots Existentes")

    if not bots:
        # Mensagem de warning mais informativa
        st.warning(f"""
            Nenhum bot encontrado ou a API não está acessível em **{API_BASE_URL}**. 
            Se você está vendo um erro de conexão acima, por favor, defina a variável de ambiente **`API_BASE_URL`** no Streamlit para o URL público do seu backend FastAPI (ex: `https://cringe-8h21.onrender.com`).
            Tente recarregar a página após a correção.
        """)
        return

    # Renderiza os cards dos bots
    # Adicionando um contador de bots
    st.markdown(f"**Total de Bots:** {len(bots)}")
    
    cols = st.columns(3)
    for i, bot in enumerate(bots):
        col = cols[i % 3]
        with col:
            with st.container(border=True):
                # Usando um placeholder com o nome do bot se o avatar não estiver disponível
                # Adicionando Gênero ao placeholder se o nome for curto
                placeholder_text = bot.name[0] if len(bot.name) > 0 else "BOT"
                st.image(bot.avatar_url or f"https://placehold.co/100x100/1e293b/ffffff?text={placeholder_text}", width=100)
                st.subheader(bot.name)
                st.markdown(f"**Gênero:** {bot.gender}")
                st.markdown(f"**Introdução:** {bot.introduction}")
                
                # Botão que define o bot atual e muda o layout
                if st.button(f"Conversar com {bot.name}", key=bot.id):
                    st.session_state.page = "chat_bot"
                    st.session_state.selected_bot = bot
                    st.experimental_rerun()

# --- LAYOUT DE CRIAÇÃO (MOCK) ---

def layout_criar_bot():
    """Página de criação de um novo bot (Mock Simples)."""
    st.title("Criar Novo Bot (Recurso Avançado)")
    st.info("Este recurso é um mock. O bot criado será temporário na sessão.")

    # Formulário de criação (simplificado)
    name = st.text_input("Nome do Bot")
    gender = st.selectbox("Gênero", ["Feminino", "Masculino", "Indefinido"])
    personality = st.text_area("Personalidade (Descrição de Persona)")
    system_prompt = st.text_area("System Prompt (Instruções para a IA)")
    avatar_url = st.text_input("URL do Avatar (Ex: https://i.imgur.com/07kI9Qh.jpeg)")

    if st.button("Salvar Bot (Mock)"):
        if name and personality and system_prompt:
            mock_bot_data = {
                "id": str(uuid.uuid4()),
                "creator_id": "user-local",
                "name": name,
                "gender": gender,
                "introduction": "Novo bot criado localmente.",
                "personality": personality,
                "welcome_message": f"Olá! Eu sou {name}!",
                "avatar_url": avatar_url or f"https://placehold.co/100x100/1e293b/ffffff?text={name[0]}",
                "tags": ["Local", "Novo"],
                "conversation_context": "",
                "context_images": "",
                "system_prompt": system_prompt,
                "ai_config": {"temperature": 0.7, "max_output_tokens": 512}
            }
            new_bot = Bot(mock_bot_data)
            
            # Adiciona o bot criado ao estado da sessão (simulação de persistência)
            if 'mock_bots' not in st.session_state:
                st.session_state.mock_bots = []
            st.session_state.mock_bots.append(new_bot)
            
            st.success(f"Bot '{name}' criado (localmente)!")
            st.session_state.page = "listagem"
            st.experimental_rerun()
        else:
            st.error("Por favor, preencha Nome, Personalidade e System Prompt.")

# --- NAVEGAÇÃO E APLICAÇÃO PRINCIPAL ---

def main():
    """Função principal que gerencia o estado e o layout da aplicação."""
    st.set_page_config(layout="wide", page_title="CRÍNGE: Chat Assíncrono com Bots (FastAPI + Streamlit)")
    st.markdown("## 👹 CRÍNGE: Chat Assíncrono com Bots (FastAPI + Streamlit)")
    st.markdown("_Arquitetura Async, implementada para atender ao Ponto 5 da Revisão da Athena._")

    # Inicialização do estado de sessão
    if "page" not in st.session_state:
        st.session_state.page = "listagem" # Inicia na listagem de bots
    if "selected_bot" not in st.session_state:
        st.session_state.selected_bot = None

    # --- SIDEBAR (Barra Lateral) ---
    with st.sidebar:
        st.header("frontend")
        
        # Priorizamos a listagem, que agora é a página inicial
        if st.button("Bots Existentes", key="nav_list"):
            st.session_state.page = "listagem"
            st.session_state.selected_bot = None
            st.session_state.messages = []
            st.experimental_rerun()
        
        if st.button("Criar Bot", key="nav_create"):
            st.session_state.page = "criar_bot"
            st.session_state.selected_bot = None
            st.session_state.messages = []
            st.experimental_rerun()
        
        # Botão extra para simular a criação de grupo (fora do escopo do chat individual)
        st.button("Criar Grupo (Em Desenvolvimento)", key="nav_group", disabled=True)
        
        st.divider()
        st.caption(f"Backend API: {API_BASE_URL}")

    # --- RENDERIZAÇÃO DA PÁGINA PRINCIPAL ---
    
    if st.session_state.page == "criar_bot":
        layout_criar_bot()
    
    elif st.session_state.page == "listagem" or st.session_state.page == "chat_bot" and st.session_state.selected_bot is None:
        # Carrega bots da API e de simulação local
        api_bots = fetch_bots()
        
        # Se houver bots locais (criados na sessão), os adiciona
        local_bots = st.session_state.get('mock_bots', [])
        all_bots = api_bots + local_bots
        
        # Se um bot foi selecionado e estamos na listagem (caso de reruns), o leva para o chat
        if st.session_state.page == "chat_bot" and st.session_state.selected_bot:
             layout_chat_bot(st.session_state.selected_bot)
        else:
            layout_listagem_bots(all_bots)

    elif st.session_state.page == "chat_bot" and st.session_state.selected_bot:
        layout_chat_bot(st.session_state.selected_bot)

if __name__ == "__main__":
    main()
