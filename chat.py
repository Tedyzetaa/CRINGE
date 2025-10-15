import streamlit as st
import requests
import json
import time

# --- CONFIGURAÇÃO ---
# URL do seu backend. Mantenha esta URL para produção/Render.
BACKEND_URL = "https://cringe-8h21.onrender.com" 

TEST_GROUP_ID = "group-123"
TEST_USER_ID = "user-1"
MESTRE_ID = "bot-mestre" 

st.set_page_config(
    page_title="CRINGE RPG-AI: V2.3 - Chat Persistente",
    layout="wide"
)

st.title("🎲 CRINGE RPG-AI: V2.3 - Chat de Teste (Mestre Opcional)")

# --- GERENCIAMENTO DE ESTADO E INICIALIZAÇÃO ---

def load_initial_data(url):
    """Carrega o histórico de mensagens, membros e todos os bots disponíveis."""
    try:
        # 1. Carrega dados do grupo (histórico e membros)
        group_res = requests.get(f"{url}/groups/{TEST_GROUP_ID}", timeout=10) 
        group_res.raise_for_status()
        group_data = group_res.json()
        
        # 2. Carrega todos os bots disponíveis
        bots_res = requests.get(f"{url}/bots/all", timeout=10)
        bots_res.raise_for_status()
        all_bots_data = bots_res.json()
        
        # 3. Armazena os nomes dos membros
        member_names = {}
        for bot in all_bots_data:
            member_names[bot['bot_id']] = bot['name']
        
        # 4. Adiciona o nome do usuário de teste
        user_res = requests.get(f"{url}/users/{TEST_USER_ID}", timeout=5)
        user_res.raise_for_status()
        user_data = user_res.json()
        member_names[TEST_USER_ID] = user_data.get('username', 'Usuário de Teste')
        
        # 5. Salva no estado da sessão
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
    except Exception as e:
        st.error(f"Erro inesperado ao carregar dados: {e}")
        st.session_state.error_loading = True

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
        st.success("Lista de membros atualizada com sucesso!")
        # Força o recarregamento do chat com a nova lista de membros
        st.rerun() 
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao atualizar membros no backend: {e}")


# --- BARRA LATERAL (GERENCIAMENTO DE BOTS) ---

with st.sidebar:
    st.header("👥 Gerenciar Membros do Grupo")
    st.markdown("---")

    # 1. CONTROLE DO MESTRE DA MASMORRA
    st.subheader("Controle do Mestre")
    is_mestre_active = MESTRE_ID in st.session_state.current_members

    mestre_toggle = st.checkbox(
        "Ativar Mestre da Masmorra", 
        value=is_mestre_active, 
        key="mestre_toggle",
        help="O Mestre narra o cenário e reage às suas ações. Desative para um chat livre sem cenário."
    )
    st.markdown("---")
    
    st.subheader("Bots NPC Disponíveis")
    
    # Identifica IDs de NPCs (todos os bots menos o Mestre)
    available_npc_ids = [bot['bot_id'] for bot in st.session_state.all_bots if bot['bot_id'] != MESTRE_ID]
    
    # Cria uma lista de bot_ids para os NPCs que estão no grupo atualmente
    active_npc_ids = [
        mid for mid in st.session_state.current_members 
        if mid.startswith("bot-") and mid != MESTRE_ID and mid != TEST_USER_ID
    ]
    
    # Mapeia IDs para nomes para o multiselect
    npc_options = {st.session_state.member_names[bot_id]: bot_id for bot_id in available_npc_ids if bot_id in st.session_state.member_names}
    default_npc_names = [st.session_state.member_names[bot_id] for bot_id in active_npc_ids if bot_id in st.session_state.member_names]
    
    selected_npc_names = st.multiselect(
        "Adicionar/Remover NPCs:",
        options=list(npc_options.keys()),
        default=default_npc_names,
        help="Selecione os bots NPC que devem participar da conversa."
    )
    
    # Mapeia nomes selecionados de volta para IDs
    newly_selected_ids = [npc_options[name] for name in selected_npc_names]

    # 2. Constrói a lista final de membros
    final_members_list = [TEST_USER_ID] # Usuário sempre incluído
    
    if mestre_toggle:
        final_members_list.append(MESTRE_ID)
        
    final_members_list.extend(newly_selected_ids)
    
    # Remove duplicatas
    final_members_list = list(dict.fromkeys(final_members_list))


    if st.button("Aplicar Mudanças no Grupo"):
        update_group_members(final_members_list)
        
    st.markdown("---")
    
    st.subheader("Membros Ativos Atuais:")
    for mid in st.session_state.current_members:
        icon = "👑" if mid == MESTRE_ID else "👤" if mid == TEST_USER_ID else "🤖"
        st.write(f"{icon} {st.session_state.member_names.get(mid, mid)}")
    
    st.markdown("---")
    st.caption(f"Backend ativo em: **{BACKEND_URL}**")


# --- INTERFACE DE CHAT ---

chat_container = st.container(height=500, border=True)

# Exibe todas as mensagens
for message in st.session_state.messages:
    sender_id = message['sender_id']
    sender_type = message['sender_type']
    
    nome = st.session_state.member_names.get(sender_id, sender_id)
    
    # Define o avatar baseado no ID/Tipo
    if sender_type == 'user':
        avatar = "👤"
    elif sender_id == MESTRE_ID:
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
    # 1. Adiciona a mensagem do usuário ao histórico local
    st.session_state.messages.append({
        "sender_id": TEST_USER_ID,
        "sender_type": "user",
        "text": prompt,
        "timestamp": time.time()
    })
    
    # Recarrega a tela para mostrar a mensagem do usuário imediatamente
    st.rerun() 
    
    payload = {
        "group_id": TEST_GROUP_ID,
        "sender_id": TEST_USER_ID,
        "text": prompt
    }
    
    with st.spinner("🤖 Os Agentes de IA estão pensando..."):
        try:
            # 4. Chama o backend
            response = requests.post(f"{BACKEND_URL}/groups/send_message", json=payload, timeout=45) 
            response.raise_for_status()
            
            api_data = response.json()
            ai_responses = api_data.get("ai_responses", [])
            
            # Adiciona as respostas da IA
            for msg in ai_responses:
                 if msg['text'] and not msg['text'].startswith("Erro de IA:"):
                     st.session_state.messages.append(msg)
                 elif msg['text'].startswith("Erro de IA:"):
                     bot_name = st.session_state.member_names.get(msg['sender_id'], msg['sender_id'])
                     # Exibe o erro específico retornado pelo backend
                     st.error(f"O agente {bot_name} falhou: {msg['text'].split('(Detalhe: ')[-1].replace(')', '')}")

            # Recarrega a tela para mostrar as novas mensagens dos bots
            st.rerun() 
                 
        except requests.exceptions.Timeout:
            st.error("Erro de Timeout: O Backend demorou demais para responder. Tente novamente.")
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de Conexão com a API: Falha ao enviar a mensagem. Detalhes: {e}")
        except json.JSONDecodeError:
            st.error("Erro: O backend retornou uma resposta inválida (não-JSON).")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")