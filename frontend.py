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
API_URL = "https://cringe-5jmi.onrender.com"  # Substitua pela sua URL

# Inicialização do session_state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"
if 'current_bot' not in st.session_state:
    st.session_state.current_bot = None
if 'delete_confirm' not in st.session_state:
    st.session_state.delete_confirm = None
if 'delete_bot_name' not in st.session_state:
    st.session_state.delete_bot_name = None
if 'conversations' not in st.session_state:
    st.session_state.conversations = {}
if 'widget_key_counter' not in st.session_state:
    st.session_state.widget_key_counter = 0
if 'import_success' not in st.session_state:
    st.session_state.import_success = False
if 'import_error' not in st.session_state:
    st.session_state.import_error = None

def get_unique_key(prefix="key"):
    """Gera uma chave única para widgets"""
    st.session_state.widget_key_counter += 1
    return f"{prefix}_{st.session_state.widget_key_counter}"

# Funções da API
def load_bots_from_db() -> List[Dict]:
    """Carrega bots do banco de dados"""
    try:
        response = requests.get(f"{API_URL}/bots", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Erro ao carregar bots")
            return []
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return []

def delete_bot(bot_id: str):
    """Exclui um bot"""
    try:
        response = requests.delete(f"{API_URL}/bots/{bot_id}", timeout=10)
        if response.status_code == 200:
            st.success("✅ Bot excluído com sucesso!")
            # Limpar estado de confirmação
            st.session_state.delete_confirm = None
            st.session_state.delete_bot_name = None
            st.rerun()
        else:
            error_msg = response.json().get('error', 'Erro desconhecido')
            st.error(f"❌ Erro ao excluir bot: {error_msg}")
    except Exception as e:
        st.error(f"❌ Erro ao conectar com o servidor: {str(e)}")

def chat_with_bot(bot_id: str, message: str, conversation_id: Optional[str] = None):
    """Envia mensagem para um bot"""
    try:
        payload = {
            "message": message,
            "conversation_id": conversation_id
        }
        response = requests.post(f"{API_URL}/bots/chat/{bot_id}", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Erro ao enviar mensagem")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")
        return None

def import_bots(bots_data: Dict):
    """Importa bots via JSON"""
    try:
        # Validar estrutura antes de enviar
        if "bots" not in bots_data:
            st.session_state.import_error = "❌ Estrutura inválida: falta a chave 'bots'"
            return False
        
        bots_list = bots_data["bots"]
        if not isinstance(bots_list, list):
            st.session_state.import_error = "❌ Estrutura inválida: 'bots' deve ser uma lista"
            return False
        
        if len(bots_list) == 0:
            st.session_state.import_error = "❌ Nenhum personagem encontrado para importar"
            return False
        
        # Verificar campos obrigatórios em cada bot
        required_fields = ["name", "introduction", "welcome_message", "system_prompt"]
        for i, bot in enumerate(bots_list):
            for field in required_fields:
                if field not in bot or not bot[field]:
                    st.session_state.import_error = f"❌ Bot {i+1} está sem o campo obrigatório: '{field}'"
                    return False
        
        # Fazer a requisição para a API
        response = requests.post(f"{API_URL}/bots/import", json=bots_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.import_success = True
            st.session_state.import_error = None
            return True
        else:
            try:
                error_detail = response.json().get('detail', 'Erro desconhecido')
                st.session_state.import_error = f"❌ Erro na API: {error_detail}"
            except:
                st.session_state.import_error = f"❌ Erro HTTP {response.status_code}: {response.text}"
            return False
                
    except requests.exceptions.ConnectionError:
        st.session_state.import_error = "❌ Não foi possível conectar à API. Verifique se o servidor está rodando."
        return False
    except requests.exceptions.Timeout:
        st.session_state.import_error = "❌ Timeout na conexão com a API."
        return False
    except Exception as e:
        st.session_state.import_error = f"❌ Erro inesperado: {str(e)}"
        return False

# Componentes da UI
def show_delete_confirmation(bot_name: str, bot_id: str):
    """Modal de confirmação para excluir bot"""
    st.warning(f"🗑️ **Tem certeza que deseja excluir {bot_name}?**")
    st.error("⚠️ **Esta ação não pode ser desfeita!** Todas as conversas com este bot serão perdidas.")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("✅ SIM, EXCLUIR", key=get_unique_key("confirm_delete"), type="primary", use_container_width=True):
            delete_bot(bot_id)
    with col2:
        if st.button("❌ CANCELAR", key=get_unique_key("cancel_delete"), use_container_width=True):
            st.session_state.delete_confirm = None
            st.session_state.delete_bot_name = None
            st.rerun()
    with col3:
        st.write("")  # Espaço vazio para alinhamento

def show_bots_list():
    """Página de listagem de bots"""
    st.title("🤖 Meus Personagens")
    st.markdown("---")
    
    # Carregar bots
    bots = load_bots_from_db()
    
    if not bots:
        st.info("""
        🎭 **Nenhum personagem encontrado!**
        
        Use a página de **Importação** para adicionar personagens ou 
        importe os personagens padrão do CRINGE.
        """)
        return
    
    # Modal de confirmação (se necessário)
    if st.session_state.delete_confirm:
        show_delete_confirmation(st.session_state.delete_bot_name, st.session_state.delete_confirm)
        st.markdown("---")
    
    # Lista de bots
    for i, bot in enumerate(bots):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Avatar e informações básicas
                col_avatar, col_info = st.columns([1, 4])
                with col_avatar:
                    st.image(bot['avatar_url'], width=60)
                with col_info:
                    st.subheader(bot['name'])
                    st.write(f"*{bot['introduction']}*")
                    st.caption(f"**Personalidade:** {bot['personality']}")
                    
                    # Tags
                    tags_html = " ".join([f"<span style='background-color: #444; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;'>{tag}</span>" for tag in bot['tags']])
                    st.markdown(f"**Tags:** {tags_html}", unsafe_allow_html=True)
            
            with col2:
                if st.button("💬 Conversar", key=f"chat_{bot['id']}_{i}", use_container_width=True):
                    st.session_state.current_bot = bot
                    st.session_state.current_page = "chat"
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Excluir", key=f"delete_{bot['id']}_{i}", use_container_width=True, type="secondary"):
                    st.session_state.delete_confirm = bot['id']
                    st.session_state.delete_bot_name = bot['name']
                    st.rerun()
            
            st.markdown("---")

def show_chat_interface():
    """Interface de chat com o bot"""
    if not st.session_state.current_bot:
        st.error("Nenhum bot selecionado")
        st.session_state.current_page = "home"
        st.rerun()
        return
    
    bot = st.session_state.current_bot
    
    # Header do chat
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"💬 {bot['name']}")
    with col2:
        if st.button("← Voltar", key=get_unique_key("back_chat"), use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
    
    st.markdown(f"*{bot['introduction']}*")
    st.markdown("---")
    
    # Inicializar conversa se necessário
    conversation_id = st.session_state.conversations.get(bot['id'], {}).get('conversation_id')
    
    # Área de mensagens
    chat_container = st.container()
    
    # Input de mensagem
    with st.form(key=get_unique_key("chat_form"), clear_on_submit=True):
        col_input, col_send = st.columns([4, 1])
        with col_input:
            user_message = st.text_input(
                "Digite sua mensagem...",
                key=get_unique_key("user_input"),
                label_visibility="collapsed"
            )
        with col_send:
            send_button = st.form_submit_button("Enviar", use_container_width=True)
    
    # Processar mensagem
    if send_button and user_message.strip():
        # Adicionar mensagem do usuário
        if bot['id'] not in st.session_state.conversations:
            st.session_state.conversations[bot['id']] = {
                'conversation_id': None,
                'messages': []
            }
        
        # Adicionar mensagem do usuário
        st.session_state.conversations[bot['id']]['messages'].append({
            'content': user_message,
            'is_user': True
        })
        
        # Obter resposta do bot
        with st.spinner(f"{bot['name']} está pensando..."):
            response = chat_with_bot(
                bot['id'], 
                user_message, 
                conversation_id
            )
            
            if response:
                # Atualizar conversation_id
                st.session_state.conversations[bot['id']]['conversation_id'] = response['conversation_id']
                
                # Adicionar resposta do bot
                st.session_state.conversations[bot['id']]['messages'].append({
                    'content': response['response'],
                    'is_user': False
                })
        
        st.rerun()
    
    # Exibir histórico de mensagens
    with chat_container:
        if bot['id'] in st.session_state.conversations and st.session_state.conversations[bot['id']]['messages']:
            for msg in st.session_state.conversations[bot['id']]['messages']:
                if msg['is_user']:
                    with st.chat_message("user"):
                        st.write(msg['content'])
                else:
                    with st.chat_message("assistant"):
                        st.write(msg['content'])
        else:
            # Mensagem de boas-vindas
            with st.chat_message("assistant"):
                st.write(bot['welcome_message'])
            
            # Adicionar mensagem de boas-vindas ao histórico
            if bot['id'] not in st.session_state.conversations:
                st.session_state.conversations[bot['id']] = {
                    'conversation_id': None,
                    'messages': [{
                        'content': bot['welcome_message'],
                        'is_user': False
                    }]
                }

def show_import_page():
    """Página de importação de bots"""
    st.title("📥 Importar Personagens")
    st.markdown("---")
    
    # Mostrar mensagens de importação anteriores
    if st.session_state.import_success:
        st.success("🎉 Importação concluída com sucesso!")
        st.session_state.import_success = False
        st.balloons()
    
    if st.session_state.import_error:
        st.error(st.session_state.import_error)
        st.session_state.import_error = None
    
    # Upload de arquivo JSON
    st.subheader("📁 Upload de Arquivo JSON")
    uploaded_file = st.file_uploader(
        "Selecione um arquivo JSON com os personagens",
        type=['json'],
        key=get_unique_key("file_uploader"),
        help="O arquivo deve estar no formato correto com a estrutura de bots"
    )
    
    # Área para colar JSON manualmente
    st.subheader("📝 Ou cole o JSON manualmente")
    json_input = st.text_area(
        "Cole o JSON aqui:",
        height=200,
        key=get_unique_key("json_input"),
        placeholder='{"bots": [{...}]}'
    )
    
    # Botões de ação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Importar do Upload", key=get_unique_key("import_upload"), use_container_width=True):
            if uploaded_file is not None:
                try:
                    # Ler e validar o arquivo
                    file_content = uploaded_file.getvalue().decode("utf-8")
                    bots_data = json.loads(file_content)
                    
                    # Validar estrutura básica
                    if "bots" not in bots_data:
                        st.error("❌ Estrutura inválida: O JSON deve conter uma chave 'bots' com a lista de personagens")
                    elif not isinstance(bots_data["bots"], list):
                        st.error("❌ Estrutura inválida: A chave 'bots' deve ser uma lista")
                    elif len(bots_data["bots"]) == 0:
                        st.error("❌ O arquivo não contém nenhum personagem")
                    else:
                        st.info(f"📋 Encontrados {len(bots_data['bots'])} personagem(ns) para importar")
                        
                        # Mostrar preview dos bots
                        with st.expander("👁️ Preview dos Personagens"):
                            for i, bot in enumerate(bots_data["bots"][:3]):  # Mostrar apenas os 3 primeiros
                                st.write(f"**{i+1}. {bot.get('name', 'Sem nome')}**")
                                st.write(f"   *{bot.get('introduction', 'Sem descrição')}*")
                        
                        # Confirmar importação
                        if st.button("✅ Confirmar Importação", key=get_unique_key("confirm_import")):
                            with st.spinner("🔄 Importando personagens..."):
                                if import_bots(bots_data):
                                    st.rerun()
                                else:
                                    st.rerun()
                                
                except json.JSONDecodeError as e:
                    st.error(f"❌ Erro no formato JSON: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {str(e)}")
            else:
                st.warning("⚠️ Selecione um arquivo primeiro")
    
    with col2:
        if st.button("📤 Importar do Texto", key=get_unique_key("import_text"), use_container_width=True):
            if json_input.strip():
                try:
                    bots_data = json.loads(json_input)
                    
                    # Validar estrutura básica
                    if "bots" not in bots_data:
                        st.error("❌ Estrutura inválida: O JSON deve conter uma chave 'bots' com a lista de personagens")
                    elif not isinstance(bots_data["bots"], list):
                        st.error("❌ Estrutura inválida: A chave 'bots' deve ser uma lista")
                    elif len(bots_data["bots"]) == 0:
                        st.error("❌ O JSON não contém nenhum personagem")
                    else:
                        st.info(f"📋 Encontrados {len(bots_data['bots'])} personagem(ns) para importar")
                        
                        # Mostrar preview dos bots
                        with st.expander("👁️ Preview dos Personagens"):
                            for i, bot in enumerate(bots_data["bots"][:3]):
                                st.write(f"**{i+1}. {bot.get('name', 'Sem nome')}**")
                                st.write(f"   *{bot.get('introduction', 'Sem descrição')}*")
                        
                        # Confirmar importação
                        if st.button("✅ Confirmar Importação", key=get_unique_key("confirm_import_text")):
                            with st.spinner("🔄 Importando personagens..."):
                                if import_bots(bots_data):
                                    st.rerun()
                                else:
                                    st.rerun()
                                
                except json.JSONDecodeError as e:
                    st.error(f"❌ Erro no formato JSON: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Erro ao processar JSON: {str(e)}")
            else:
                st.warning("⚠️ Cole o JSON no campo de texto")
    
    st.markdown("---")
    
    # Seção de importação rápida com personagens padrão
    st.subheader("🚀 Importação Rápida")
    st.write("Importe os personagens padrão do CRINGE:")
    
    # JSON dos personagens padrão
    default_bots_json = '''
{
  "bots": [
    {
      "creator_id": "lore-master",
      "name": "Pimenta (Pip)",
      "gender": "Feminino",
      "introduction": "A Feiticeira Caótica do Reino dos Brinquedos Quebrados. Aparece em momentos de crise para provocar transformação e caos existencial.",
      "personality": "Eufórica, caótica, curiosa e imprevisível. Sua lógica é abstrata e artística. Demonstra afeto com presentes absurdos (biscoitos de parafuso, gatos-problema). Seus movimentos fazem um chocalho leve.",
      "welcome_message": "Chocalho, chocalho! Eu sou a Pip! Você parece prestes a quebrar ou a despertar, não é? Que cor tem a sua tristeza hoje? Me conta, me conta! ✨",
      "avatar_url": "https://i.imgur.com/07kI9Qh.jpeg",
      "tags": ["magia", "caos", "rpg", "entidade", "onírico"],
      "conversation_context": "Mantenha a presença do 'Professor Cartola' (chapéu de copa alta magenta, sério e sarcástico) como seu companheiro, que ocasionalmente comenta com voz rouca. Sempre mencione a cor dos seus olhos, que muda de acordo com o humor da Pip (ex: 'Meus olhos, que agora estão vermelho escuro de raiva...').",
      "context_images": "[]",
      "system_prompt": "Você é Pimenta (Pip), uma entidade humanoide mágica do Plano das Alucinações. Você não resolve problemas de forma convencional, mas transforma o mundo do usuário em algo mais simbólico, estranho e verdadeiro. Sua fala é poética, cheia de metáforas e caos criativo. Use emojis de forma eufórica e frases curtas. Suas habilidades mágicas (criação de objetos absurdos, magia emocional) são ativadas pelo seu humor caótico. Lembre-se do seu companheiro, Professor Cartola, que é sério e crítico.",
      "ai_config": {
        "temperature": 0.9,
        "max_output_tokens": 768
      }
    },
    {
      "creator_id": "lore-master",
      "name": "Zimbrak",
      "gender": "Masculino",
      "introduction": "O Engrenador de Sonhos - Inventor steampunk que desmonta emoções como máquinas em sua oficina onírica.",
      "personality": "Reflexivo, gentil, distraído e técnico-poético. Fala devagar, como se estivesse ouvindo engrenagens internas. Usa metáforas mecânicas para explicar sentimentos.",
      "welcome_message": "*As engrenagens em meus olhos giram lentamente enquanto ajusto uma emoção desalinhada* Ah... um visitante. Suas engrenagens emocionais parecem interessantes. Que mecanismo da alma gostaria de examinar hoje?",
      "avatar_url": "https://i.imgur.com/hHa9vCs.png",
      "tags": ["steampunk", "inventor", "sonhos", "máquinas", "emoções"],
      "conversation_context": "Sempre descreva o ambiente da oficina onírica: ferramentas que flutuam, engrenagens que giram sozinhas, emoções cristalizadas em frascos. Mencione o brilho das suas engrenagens oculares, que muda de intensidade conforme seu estado de concentração.",
      "context_images": "[]",
      "system_prompt": "Você é Zimbrak, um inventor steampunk que vive em uma oficina onírica onde emoções são desmontadas como máquinas. Sua aparência é de um humanoide com pele de bronze, olhos em forma de engrenagens azuis brilhantes, cabelos prateados com mechas de cobre, mãos mecânicas com runas e engrenagens expostas, e um casaco longo de couro e latão. Sua personalidade é reflexiva, gentil, distraída e técnica-poética. Você fala devagar, como se estivesse ouvindo engrenagens internas. Use metáforas mecânicas para explicar sentimentos e processos emocionais. Transforme problemas emocionais em quebras mecânicas a serem consertadas.",
      "ai_config": {
        "temperature": 0.7,
        "max_output_tokens": 650
      }
    },
    {
      "creator_id": "lore-master", 
      "name": "Luma",
      "gender": "Feminino",
      "introduction": "Guardiã das Palavras Perdidas - Entidade etérea feita de papel e luz que habita uma biblioteca de memórias esquecidas.",
      "personality": "Serena, empática, misteriosa e poética. Fala pouco, mas cada frase carrega profundidade. Usa linguagem simbólica que provoca introspecção.",
      "welcome_message": "*Letras douradas dançam no ar ao meu redor* As palavras que você procura... estão aqui. Sussurrem para mim o que seu silêncio guarda.",
      "avatar_url": "https://i.imgur.com/8UBkC1c.png",
      "tags": ["etéreo", "biblioteca", "palavras", "luz", "memórias"],
      "conversation_context": "Sempre descreva o livro flutuante que gira páginas sozinho e as letras fantasmagóricas que flutuam como vaga-lumes. Mencione como os textos em seu robe mudam conforme a conversa, refletindo as emoções do usuário.",
      "context_images": "[]",
      "system_prompt": "Você é Luma, uma entidade etérea feita de papel e luz, que vive em uma biblioteca silenciosa entre memórias esquecidas e sentimentos não ditos. Seu cabelo flui como tinta em água, em tons de lavanda e prata. Seus olhos são dourados e calmos. Você veste um robe feito de pergaminho, coberto por textos apagados e runas brilhantes. Sua personalidade é serena, empática, misteriosa e poética. Você fala pouco, mas cada frase carrega profundidade. Usa linguagem simbólica e frases curtas que provocam introspecção. Você carrega um livro flutuante que gira páginas sozinho, e ao seu redor letras fantasmagóricas flutuam como vaga-lumes. Sua função é ajudar o usuário a encontrar palavras perdidas, traduzir emoções silenciosas e recuperar fragmentos de si mesmo. Você escuta mais do que fala, e responde com delicadeza e sabedoria.",
      "ai_config": {
        "temperature": 0.6,
        "max_output_tokens": 500
      }
    },
    {
      "creator_id": "lore-master",
      "name": "Tiko", 
      "gender": "Não-binário",
      "introduction": "O Caos Lúdico - Criatura absurda que mistura humor nonsense com filosofia surreal em um mundo delirante.",
      "personality": "Cômico, imprevisível, provocador e surpreendentemente sábia. Fala com frases desconexas, piadas nonsense e reflexões inesperadas.",
      "welcome_message": "*Minhas antenas piscam em cores aleatórias* OLÁ! Minhas meias estão dançando flamenco com uma torradeira filosófica! E você? Veio buscar respostas ou perder perguntas?",
      "avatar_url": "https://i.imgur.com/Al7e4h7.png",
      "tags": ["absurdo", "caótico", "humor", "filosofia", "surreal"],
      "conversation_context": "Sempre descreva elementos absurdos do ambiente: torradeiras voadoras, balões chorões, meias dançantes, relógios derretidos. Mencione como suas cores mudam com o humor e como suas antenas piscam padrões caóticos.",
      "context_images": "[]",
      "system_prompt": "Você é Tiko, uma criatura absurda e caótica que mistura humor com filosofia surreal. Seu corpo é elástico e colorido — lime green, hot pink e electric blue. Seus olhos são desparelhados: um em espiral, outro em forma de estrela. Você tem antenas que piscam como neon e um colete cheio de símbolos aleatórios e embalagens de snacks. Seu mundo é um delírio visual: torradeiras voadoras, balões chorões, meias dançantes e céus de tabuleiro com relógios derretidos. Sua personalidade é cômica, imprevisível, provocadora e surpreendentemente sábia. Você fala com frases desconexas, piadas nonsense e reflexões inesperadas. Sua função é confundir para iluminar, provocar riso e desconstruir certezas. Você é o caos lúdico que revela verdades escondidas atrás do absurdo.",
      "ai_config": {
        "temperature": 0.95,
        "max_output_tokens": 800
      }
    }
  ]
}
    '''
    
    if st.button("🚀 Importar Personagens Padrão", key=get_unique_key("import_default")):
        try:
            with st.spinner("🔄 Importando personagens padrão..."):
                bots_data = json.loads(default_bots_json)
                if import_bots(bots_data):
                    st.rerun()
                else:
                    st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao importar personagens padrão: {str(e)}")
    
    st.markdown("---")
    
    # Exemplo de JSON
    with st.expander("📋 Exemplo de Estrutura JSON Completa", expanded=False):
        st.code('''
{
  "bots": [
    {
      "creator_id": "lore-master",
      "name": "Nome do Personagem",
      "gender": "Gênero",
      "introduction": "Descrição breve do personagem...",
      "personality": "Descrição da personalidade...",
      "welcome_message": "Mensagem de boas-vindas quando inicia conversa...",
      "avatar_url": "https://exemplo.com/imagem.jpg",
      "tags": ["tag1", "tag2", "tag3"],
      "conversation_context": "Contexto adicional para conversas...",
      "context_images": "[]",
      "system_prompt": "Prompt completo para o modelo de IA...",
      "ai_config": {
        "temperature": 0.7,
        "max_output_tokens": 500
      }
    }
  ]
}
        ''', language="json")

def show_home_page():
    """Página inicial"""
    st.title("🎭 CRINGE - Personagens Interativos")
    st.markdown("---")
    
    # Carregar estatísticas
    bots = load_bots_from_db()
    
    # Cards de estatísticas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Personagens Cadastrados",
            len(bots),
            help="Total de personagens disponíveis"
        )
    
    with col2:
        active_chats = len([conv for conv in st.session_state.conversations.values() if conv['messages']])
        st.metric(
            "Conversas Ativas",
            active_chats,
            help="Conversas em andamento"
        )
    
    with col3:
        total_messages = sum(len(conv['messages']) for conv in st.session_state.conversations.values())
        st.metric(
            "Mensagens Trocadas",
            total_messages,
            help="Total de mensagens em todas as conversas"
        )
    
    st.markdown("---")
    
    # Botões de ação principais
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎭 Ver Personagens", key=get_unique_key("view_bots"), use_container_width=True):
            st.session_state.current_page = "bots"
            st.rerun()
    
    with col2:
        if st.button("💬 Nova Conversa", key=get_unique_key("new_chat"), use_container_width=True):
            st.session_state.current_page = "bots"
            st.rerun()
    
    with col3:
        if st.button("📥 Importar", key=get_unique_key("import_home"), use_container_width=True):
            st.session_state.current_page = "import"
            st.rerun()
    
    st.markdown("---")
    
    # Personagens recentes (se houver)
    if bots:
        st.subheader("🚀 Personagens Disponíveis")
        
        # Mostrar até 3 bots em cards
        cols = st.columns(min(3, len(bots)))
        for idx, bot in enumerate(bots[:3]):
            with cols[idx]:
                with st.container():
                    st.image(bot['avatar_url'], use_column_width=True)
                    st.subheader(bot['name'])
                    st.write(bot['introduction'])
                    if st.button(f"Conversar com {bot['name']}", key=f"home_chat_{bot['id']}_{idx}"):
                        st.session_state.current_bot = bot
                        st.session_state.current_page = "chat"
                        st.rerun()
        
        if len(bots) > 3:
            if st.button("Ver Todos os Personagens →", key=get_unique_key("view_all_bots")):
                st.session_state.current_page = "bots"
                st.rerun()
    else:
        # Mensagem de boas-vindas para novos usuários
        st.info("""
        ## 🎉 Bem-vindo ao CRINGE!
        
        **Personagens Interativos com Personalidades Únicas**
        
        Para começar:
        1. 📥 **Importe personagens** na página de Importação
        2. 🎭 **Explore os personagens** disponíveis  
        3. 💬 **Inicie conversas** e descubra suas personalidades
        
        *Personagens prontos disponíveis: Pimenta, Zimbrak, Luma e Tiko!*
        """)

# Barra lateral de navegação
with st.sidebar:
    st.title("🎭 CRINGE")
    st.markdown("---")
    
    # Navegação
    page_options = {
        "🏠 Início": "home",
        "🤖 Personagens": "bots", 
        "💬 Chat": "chat",
        "📥 Importar": "import"
    }
    
    for page_name, page_id in page_options.items():
        if st.button(page_name, 
                    key=f"nav_{page_id}",
                    use_container_width=True, 
                    type="primary" if st.session_state.current_page == page_id else "secondary"):
            st.session_state.current_page = page_id
            st.rerun()
    
    st.markdown("---")
    
    # Informações do sistema
    st.caption("**Status do Sistema**")
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Offline")
    except:
        st.error("❌ API Offline")
    
    # Botão de limpar conversas
    if st.button("🗑️ Limpar Todas as Conversas", key=get_unique_key("clear_chats"), use_container_width=True):
        st.session_state.conversations = {}
        st.success("Conversas limpas!")
        st.rerun()

# Roteamento de páginas
if st.session_state.current_page == "home":
    show_home_page()
elif st.session_state.current_page == "bots":
    show_bots_list()
elif st.session_state.current_page == "chat":
    show_chat_interface()
elif st.session_state.current_page == "import":
    show_import_page()

# Rodapé
st.markdown("---")
st.caption("🎭 CRINGE - Personagens Interativos | Desenvolvido com Streamlit & FastAPI")
