# database.py
# Este arquivo configura a conexão com o banco de dados e a dependência do FastAPI.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# ⚠️ Nota: Para um ambiente de produção como Render/Heroku, você deve usar
# uma variável de ambiente, como abaixo, em vez de um arquivo SQLite local.
# Exemplo para PostgreSQL: DATABASE_URL = os.environ.get("DATABASE_URL")
# Para o nosso exemplo local, mantemos o SQLite:
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"  

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # Necessário apenas para SQLite, pois impede que múltiplas threads
    # tentem acessar a mesma conexão.
    connect_args={"check_same_thread": False} 
)

# A sessão de banco de dados que será usada pelas funções de CRUD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para declarar as classes de modelo (tables)
Base = declarative_base()

# Dependência do Banco de Dados para FastAPI
def get_db():
    """Retorna uma sessão de DB e garante que ela seja fechada após o uso (dependency injector)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
