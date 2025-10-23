# main.py (Backend FastAPI)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import bots
import sys

try:
    from init_db import initialize_database_with_data
except ImportError:
    print("AVISO: Módulo 'init_db' não encontrado. Importação automática de bots desabilitada.")
    initialize_database_with_data = None


# 1. Cria a instância do FastAPI
app = FastAPI(
    title="Cringe API",
    version="3.0",
    description="Backend API para o Cringe Bot Project",
)

# 2. Cria as tabelas do banco de dados (se não existirem)
print("Criando tabelas no banco de dados...")
try:
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso.")
except Exception as e:
    print(f"ERRO CRÍTICO ao criar tabelas: {e}")
    sys.exit(1)


# 3. IMPORTAÇÃO CRÍTICA PARA RENDER (Popula o DB)
if initialize_database_with_data:
    print("Iniciando importação de bots (necessário devido ao DB volátil do Render)...")
    try:
        initialize_database_with_data()
        print("Bots iniciais importados com sucesso.")
    except Exception as e:
        print(f"ERRO FATAL ao importar bots iniciais: {e}")
else:
    print("Função de inicialização de dados pulada.")


# 4. Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 5. Inclusão dos Roteadores
app.include_router(bots.router)


# 6. Rota Raiz Simples
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Cringe API V3.0 is running."}
