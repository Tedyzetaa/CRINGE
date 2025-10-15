# 🔥 CRINGE RPG-AI Multi-Bot Backend - Versão 1.2

Este projeto é um backend de alto desempenho, construído com **FastAPI** e **Python**, desenhado para gerenciar um jogo de RPG de mesa onde múltiplos personagens e o Mestre do Jogo são controlados por Agentes de Inteligência Artificial (Gemini API).

O nome oficial do projeto é **CRINGE**. A **Versão 1.2** integra a chamada real ao Gemini, corrige erros de execução assíncrona e adiciona o frontend de gerenciamento de Bots.

## 🚀 Status da Versão 1.2

✅ **Arquitetura Base (FastAPI/DB):** Completa.
✅ **Lógica de IA (Gemini API):** Funcional e otimizada com chamadas assíncronas.
✅ **Frontend de Teste (Chat):** Funcional (`frontend.py`).
✅ **Frontend de Gerenciamento (Criação de Bots):** Novo e Funcional (`bot_creator.py`).
✅ **Deploy:** Projeto pronto para ser hospedado no Render/Heroku.

---

## 🛠️ Detalhes da Tecnologia

* **Framework:** FastAPI (Python)
* **Servidor:** Uvicorn (ASGI)
* **Interface:** Streamlit (para os dois frontends de teste/gerenciamento)
* **Gerenciamento de Ambiente:** Conda (`rpg-ia`)
* **Modelo de IA:** Google Gemini API (`gemini-2.5-flash`)

## 📂 Estrutura do Projeto

/cringe/1.1/
├── main.py          # Aplicação FastAPI, define as rotas da API e a lógica de IA.
├── db.py            # Simulação de Banco de Dados em memória.
├── models.py        # Definição dos modelos de dados (classes Pydantic).
├── requirements.txt # Lista de dependências Python (Atualizada com streamlit).
├── frontend.py      # Frontend Streamlit para o Chat (Interação com os Bots).
├── bot_creator.py   # Frontend Streamlit para criar novos Agentes de IA (Bots).
├── Procfile         # Configuração para deploy em serviços como Render.
└── README.md        # Este arquivo.


## ⚙️ Configuração e Inicialização

O projeto deve ser rodado dentro do ambiente Conda chamado `rpg-ia`.

### 1. Instalar Dependências

Certifique-se de estar na pasta do projeto e com o ambiente ativo:

```bash
pip install -r requirements.txt
2. Configurar a Chave de API
Crie um arquivo chamado .env na pasta raiz (/cringe/1.1) e adicione sua chave:

Snippet de código

# .env
GEMINI_API_KEY="SUA_CHAVE_AQUI"
3. Rodar o Backend
Inicie o servidor Uvicorn no Terminal 1:

Bash

uvicorn main:app --reload --port 8080
(O backend estará acessível em http://127.0.0.1:8080)

4. Rodar o Frontend (Criação de Bots)
Inicie a interface de gerenciamento de Bots no Terminal 2:

Bash

streamlit run bot_creator.py
5. Rodar o Frontend (Chat Principal)
Inicie a interface de chat principal no Terminal 2 (após fechar o bot_creator.py) ou no Terminal 3:

Bash

streamlit run frontend.py
🧭 Rotas Principais da API
As rotas já estão configuradas para interagir com os dados simulados:

Método	Endpoint	Descrição	Modelo de Input
GET	/	Confirma o status da API.	N/A
GET	/groups/{group_id}	Retorna o estado completo de um grupo de chat.	group-123 (ID de teste)
POST	/bots/create	NOVA ROTA: Cria e armazena um novo Agente de IA (Bot).	Bot (JSON)
POST	/groups/send_message	PRINCIPAL: Recebe mensagem do usuário, salva e aciona múltiplas IAs em paralelo.	NewMessage (JSON)

Exportar para as Planilhas
🌐 Deploy Temporário
O projeto está configurado para um deploy fácil (ex: Render) usando o arquivo Procfile. O URL de produção deve ser usado para atualizar a variável BACKEND_URL no frontend.py antes de compartilhar o projeto com testadores externos.