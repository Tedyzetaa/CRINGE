from fastapi import FastAPI
from routers import users, bots, groups

app = FastAPI(title="CRINGE RPG-AI API")

# Registrando os routers
app.include_router(users.router)
app.include_router(bots.router)
app.include_router(groups.router)

@app.get("/")
def root():
    return {"message": "Servidor CRINGE RPG-AI rodando com sucesso!"}
