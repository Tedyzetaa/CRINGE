# c:\cringe\3.0\database.py (ATUALIZADO PARA POSTGRES/RENDER)

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Tenta obter a URL do banco de dados do ambiente (Render)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render usa PostgreSQL, mas o driver psycopg2 usa 'postgresql'
    # Esta substituição é comum em deploys
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Cria o motor para PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        # O pool_pre_ping é bom para manter a conexão viva em ambientes de nuvem
        pool_pre_ping=True
    )
    print("INFO: Usando PostgreSQL com DATABASE_URL.")
else:
    # Fallback para SQLite local (para desenvolvimento)
    SQLALCHEMY_DATABASE_URL = "sqlite:///./cringe.db"
    
    # Cria o motor para SQLite
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}, # Necessário para SQLite em FastAPI
    )
    print("INFO: Usando SQLite localmente.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Função para dependência do FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Importe os modelos em seu main.py e chame Base.metadata.create_all(bind=engine)
# para garantir que as tabelas sejam criadas.