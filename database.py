# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Adicione esta importação para manipular JSON (útil para listas no SQLAlchemy)
from sqlalchemy import JSON 

# URL do seu banco de dados
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"  
# Se for PostgreSQL, seria algo como: 
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host:port/dbname"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} # Permite threads no SQLite
    # Remova o connect_args se estiver usando um DB em rede (como PostgreSQL)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
