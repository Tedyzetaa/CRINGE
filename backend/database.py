from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

def get_database_url():
    """Obtém a URL do banco de dados de forma segura para Render"""
    
    # No Render, a DATABASE_URL é fornecida automaticamente para PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Corrige PostgreSQL URL se necessário
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        print(f"🔗 Usando PostgreSQL no Render")
        return database_url
    else:
        # Desenvolvimento local com SQLite
        print(f"🔗 Usando SQLite local")
        return "sqlite:///./sql_app.db"

SQLALCHEMY_DATABASE_URL = get_database_url()

# Configuração do engine
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL no Render
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()