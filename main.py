# c:\cringe\3.0\main.py (VERSÃO CORRIGIDA)

from fastapi import FastAPI
from database import engine, Base # Importa o engine e o Base
from routers import users, bots, groups # Roteadores principais
# Remova esta linha: from routers import import_data 
import models # Garante que os modelos sejam carregados para o Base.metadata

# ⚠️ CRIA AS TABELAS NO BANCO DE DADOS
Base.metadata.create_all(bind=engine) 

app = FastAPI(title="CRINGE RPG-AI API", version="0.1.0")

# --- Inclusão dos Roteadores ---

app.include_router(users.router)
app.include_router(bots.router)
app.include_router(groups.router)

# Remova esta linha: app.include_router(import_data.router) 

# --- Endpoint Raiz ---

@app.get("/")
def read_root():
    return {"message": "CRINGE RPG-AI API está rodando! Chame o /docs para ver a documentação."}