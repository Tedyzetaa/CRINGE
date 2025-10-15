# 🔥 CRINGE RPG-AI Multi-Bot Backend - Versão 1.0

Este projeto é um backend de alto desempenho, construído com **FastAPI** e **Python**, desenhado para gerenciar um jogo de RPG de mesa onde múltiplos personagens e o Mestre do Jogo são controlados por Agentes de Inteligência Artificial (Gemini API).

O nome oficial do projeto é **CRINGE**.

A **Versão 1.0** estabelece a arquitetura completa de dados e as rotas de API para gerenciar usuários, bots, grupos de chat e o histórico de mensagens.

## 🚀 Status da Versão 1.0

✅ **Arquitetura Base:** Completa.
✅ **Modelos de Dados (Pydantic):** Finalizados (`User`, `Bot`, `ChatGroup`, `Message`).
✅ **Simulação de Banco de Dados:** Funcional (`db.py`).
✅ **Rotas FastAPI:** Criadas e testadas.
🛑 **Lógica de IA:** Simulação (Hardcoded) na rota `/groups/send_message`.

---

## 🛠️ Detalhes da Tecnologia

* **Framework:** FastAPI (Python)
* **Servidor:** Uvicorn (ASGI)
* **Gerenciamento de Ambiente:** Conda (`rpg-ia`)
* **Modelo de IA Integrado (Futuro):** Google Gemini API (`google-genai`)

## 📂 Estrutura do Projeto

/cringe/1.0/
├── main.py        # Aplicação FastAPI, define as rotas da API.
├── db.py          # Simulação de Banco de Dados em memória (inicializa dados para teste).
├── models.py      # Definição dos modelos de dados (classes Pydantic).
├── requirements.txt # Lista de dependências Python.
└── README.md      # Este arquivo.


## ⚙️ Configuração e Inicialização

O projeto deve ser rodado dentro do ambiente Conda chamado `rpg-ia`.

### 1. Instalar Dependências

Certifique-se de estar na pasta `C:\cringe\1.0` e com o ambiente `(rpg-ia)` ativo:

```bash
pip install -r requirements.txt
2. Rodar o Servidor
O servidor Uvicorn deve ser iniciado usando a porta 8080 (para evitar bloqueios de firewall). O flag --reload garante que o servidor reinicie automaticamente após salvar alterações no código.

Bash

uvicorn main:app --reload --port 8080
3. Acessar a Documentação da API
Com o servidor rodando, a documentação interativa (Swagger UI) está acessível em:

http://127.0.0.1:8080/docs

🧭 Rotas Principais da API
As rotas já estão configuradas para interagir com os dados simulados:

Método	Endpoint	Descrição	Modelo de Input
GET	/	Confirma o status da API.	N/A
GET	/groups/{group_id}	Retorna o estado completo de um grupo de chat (inclui histórico).	group-123 (ID de teste)
GET	/users/{user_id}	Retorna detalhes de um usuário.	user-1 (ID de teste)
POST	/groups/send_message	Recebe mensagem do usuário, salva, e aciona a IA.	NewMessage (JSON)
🌟 Próxima Fase: Integração e Lógica da IA
A rota POST /groups/send_message atualmente contém uma resposta simulada. O objetivo da próxima fase é:

Configurar a autenticação do Gemini API (GEMINI_API_KEY).

Implementar a lógica no main.py para iterar sobre os bots do grupo (bot-mestre, bot-npc-1).

Para cada bot, montar um prompt de sistema/histórico de chat.

Chamar o modelo gemini-2.5-flash de forma assíncrona para gerar as respostas.

Salvar as respostas geradas pelos bots no histórico do grupo (db.py).