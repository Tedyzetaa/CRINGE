# c:\cringe\3.0\main.py (COM CORREÇÕES DE API)

import streamlit as st
import requests
import time
from typing import List, Dict, Any # Importações úteis para tipagem

# 🚨 API_URL deve apontar para o servidor FastAPI
API_URL = "https://cringe-8h21.onrender.com"

# ... (Configurações de página e estilos permanecem iguais)
st.set_page_config(page_title="CRINGE RPG-AI", page_icon="🧙", layout="wide")

# 🔹 Estilo personalizado (MANTENHA ESTE BLOCO)
st.markdown("""
    <style>
    .main { background-color: #1e1e2f; color: #f0f0f0; }
    .block-container { padding-top: 2rem; }
    .stTextInput > div > input { background-color: #2e2e3e; color: white; }
    .stButton > button { background-color: #6c63ff; color: white; border-radius: 5px; }
    .stSelectbox > div { background-color: #2e2e3e; color: white; }
    </style>
""", unsafe_allow_html=True)


st.title("🧙 CRINGE RPG-AI")
st.subheader("Converse com seus bots em cenários épicos")

# --- FUNÇÕES DE CHAMADA À API (CORRIGIDAS) ---
def api_post(endpoint, payload):
    # CORREÇÃO: Garante que endpoints como "users" e "groups" tenham a barra no final
    if not endpoint.endswith('/') and endpoint not in ["groups/send_message", "users"]:
        endpoint += '/'
        
    try:
        res = requests.post(f"{API_URL}/{endpoint}", json=payload)
        res.raise_for_status() 
        return res.json()
    except requests.exceptions.ConnectionError:
        st.sidebar.error(f"❌ Erro de Conexão: O backend em {API_URL} não está respondendo.")
        return None
    except requests.exceptions.HTTPError as e:
        st.sidebar.error(f"❌ Erro HTTP ao enviar para /{endpoint}: {e} | URL: {res.url}")
        return None

def api_get(endpoint):
    # CORREÇÃO: Garante que endpoints como "bots" e "groups" tenham a barra no final
    # Exceção para endpoints com ID no final (ex: groups/1/messages)
    path_segments = endpoint.split('/')
    if not endpoint.endswith('/') and not (len(path_segments) > 1 and path_segments[-1].isdigit()):
        endpoint += '/'

    try:
        res = requests.get(f"{API_URL}/{endpoint}")
        res.raise_for_status()
        return res.json()
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Erro de Conexão: Não foi possível acessar o backend em {API_URL}.")
        return []
    except requests.exceptions.HTTPError:
        # Retorna lista vazia em caso de 404/500 para evitar quebra do app
        return []

# --- SIDEBAR: JOGADOR (MANTIDO) ---
st.sidebar.header("🎭 Jogador")
username = st.sidebar.text_input("Nome do jogador", value="Aventureiro")
user_id = f"user-{username.lower().replace(' ', '-')}"
is_admin = st.sidebar.checkbox("Sou administrador")

# Cria/Atualiza usuário
if username:
    # A chamada "users" será corrigida pela api_post
    api_post("users", {
        "name": username
    })

# --- SIDEBAR: CRIAÇÃO DE BOT (APENAS BOTÃO) ---
st.sidebar.header("⚙️ Ferramentas")
# O botão de criação de Bot agora é um link para a página 'Criar Bot'
if st.sidebar.button("🤖 Criar Novo Bot"):
    # Streamlit automaticamente navega para a página 1_Criar_Bot
    pass 
    
# --- SIDEBAR: CRIAÇÃO DE GRUPO (AJUSTADO PARA A CHAMADA DE API) ---
st.sidebar.header("🌍 Criar Grupo")
with st.sidebar.expander("Novo Grupo"):
    group_name = st.text_input("Nome do Grupo")
    group_scenario = st.text_area("Cenário")
    
    # 💡 BUSCA DE BOTS PARA O MULTISELECT
    all_bots = api_get("bots") # Será corrigido para "bots/"
    bot_options = {b.get("name"): b.get("id") for b in all_bots if b.get("name")} 
    
    selected_bot_names = st.multiselect(
        "Bots no grupo", 
        list(bot_options.keys()),
        default=[]
    )
    
    # Mapeia nomes selecionados de volta para IDs
    selected_bot_ids = [bot_options[name] for name in selected_bot_names if name in bot_options]
    
    if st.button("Criar Grupo"):
        if not selected_bot_ids:
            st.sidebar.warning("Selecione pelo menos um bot para criar o grupo.")
        else:
            group_payload = {
                "name": group_name,
                "scenario": group_scenario,
                "bot_ids": selected_bot_ids 
            }
            if api_post("groups", group_payload): # Será corrigido para "groups/"
                st.sidebar.success(f"Grupo '{group_name}' criado com sucesso!")
                st.rerun() 

# --- SELEÇÃO DE GRUPO E CONVERSA (Falta o código completo, mas as chamadas de API foram corrigidas) ---

# ... O código de Seleção de Grupo e Conversa **DEVE** ser idêntico ao que estava no frontend.py.
# Vou adicionar o restante do código da conversa aqui com as correções de API:

# --- SELEÇÃO DE GRUPO ---
st.subheader("🌍 Escolha o grupo")

all_groups = api_get("groups") # Será corrigido para "groups/"

group_name_to_id = {g.get("name"): g.get("id") for g in all_groups if g.get("name")}
group_names = list(group_name_to_id.keys())

placeholder_text = "Nenhuma opção para selecionar. Crie um grupo na sidebar."
display_options = group_names if group_names else [placeholder_text]

group_choice = st.selectbox(
    "Selecione um grupo para continuar a conversa:",
    options=display_options,
    index=0 if group_names else None, 
    placeholder=placeholder_text
)

group_id = None
if group_choice and group_choice != placeholder_text:
    group_id = group_name_to_id.get(group_choice)

# --- CONVERSA ---
st.markdown("### 💬 Conversa")

if not group_id:
    st.info("Selecione ou crie um grupo para começar a conversar.")
else:
    # Busca o histórico de mensagens
    msg_resp_data = api_get(f"groups/{group_id}/messages") # Endpoint com ID, não precisa de barra
    
    if msg_resp_data and isinstance(msg_resp_data, list):
        for msg in msg_resp_data:
            sender_id = msg.get("sender_id", "unknown")
            text = msg.get('text', 'Mensagem vazia')

            if sender_id.startswith("bot-"):
                sender_display = f"🤖 Bot (ID: {sender_id.split('-')[-1]})" 
                st.markdown(f"**{sender_display}**: {text}")
            else:
                sender_display = "🧑 Jogador" 
                st.markdown(f"**{sender_display}**: {text}")
    else:
           st.warning("Não há histórico de mensagens para este grupo.")

# --- ENVIAR NOVA MENSAGEM ---
st.markdown("---")
st.markdown("### ✉️ Enviar mensagem")

with st.form("message_form", clear_on_submit=True):
    text = st.text_input("Digite sua mensagem", key="message_input")
    submitted = st.form_submit_button("Enviar")

    if submitted:
        if not group_id:
            st.error("Selecione um grupo antes de enviar a mensagem.")
        elif text:
            message_payload = {
                "group_id": group_id,
                "sender_id": user_id,
                "text": text
            }
            # CORREÇÃO: "groups/send_message" não deve ter barra
            if api_post("groups/send_message", message_payload): 
                time.sleep(0.1) 
                st.rerun()