# 🔥 CRINGE RPG-AI Multi-Bot Backend & Frontend - Versão 1.5

Este projeto é uma plataforma de RPG de mesa onde múltiplos personagens e o Mestre do Jogo são controlados por Agentes de Inteligência Artificial (Gemini API). O projeto está dividido em Backend (FastAPI) e Frontends (Streamlit), hospedados em plataformas diferentes para máxima eficiência.

## 🚀 Status da Versão 1.5 - DEPLOY COMPLETO

| Componente | Plataforma de Hospedagem | Status | URL de Produção |
| :--- | :--- | :--- | :--- |
| **Backend (FastAPI/IA)** | **Render** | ✅ Online 24/7 | `https://cringe-8h21.onrender.com` |
| **Frontend (Chat Principal)** | **Streamlit Cloud** | ✅ Online 24/7 | **[A SER INSERIDO APÓS O DEPLOY]** |
| **Frontend (Criador de Bots)**| **Streamlit Cloud** | ✅ Online 24/7 | **[A SER INSERIDO APÓS O DEPLOY]** |

### ⚠️ AVISO IMPORTANTE

O Backend está ativo, mas para que a IA funcione, a chave **`GEMINI_API_KEY`** deve ser válida e estar configurada com sucesso nas **Environment Variables** do Render.

---

## 🛠️ Detalhes da Tecnologia

* **Backend Framework:** FastAPI (Python)
* **Backend Hosting:** Render
* **Interface de Usuário (Frontend):** Streamlit
* **Frontend Hosting:** Streamlit Community Cloud
* **Modelo de IA:** Google Gemini API (`gemini-2.5-flash`)

## 📂 Estrutura do Projeto

/cringe/1.1/
├── main.py          # Aplicação FastAPI, rotas da API e lógica de IA.
├── db.py            # Simulação de Banco de Dados (em memória).
├── models.py        # Definição dos modelos de dados (classes Pydantic).
├── requirements.txt # Lista de dependências Python para o Backend e Frontend.
├── frontend.py      # Frontend Streamlit para o Chat de Interação (Aponta para o Render).
├── bot_creator.py   # Frontend Streamlit para criar novos Agentes de IA (Aponta para o Render).
├── Procfile         # Comando de inicialização do Uvicorn para o Render.
├── .gitignore       # Ignora arquivos sensíveis (.env).
└── README.md        # Este arquivo.


## ⚙️ Inicialização Local para Desenvolvimento

Para rodar o projeto localmente para desenvolvimento ou depuração, siga os passos abaixo.

### 1. Instalar Dependências

Certifique-se de estar no ambiente Conda `(rpg-ia)`:

```bash
pip install -r requirements.txt
2. Configurar a Chave de API
Crie um arquivo chamado .env na pasta raiz (/cringe/1.1) e adicione sua chave.

3. Rodar o Backend Localmente (Render Offline)
Inicie o servidor Uvicorn no Terminal 1:

Bash

uvicorn main:app --reload --port 8080
4. Rodar o Frontend Localmente
Inicie as interfaces Streamlit no Terminal 2. Note que, ao rodar localmente, o frontend ainda tentará se comunicar com o Render, a menos que você mude o BACKEND_URL em frontend.py e bot_creator.py para http://127.0.0.1:8080.

Chat Principal: streamlit run frontend.py

Criador de Bots: streamlit run bot_creator.py

🧭 Rotas Principais da API (Backend no Render)
A URL base para todas as requisições é: https://cringe-8h21.onrender.com

Método	Endpoint	Descrição
GET	/	Confirma o status da API.
POST	/bots/create	Cria e armazena um novo Agente de IA.
POST	/groups/send_message	Recebe mensagem do usuário e aciona múltiplas IAs em paralelo.