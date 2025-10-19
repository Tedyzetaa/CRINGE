# c:\cringe\3.0\main.py (BLOCO ATUALIZADO)

from fastapi import FastAPI
from database import engine, Base # Importa o engine e o Base
from routers import users, bots, groups
# Importe models para que o Base saiba quais tabelas criar
import models 

# ⚠️ CRIA AS TABELAS NO BANCO DE DADOS (SQLite ou PostgreSQL)
# Se você tiver a flag --reload, ele pode rodar várias vezes localmente, mas é necessário no deploy.
Base.metadata.create_all(bind=engine) 

app = FastAPI(title="CRINGE RPG-AI API", version="0.1.0")

app.include_router(users.router)
app.include_router(bots.router)
app.include_router(groups.router)

@app.get("/")
def read_root():
    return {"message": "CRINGE RPG-AI API está rodando!"}