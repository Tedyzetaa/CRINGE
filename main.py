# Seu arquivo: main.py (Backend FastAPI)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import bots
import os
import sys

# NOVO: Importa a função de inicialização/importação do DB
try:
    # Assumimos que o arquivo é init_db.py e contém a função initialize_database_with_data
    from init_db import initialize_database_with_data
except ImportError:
    # Se o nome do arquivo ou da função for diferente, você deve ajustar aqui.
    print("AVISO: Módulo 'init_db' ou função 'initialize_database_with_data' não encontrado.")
    initialize_database_with_data = None


# 1. Cria a instância do FastAPI
app = FastAPI(
    title="Cringe API",
    version="3.0",
    description="Backend API para o Cringe Bot Project",
)

# 2. Cria as tabelas do banco de dados (se não existirem)
# NOTA: Este bloco sempre deve ser executado para garantir que as tabelas existam
print("Criando tabelas no banco de dados...")
try:
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso.")
except Exception as e:
    print(f"ERRO CRÍTICO ao criar tabelas: {e}")
    sys.exit(1) # Sai se não conseguir criar as tabelas


# 3. IMPORTAÇÃO CRÍTICA PARA RENDER (Garante que os bots existam após o reset do DB)
if initialize_database_with_data:
    print("Iniciando importação de bots (necessário devido ao DB volátil do Render)...")
    try:
        initialize_database_with_data()
        print("Bots iniciais importados com sucesso.")
    except Exception as e:
        print(f"ERRO FATAL ao importar bots iniciais: {e}")
else:
    print("Função de inicialização de dados pulada. Verifique se 'init_db.py' está correto.")


# 4. Configuração de CORS
# Permite todas as origens temporariamente para facilitar o deploy no Render
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
