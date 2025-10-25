CRINGE RPG-AI: Plataforma de Chatbots Personalizados
Resumo Geral do Projeto
O CRINGE RPG-AI é uma plataforma que permite a criação e interação com chatbots de RPG (Role-Playing Game) personalizados. O projeto é dividido em dois componentes principais: um Backend (API) construído com FastAPI, responsável pela lógica de dados e integração com a IA (Hugging Face), e um Frontend construído com Streamlit, que fornece a interface de usuário para seleção e conversação com os bots.
Arquitetura de Componentes
Componente
Tecnologia
Responsabilidade Principal
Backend API
FastAPI, SQLAlchemy
Gerenciamento de Dados (Bots), Rotas RESTful (/bots, /bots/chat), Integração com Modelos de IA (via AIService).
Frontend UI
Streamlit
Interface de Usuário, Seleção de Bots, Tela de Chat, Gerenciamento de Estado da Conversa.
Banco de Dados
SQLite (Local), SQLAlchemy ORM
Persistência dos dados dos Bots.
Serviço de IA
Hugging Face API
Geração das respostas de chat baseadas na personalidade do Bot.

Peculiaridades e Detalhes de Implementação
1. Sistema de Módulos e Importação (Python Backend)
A arquitetura do backend utiliza diretórios (routers, services, etc.). Para garantir que o servidor Uvicorn no Render (produção) consiga iniciar sem erros de importação, o arquivo routers/bots.py implementa uma lógica de importação robusta:
try:
    # 1. Tentativa de importação para ambiente de produção (Uvicorn)
    from services.ai_service import AIService 
    from database import get_db
    from models import Bot
    from schemas import ChatRequest, ChatResponse, BotDisplay
except ImportError as e:
    # 2. Fallback para imports relativos (ambientes de teste/locais)
    try:
        from ..database import get_db
        # ... imports relativos restantes ...
    except ImportError as e_relative:
        # 3. Fallback final: Classe Placeholder para evitar NameError
        class AIService:
            def generate_response(self, *args, **kwargs):
                raise NotImplementedError("AIService não foi carregado corretamente.")


Peculiaridade: Esta estrutura garante que a classe AIService seja sempre definida (mesmo que como um placeholder com erro controlado) antes de ser instanciada (ai_service = AIService()), resolvendo o erro comum de NameError que acontece ao iniciar servidores como o uvicorn a partir de um script principal.
2. Persistência de Dados de Configuração
O modelo Bot no SQLAlchemy precisa armazenar configurações complexas (como as configurações específicas da IA, ai_config, e a lista de tags), que são estruturadas em JSON no código Python.
Peculiaridade: Em vez de usar tipos complexos do SQLAlchemy, esses campos são armazenados como strings JSON no banco de dados:
ai_config_json (string): Armazena a configuração da IA como uma string JSON (ex: {"temperature": 0.7, "model_name": "..."}).
tags (string): Armazena a lista de tags como uma string JSON (ex: ["rpg", "fantasia", "mago"]).
As rotas da API (GET /bots e POST /bots/chat/{bot_id}) são responsáveis por desserializar essas strings JSON (usando json.loads()) de volta para objetos Python (dict ou list) antes de processar ou retornar os dados.
3. Rotas da API e Tratamento de Erros
O roteador principal (routers/bots.py) define duas rotas essenciais:
GET /bots: Retorna a lista de bots, desserializando as tags para o cliente.
POST /bots/chat/{bot_id}:
Busca o bot por ID no DB.
Desserializa ai_config_json para passar as configurações corretas para a AIService.
Envia a requisição de geração de resposta para o Hugging Face (via AIService).
Inclui um tratamento de exceção (try/except Exception as e:) robusto para capturar falhas de rede, timeouts ou erros da API externa de IA e retornar um HTTPException(500) informativo ao frontend.
4. Correções de Frontend (Streamlit)
O frontend (frontend.py) foi ajustado para maior robustez e depuração:
Rerun Atualizado: O uso de st.experimental_rerun() foi atualizado para o padrão moderno do Streamlit: st.rerun().
URL Base Dinâmica: A URL base da API (API_BASE_URL) pode ser configurada dinamicamente na barra lateral do Streamlit, permitindo alternar facilmente entre o ambiente de desenvolvimento local (http://localhost:8000) e o ambiente de produção (ex: https://cringe-8h21.onrender.com), facilitando a depuração de problemas de conexão.
Timeout Aumentado: O timeout de requisição para o chat foi aumentado (90 segundos), dando mais tempo para modelos de IA mais lentos processarem as respostas.
