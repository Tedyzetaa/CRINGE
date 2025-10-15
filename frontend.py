import streamlit as st
import requests
import json
import time

# --- CONFIGURAÇÃO ---
# URL do seu backend CRINGE no Render.
# Se você estiver testando localmente, mude para: "http://127.0.0.1:8080"
BACKEND_URL = "https://cringe-8h21.onrender.com" 

TEST_GROUP_ID = "group-123"
TEST_USER_ID = "user-1"

st.set_page_config(
    page_title="CRINGE RPG-AI: V2.0 - Chat Persistente",
    layout="wide"
)

# Título da Aplicação
st.title("🎲 CRINGE RPG-AI: V2.0 - Chat de Teste")

# --- GERENCIAMENTO DE ESTADO E INICIALIZAÇÃO ---

def load_initial_data(url):
    """Carrega o histórico de mensagens, membros e todos os bots disponíveis."""
    try:
        # Carrega dados do grupo (histórico e membros)
        group_res = requests.get(f"{url}/groups/{TEST_GROUP_ID}", timeout=10) 
        group_res.raise_for_status()
        group_data = group_res.json()
        
        # Carrega todos os bots disponíveis
        bots_res = requests.get(f"{url}/bots/all", timeout=10)
        bots_res.raise_for_status()
        all_bots_data = bots_res.json()
        
        # 1. Armazena os nomes dos membros
        member_names = {}
        for bot in all_bots_data:
            member_names[bot['bot_id']] = bot['name']
        
        # Adiciona o nome do usuário de teste
        user_res = requests.get(f"{url}/users/{TEST_USER_ID}")
        member_names[TEST_USER_ID] = user_res.json().get('username', 'Usuário de Teste')
        
        st.session_state.member_names = member_names
        st.session_state.messages = group_data.get('messages', [])
        st.session_state.current_members = group_data.get('member_ids', [])
        st.session_state.all_bots = all_bots_data
        st.session_state.error_loading = False
    except requests.exceptions.RequestException as e:
        st.session_state.messages = []
        st.session_state.error_loading = True
        st.session_state.member_names = {}
        st.error(f"Erro ao conectar com o Backend: Certifique-se de que o backend está ativo em {url}. Detalhes: {e}")

if 'messages' not in st.session_state:
    load_initial_data(BACKEND_URL)
    
if st.session_state.error_loading:
    st.stop()


# --- FUNÇÃO DE GERENCIAMENTO DE MEMBROS ---

def update_group_members(new_member_ids: list[str]):
    """Envia a nova lista de membros para o backend para persistência."""
    payload = {"member_ids": new_member_ids}
    try:
        response = requests.post(f"{BACKEND_URL}/groups/{TEST_GROUP_ID}/members", json=payload, timeout=5)
        response.raise_for_status()
        
        st.session_state.current_members = response.json().get('member_ids', [])
        st.success("Lista de membros atualizada com sucesso no banco de dados!")
        st.rerun()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao atualizar membros no backend: {e}")


# --- BARRA LATERAL (GERENCIAMENTO DE BOTS) ---

with st.sidebar:
    st.header("👥 Gerenciar Membros do Grupo")
    st.markdown("---")
    
    st.subheader("Bots Disponíveis (SQLite)")
    
    # Cria uma lista de bot_ids para os bots que estão no grupo atualmente
    active_bot_ids = [mid for mid in st.session_state.current_members if mid.startswith("bot-") and mid not in ["bot-mestre", TEST_USER_ID]]
    
    # Lista de todos os IDs de bots (excluindo o Mestre, que é obrigatório)
    available_bot_ids = [bot['bot_id'] for bot in st.session_state.all_bots if bot['bot_id'] not in ["bot-mestre"]]
    
    # Cria o seletor mútiplo usando os nomes dos bots
    selected_bot_names = st.multiselect(
        "Adicionar/Remover Bots:",
        options=[st.session_state.member_names[bot_id] for bot_id in available_bot_ids],
        default=[st.session_state.member_names[bot_id] for bot_id in active_bot_ids],
        help="Selecione os bots que devem responder no chat (além do Mestre da Masmorra)."
    )
    
    # Mapeia nomes selecionados de volta para IDs
    name_to_id = {v: k for k, v in st.session_state.member_names.items()}
    newly_selected_ids = [name_to_id[name] for name in selected_bot_names]

    # Garante que o Mestre e o Usuário de Teste estão sempre lá
    final_members_list = list(set(newly_selected_ids + ["bot-mestre", TEST_USER_ID]))

    if st.button("Aplicar Mudanças no Grupo"):
        update_group_members(final_members_list)
        
    st.markdown("---")
    
    st.subheader("Membros Ativos:")
    for mid in st.session_state.current_members:
        icon = "👑" if mid == "bot-mestre" else "👤" if mid == TEST_USER_ID else "🤖"
        st.write(f"{icon} {st.session_state.member_names.get(mid, mid)}")
    
    st.markdown("---")
    st.caption(f"Backend CRINGE rodando em: **{BACKEND_URL}**")


# --- INTERFACE DE CHAT ---

chat_container = st.container(height=500, border=True)

# Exibe todas as mensagens salvas no SQLite
for message in st.session_state.messages:
    sender_id = message['sender_id']
    sender_type = message['sender_type']
    
    nome = st.session_state.member_names.get(sender_id, sender_id)
    
    if sender_type == 'user':
        avatar = "👤"
    elif sender_id == "bot-mestre":
        avatar = "👑"
    elif sender_id == "bot-npc-1":
        avatar = "🎶"
    else: 
        avatar = "🤖"
        
    with chat_container:
        st.chat_message(name=nome, avatar=avatar).write(message['text'])


# 2. Entrada do Usuário
prompt = st.chat_input("Digite sua ação ou mensagem para o grupo...")

if prompt:
    # 3. Processar a mensagem
    # (Função que envia a mensagem para o backend, mesma de antes)
    
    # 1. Adiciona a mensagem do usuário ao histórico local (antes de enviar)
    st.session_state.messages.append({
        "sender_id": TEST_USER_ID,
        "sender_type": "user",
        "text": prompt,
        "timestamp": time.time()
    })
    
    payload = {
        "group_id": TEST_GROUP_ID,
        "sender_id": TEST_USER_ID,
        "text": prompt
    }
    
    with st.spinner("🤖 Os Agentes de IA estão pensando..."):
        try:
            response = requests.post(f"{BACKEND_URL}/groups/send_message", json=payload, timeout=45) 
            response.raise_for_status()
            
            api_data = response.json()
            ai_responses = api_data.get("ai_responses", [])
            
            for msg in ai_responses:
                 if msg['text'] and not msg['text'].startswith("Erro de IA:"):
                    st.session_state.messages.append(msg)
                 elif msg['text'].startswith("Erro de IA:"):
                    bot_name = st.session_state.member_names.get(msg['sender_id'], msg['sender_id'])
                    st.error(f"O agente {bot_name} falhou: {msg['text'].split('(Detalhe: ')[-1].replace(')', '')}")

            st.rerun() 
                 
        except requests.exceptions.Timeout:
            st.error("Erro de Timeout: O Backend demorou demais para responder. Tente novamente.")
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de Conexão com a API: {e}")
        except json.JSONDecodeError:
            st.error("Erro: O backend retornou uma resposta inválida (não-JSON).")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")