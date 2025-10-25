import streamlit as st
import requests
import json
import time

# Configuração básica
st.set_page_config(page_title="CRINGE - Importar", page_icon="🤖")

API_URL = "https://cringe-5jmi.onrender.com"

# Estado da aplicação
if 'import_status' not in st.session_state:
    st.session_state.import_status = None
if 'import_message' not in st.session_state:
    st.session_state.import_message = ""

st.title("📥 Importar Personagens - CRINGE")
st.markdown("---")

# Função simplificada de importação
def importar_personagens(bots_data):
    """Função mínima para importar personagens"""
    try:
        st.session_state.import_status = "loading"
        st.session_state.import_message = "Enviando dados para a API..."
        
        response = requests.post(f"{API_URL}/bots/import", json=bots_data, timeout=30)
        
        if response.status_code == 200:
            st.session_state.import_status = "success"
            st.session_state.import_message = "✅ Personagens importados com sucesso!"
            return True
        else:
            error_detail = response.json().get('detail', 'Erro desconhecido')
            st.session_state.import_status = "error"
            st.session_state.import_message = f"❌ Erro na API: {error_detail}"
            return False
            
    except Exception as e:
        st.session_state.import_status = "error"
        st.session_state.import_message = f"❌ Erro de conexão: {str(e)}"
        return False

# Seção 1: JSON manual
st.subheader("📝 Cole o JSON aqui")
json_input = st.text_area(
    "Cole o conteúdo JSON dos personagens:",
    height=300,
    placeholder='{"bots": [{"creator_id": "lore-master", "name": "Nome", ...}]}',
    key="json_input_unique"
)

# JSON de exemplo pré-pronto
json_exemplo = '''{
  "bots": [
    {
      "creator_id": "lore-master",
      "name": "Pimenta (Pip)",
      "gender": "Feminino",
      "introduction": "A Feiticeira Caótica do Reino dos Brinquedos Quebrados",
      "personality": "Eufórica, caótica, curiosa e imprevisível",
      "welcome_message": "Chocalho, chocalho! Eu sou a Pip! ✨",
      "avatar_url": "https://i.imgur.com/07kI9Qh.jpeg",
      "tags": ["magia", "caos", "rpg"],
      "conversation_context": "Mantenha a presença do Professor Cartola",
      "context_images": "[]",
      "system_prompt": "Você é Pimenta (Pip), uma entidade mágica caótica...",
      "ai_config": {"temperature": 0.9, "max_output_tokens": 768}
    }
  ]
}'''

# Botão para usar exemplo
if st.button("📋 Usar Exemplo Pronto", key="btn_exemplo"):
    st.session_state.json_input_unique = json_exemplo
    st.rerun()

# Botão de importação principal
if st.button("🚀 IMPORTAR PERSONAGENS", type="primary", key="btn_importar"):
    if json_input.strip():
        try:
            # Validar JSON
            bots_data = json.loads(json_input)
            
            # Verificar estrutura básica
            if "bots" not in bots_data:
                st.error("❌ Estrutura inválida: falta a chave 'bots'")
            elif not isinstance(bots_data["bots"], list):
                st.error("❌ Estrutura inválida: 'bots' deve ser uma lista")
            elif len(bots_data["bots"]) == 0:
                st.error("❌ Nenhum personagem encontrado no JSON")
            else:
                # Mostrar preview
                st.info(f"📋 Encontrados {len(bots_data['bots'])} personagem(s)")
                
                # Importar
                with st.spinner("Importando personagens..."):
                    success = importar_personagens(bots_data)
                    
                # Mostrar resultado
                if success:
                    st.success(st.session_state.import_message)
                    st.balloons()
                    st.info("✅ Importação concluída! Verifique a lista de personagens.")
                else:
                    st.error(st.session_state.import_message)
                    
        except json.JSONDecodeError as e:
            st.error(f"❌ Erro no JSON: {str(e)}")
        except Exception as e:
            st.error(f"❌ Erro inesperado: {str(e)}")
    else:
        st.warning("⚠️ Cole o JSON no campo acima")

st.markdown("---")

# Seção 2: Importação direta com botões pré-definidos
st.subheader("⚡ Importação Rápida")

col1, col2 = st.columns(2)

with col1:
    if st.button("🤖 Importar Pimenta", key="btn_pimenta"):
        bots_data = {
            "bots": [{
                "creator_id": "lore-master",
                "name": "Pimenta (Pip)",
                "gender": "Feminino",
                "introduction": "A Feiticeira Caótica do Reino dos Brinquedos Quebrados",
                "personality": "Eufórica, caótica, curiosa e imprevisível",
                "welcome_message": "Chocalho, chocalho! Eu sou a Pip! Que cor tem a sua tristeza hoje? ✨",
                "avatar_url": "https://i.imgur.com/07kI9Qh.jpeg",
                "tags": ["magia", "caos", "rpg"],
                "conversation_context": "Mantenha a presença do Professor Cartola",
                "context_images": "[]",
                "system_prompt": "Você é Pimenta (Pip), uma entidade mágica caótica do Plano das Alucinações.",
                "ai_config": {"temperature": 0.9, "max_output_tokens": 768}
            }]
        }
        
        with st.spinner("Importando Pimenta..."):
            success = importar_personagens(bots_data)
            if success:
                st.success("✅ Pimenta importada com sucesso!")
                st.balloons()
            else:
                st.error(st.session_state.import_message)

with col2:
    if st.button("🔧 Importar Zimbrak", key="btn_zimbrak"):
        bots_data = {
            "bots": [{
                "creator_id": "lore-master",
                "name": "Zimbrak",
                "gender": "Masculino", 
                "introduction": "O Engrenador de Sonhos - Inventor steampunk",
                "personality": "Reflexivo, gentil e técnico-poético",
                "welcome_message": "Ah... um visitante. Que mecanismo da alma gostaria de examinar hoje?",
                "avatar_url": "https://i.imgur.com/hHa9vCs.png",
                "tags": ["steampunk", "inventor", "sonhos"],
                "conversation_context": "Oficina onírica com engrenagens",
                "context_images": "[]",
                "system_prompt": "Você é Zimbrak, inventor steampunk de emoções.",
                "ai_config": {"temperature": 0.7, "max_output_tokens": 650}
            }]
        }
        
        with st.spinner("Importando Zimbrak..."):
            success = importar_personagens(bots_data)
            if success:
                st.success("✅ Zimbrak importado com sucesso!")
                st.balloons()
            else:
                st.error(st.session_state.import_message)

# Status da API
st.markdown("---")
st.subheader("🔍 Status do Sistema")

try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    if response.status_code == 200:
        st.success("✅ API Online e funcionando")
    else:
        st.error(f"❌ API com problemas: Status {response.status_code}")
except Exception as e:
    st.error(f"❌ Não foi possível conectar à API: {str(e)}")

# Debug info (opcional)
with st.expander("🔧 Informações de Debug"):
    st.write("**URL da API:**", API_URL)
    st.write("**Status da importação:**", st.session_state.import_status)
    st.write("**Mensagem:**", st.session_state.import_message)
