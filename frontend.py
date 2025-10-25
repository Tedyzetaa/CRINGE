import streamlit as st
import requests
import json
import uuid
from typing import List, Dict, Optional

# Configuração da página
st.set_page_config(
    page_title="CRINGE - Personagens Interativos",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações da API
API_URL = "https://cringe-5jmi.onrender.com"

# Inicialização do session_state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"
if 'current_bot' not in st.session_state:
    st.session_state.current_bot = None
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'widget_counter' not in st.session_state:
    st.session_state.widget_counter = 0

def get_unique_key(prefix="widget"):
    """Gera uma chave única para widgets"""
    st.session_state.widget_counter += 1
    return f"{prefix}_{st.session_state.widget_counter}"

# Funções da API
def load_bots_from_db() -> List[Dict]:
    """Carrega bots do banco de dados"""
    try:
        response = requests.get(f"{API_URL}/bots")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return []

def import_bots_simple(bots_data: Dict):
    """Função simplificada para importar bots"""
    try:
        response = requests.post(f"{API_URL}/bots/import", json=bots_data, timeout=30)
        
        if response.status_code == 200:
            return True, "Importação realizada com sucesso!"
        else:
            error_msg = response.json().get('detail', 'Erro desconhecido')
            return False, f"Erro: {error_msg}"
    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"

# Páginas principais
def show_import_page_simple():
    """Página de importação simplificada"""
    st.title("📥 Importar Personagens")
    st.markdown("---")
    
    # Opção 1: Upload de arquivo
    st.subheader("📁 Upload de Arquivo JSON")
    uploaded_file = st.file_uploader("Selecione um arquivo JSON", type=['json'], key=get_unique_key("file_upload"))
    
    # Opção 2: JSON manual
    st.subheader("📝 Ou cole o JSON aqui")
    json_text = st.text_area("Cole o conteúdo JSON:", height=200, placeholder='{"bots": [...]}', key=get_unique_key("json_text"))
    
    # Botão de importação principal
    if st.button("🚀 IMPORTAR PERSONAGENS", type="primary", use_container_width=True, key=get_unique_key("import_main")):
        bots_data = None
        
        # Tentar obter dados do arquivo upload
        if uploaded_file is not None:
            try:
                file_content = uploaded_file.getvalue().decode("utf-8")
                bots_data = json.loads(file_content)
                st.success("✅ Arquivo carregado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao ler arquivo: {str(e)}")
                return
        
        # Se não tem arquivo, tentar do texto
        elif json_text.strip():
            try:
                bots_data = json.loads(json_text)
                st.success("✅ JSON validado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro no JSON: {str(e)}")
                return
        
        else:
            st.warning("⚠️ Selecione um arquivo ou cole o JSON")
            return
        
        # Validar estrutura
        if bots_data and "bots" in bots_data and isinstance(bots_data["bots"], list):
            st.info(f"📋 {len(bots_data['bots'])} personagem(s) encontrado(s)")
            
            # Mostrar preview
            with st.expander("👀 Visualizar Personagens"):
                for i, bot in enumerate(bots_data["bots"][:5]):  # Mostrar até 5
                    st.write(f"**{i+1}. {bot.get('name', 'Sem nome')}**")
                    st.write(f"   {bot.get('introduction', 'Sem descrição')}")
            
            # Confirmar importação
            if st.button("✅ CONFIRMAR IMPORTAÇÃO", type="secondary", use_container_width=True, key=get_unique_key("confirm_import")):
                with st.spinner("Importando personagens..."):
                    success, message = import_bots_simple(bots_data)
                    if success:
                        st.success(f"🎉 {message}")
                        st.balloons()
                        # Redirecionar para a lista de bots após 2 segundos
                        st.info("Redirecionando para a lista de personagens...")
                        st.session_state.current_page = "bots"
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        else:
            st.error("❌ Estrutura inválida. O JSON deve conter uma lista 'bots'")
    
    st.markdown("---")
    
    # Importação rápida com personagens padrão
    st.subheader("⚡ Importação Rápida")
    
    default_bots = {
        "bots": [
            {
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
                "system_prompt": "Você é Pimenta (Pip), uma entidade mágica caótica...",
                "ai_config": {"temperature": 0.9, "max_output_tokens": 768}
            },
            {
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
                "system_prompt": "Você é Zimbrak, inventor steampunk...",
                "ai_config": {"temperature": 0.7, "max_output_tokens": 650}
            }
        ]
    }
    
    if st.button("🤖 Importar Personagens de Exemplo", use_container_width=True, key=get_unique_key("import_example")):
        with st.spinner("Importando personagens de exemplo..."):
            success, message = import_bots_simple(default_bots)
            if success:
                st.success(f"🎉 {message}")
                st.balloons()
                st.session_state.current_page = "bots"
                st.rerun()
            else:
                st.error(f"❌ {message}")

def show_bots_list_simple():
    """Página de listagem simplificada"""
    st.title("🤖 Meus Personagens")
    
    bots = load_bots_from_db()
    
    if not bots:
        st.info("""
        🎭 **Nenhum personagem encontrado!**
        
        Vá para a página de **Importação** para adicionar personagens.
        """)
        return
    
    for i, bot in enumerate(bots):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader(bot['name'])
            st.write(f"*{bot['introduction']}*")
        with col2:
            if st.button("💬 Chat", key=f"chat_{bot['id']}_{i}"):
                st.session_state.current_bot = bot
                st.session_state.current_page = "chat"
                st.rerun()
        st.markdown("---")

def show_home_page_simple():
    """Página inicial simplificada"""
    st.title("🎭 CRINGE - Personagens Interativos")
    st.markdown("---")
    
    bots = load_bots_from_db()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Personagens", len(bots))
    with col2:
        st.metric("Conversas", len(st.session_state.conversations))
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Ver Personagens", use_container_width=True, key=get_unique_key("view_bots")):
            st.session_state.current_page = "bots"
            st.rerun()
    with col2:
        if st.button("📥 Importar", use_container_width=True, key=get_unique_key("import_home")):
            st.session_state.current_page = "import"
            st.rerun()
    
    if bots:
        st.subheader("Personagens Disponíveis")
        for i, bot in enumerate(bots[:3]):
            if st.button(f"💬 {bot['name']}", key=f"home_{bot['id']}_{i}"):
                st.session_state.current_bot = bot
                st.session_state.current_page = "chat"
                st.rerun()

# Barra lateral de navegação
with st.sidebar:
    st.title("🎭 CRINGE")
    st.markdown("---")
    
    pages = {
        "🏠 Início": "home",
        "🤖 Personagens": "bots", 
        "📥 Importar": "import"
    }
    
    for page_name, page_id in pages.items():
        if st.button(page_name, use_container_width=True, key=f"nav_{page_id}"):
            st.session_state.current_page = page_id
            st.rerun()
    
    st.markdown("---")
    
    # Status da API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Offline")
    except:
        st.error("❌ API Offline")

# Roteamento
if st.session_state.current_page == "home":
    show_home_page_simple()
elif st.session_state.current_page == "bots":
    show_bots_list_simple()
elif st.session_state.current_page == "import":
    show_import_page_simple()

st.markdown("---")
st.caption("🎭 CRINGE - Personagens Interativos")
