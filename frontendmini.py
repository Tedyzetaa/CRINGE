import streamlit as st
import requests
import json

# Configuração mais básica possível
st.set_page_config(page_title="CRINGE Import", layout="centered")

API_URL = "https://cringe-5jmi.onrender.com"

st.title("🤖 CRINGE - Importar Personagens")
st.write("---")

# Função única e simples
def testar_importacao(bots_data):
    try:
        st.write("🔄 Testando conexão com API...")
        response = requests.post(f"{API_URL}/bots/import", json=bots_data, timeout=10)
        
        st.write(f"📡 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            st.success("🎉 SUCESSO: Personagens importados!")
            return True
        else:
            st.error(f"❌ ERRO: {response.text}")
            return False
    except Exception as e:
        st.error(f"💥 EXCEÇÃO: {str(e)}")
        return False

# Botão de teste mais simples possível
st.subheader("Teste Rápido 1: Pimenta")
if st.button("Testar Importação da Pimenta"):
    bot_teste = {
        "bots": [{
            "creator_id": "teste",
            "name": "Pimenta Teste",
            "gender": "Feminino",
            "introduction": "Teste simples",
            "personality": "Teste",
            "welcome_message": "Olá, sou um teste!",
            "avatar_url": "https://i.imgur.com/07kI9Qh.jpeg",
            "tags": ["teste"],
            "conversation_context": "teste",
            "context_images": "[]",
            "system_prompt": "Você é um teste.",
            "ai_config": {"temperature": 0.7, "max_output_tokens": 100}
        }]
    }
    testar_importacao(bot_teste)

st.write("---")

# Teste direto com JSON
st.subheader("Teste Rápido 2: JSON Direto")
json_direto = st.text_area("Cole JSON direto:", height=150, value='''{
  "bots": [{
    "creator_id": "teste",
    "name": "Teste Direto",
    "gender": "Masculino",
    "introduction": "Teste direto",
    "personality": "Teste",
    "welcome_message": "Olá teste!",
    "avatar_url": "https://i.imgur.com/hHa9vCs.png",
    "tags": ["teste"],
    "conversation_context": "teste",
    "context_images": "[]",
    "system_prompt": "Teste direto",
    "ai_config": {"temperature": 0.7, "max_output_tokens": 100}
  }]
}''')

if st.button("Testar JSON Direto"):
    try:
        dados = json.loads(json_direto)
        testar_importacao(dados)
    except Exception as e:
        st.error(f"Erro no JSON: {e}")

st.write("---")

# Verificar status da API
st.subheader("Status da API")
try:
    resposta = requests.get(f"{API_URL}/health", timeout=5)
    if resposta.status_code == 200:
        st.success("✅ API ONLINE")
        st.json(resposta.json())
    else:
        st.error(f"❌ API OFFLINE - Status: {resposta.status_code}")
except Exception as e:
    st.error(f"💥 ERRO DE CONEXÃO: {e}")

# Verificar bots existentes
st.subheader("Bots Existentes")
try:
    bots = requests.get(f"{API_URL}/bots", timeout=5)
    if bots.status_code == 200:
        st.write(f"📊 Total de bots: {len(bots.json())}")
        for bot in bots.json():
            st.write(f"- {bot['name']} (ID: {bot['id'][:8]}...)")
    else:
        st.error(f"Erro ao buscar bots: {bots.status_code}")
except Exception as e:
    st.error(f"Erro: {e}")

st.write("---")
st.write("🔍 **Dica:** Verifique o console do navegador (F12) para mais detalhes")
