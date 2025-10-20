# c:\cringe\3.0\pages\1_Criar_Bot.py (NOVO ARQUIVO)

import streamlit as st
import requests
import time

# --- CONFIGURAÇÕES E FUNÇÕES REPETIDAS ---
# REUTILIZE a API_URL e as funções api_post / api_get
API_URL = "https://cringe-8h21.onrender.com"

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

# Funções auxiliares (Se você tiver a função api_get, inclua-a também)
# ...

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
                "avatar_url": bot_avatar,  # Novo Campo
                "tags": [t.strip() for t in bot_tags.split(',')] if bot_tags else [], # Novo Campo
                "conversation_context": "", # Campo Vazio por padrão
                "context_images": [],     # Campo Vazio por padrão
                "system_prompt": system_prompt,
                "ai_config": {"temperature": temperature, "max_output_tokens": max_tokens}
            }
            
            if api_post("bots", bot_payload):
                st.success(f"Bot '{bot_name}' criado com sucesso!")
                time.sleep(1.5)
                # O ideal aqui é redirecionar de volta para a Home Page
                # st.switch_page("main.py") # Streamlit 1.30+
                st.info("Voltando para a Home Page em instantes...")
                st.rerun() # Alternativa simples para recarregar