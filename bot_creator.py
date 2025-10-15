import streamlit as st
import requests
import json
import uuid

# --- CONFIGURAÇÃO ---
# URL do seu backend CRINGE no Render.
BACKEND_URL = "https://cringe-8h21.onrender.com"
TEST_CREATOR_ID = "user-1" # ID do usuário criador

st.set_page_config(
    page_title="CRINGE: Criador de Agentes de IA",
    layout="centered"
)

st.title("🤖 Criador de Agentes de IA (Bots)")
st.subheader("Defina a Personalidade e o Comportamento do seu Agente")

# --- Função de Submissão ---

def submit_bot(bot_data):
    """Envia os dados do novo bot para o backend (FastAPI)."""
    
    # 1. Cria um ID único
    bot_id = f"bot-{uuid.uuid4().hex[:8]}"
    
    # 2. Constrói o Payload completo
    payload = {
        "bot_id": bot_id,
        "creator_id": TEST_CREATOR_ID,
        "name": bot_data["name"],
        "system_prompt": bot_data["system_prompt"],
        "ai_config": {
            "temperature": bot_data["temperature"],
            "max_output_tokens": bot_data["max_tokens"]
        }
    }
    
    # 3. Envia a requisição POST
    try:
        response = requests.post(f"{BACKEND_URL}/bots/create", json=payload, timeout=10)
        response.raise_for_status()
        
        st.success(f"🤖 Bot '{payload['name']}' criado com sucesso! ID: **{bot_id}**")
        st.balloons()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao criar Bot. Verifique se o Backend está ativo em {BACKEND_URL}. Detalhes: {e}")
    except Exception as e:
        st.error(f"Erro inesperado: {e}")

# --- Formulário Streamlit ---

with st.form("bot_creation_form"):
    st.markdown("### 1. Detalhes Básicos")
    bot_name = st.text_input("Nome do Agente (Ex: Mestre Sombrio, Elfo Bardo):", 
                             max_chars=50)
    
    st.markdown("### 2. Personalidade e Prompt")
    system_prompt = st.text_area("Instrução do Sistema (System Prompt):", 
                                 help="Descreva a personalidade, o papel e as regras do seu bot. (Ex: 'Você é um oráculo cego e misterioso que responde apenas em enigmas e rimas.')",
                                 height=200)

    st.markdown("### 3. Configurações da IA (Gemini)")
    col1, col2 = st.columns(2)
    
    with col1:
        temperature = st.slider("Temperatura (Criatividade):", 
                                min_value=0.0, max_value=1.0, value=0.7, step=0.05,
                                help="Valores mais altos (perto de 1.0) tornam a resposta mais criativa e menos previsível.")
    
    with col2:
        max_tokens = st.slider("Tokens Máximos na Resposta:", 
                               min_value=128, max_value=2048, value=1024, step=128,
                               help="O tamanho máximo que a resposta da IA pode ter.")
        
    submitted = st.form_submit_button("Criar Bot de IA")
    
    if submitted:
        if not bot_name or not system_prompt:
            st.error("Por favor, preencha o Nome e o Prompt do Sistema.")
        else:
            bot_data = {
                "name": bot_name,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            submit_bot(bot_data)

st.markdown("---")
st.caption(f"Backend ativo em: **{BACKEND_URL}**")