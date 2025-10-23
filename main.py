# Seu arquivo: main.py (Backend FastAPI)

# NOVO: Importa a função para carregar variáveis do arquivo .env
from dotenv import load_dotenv

# NOVO: Carrega variáveis de ambiente (como HF_API_TOKEN) do arquivo .env
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import bots # Certifique-se de que o nome 'bots' está correto
# Outros roteadores que você possa ter (ex: from routers import groups, users)

# 1. Cria a instância do FastAPI
app = FastAPI(
    title="Cringe API",
    version="3.0",
    description="Backend API para o Cringe Bot Project",
)

# 2. Cria as tabelas do banco de dados (se não existirem)
# Nota: Em produção, você pode preferir usar ferramentas de migração como Alembic.
Base.metadata.create_all(bind=engine)

# 3. Configuração de CORS (Essencial para o Streamlit rodar em outra URL, como o Render)
# Certifique-se de que a origem do seu Streamlit esteja aqui
origins = [
    # Adicione a URL completa do seu Frontend Streamlit aqui, se for diferente
    "http://localhost:8501",   # Localhost Streamlit
    "http://127.0.0.1:8501", # Outra versão de localhost
    "https://cringe-8h21.onrender.com" # Se esta for a URL do seu Streamlit
    # Você pode adicionar "*" durante o desenvolvimento, mas é menos seguro em produção
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permitindo tudo temporariamente para evitar problemas de CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 4. Inclusão dos Roteadores
# Monta as rotas para /bots
app.include_router(bots.router)
# app.include_router(groups.router) # Exemplo: se tiver outras rotas
# app.include_router(users.router)   # Exemplo: se tiver outras rotas


# 5. Rota Raiz Simples (Para testar se a API está no ar)
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Cringe API V3.0 is running."}

# Nota: O comando de inicialização no Render deve ser:
# uvicorn main:app --host 0.0.0.0 --port $PORT