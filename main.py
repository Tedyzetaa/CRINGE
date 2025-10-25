from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import bots
import os

print("🚀 Iniciando CRINGE API no Render...")

# Validações iniciais
if not os.getenv("OPENROUTER_API_KEY"):
    print("❌ ERRO: OPENROUTER_API_KEY não encontrada!")
    print("💡 Configure OPENROUTER_API_KEY no Render Dashboard")
    # Não saia em produção, apenas log o erro

# Cria a instância do FastAPI
app = FastAPI(
    title="CRINGE API",
    version="3.1",
    description="Backend API para o Cringe Bot Project",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS para produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja para seus domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas
try:
    print("📊 Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso!")
except Exception as e:
    print(f"❌ Erro ao criar tabelas: {e}")

# Inclui rotas
app.include_router(bots.router)

# Rotas básicas
@app.get("/")
def read_root():
    return {
        "status": "ok", 
        "message": "CRINGE API rodando no Render!",
        "version": "3.1",
        "ai_provider": "OpenRouter"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "environment": "production"}

# Não use __main__ no Render - o Render executa uvicorn diretamente