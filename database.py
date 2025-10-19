# database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# -----------------------------------------------------------
# 1. Configuração do Banco de Dados
# -----------------------------------------------------------
DATABASE_URL = "sqlite:///./cringe.db"

# O 'check_same_thread' é necessário apenas para SQLite, 
# mas é mantido para compatibilidade com o FastAPI/SQLite.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# -----------------------------------------------------------
# 2. Criação das Tabelas
# -----------------------------------------------------------

# Importa o módulo models para que Base conheça todas as classes
# Nota: Você deve garantir que 'models.py' existe na raiz e tem suas classes ORM.
import models 

# Cria as tabelas no banco de dados se elas ainda não existirem
# Isso deve ser chamado antes de iniciar a aplicação (ex: em main.py ou em um script de inicialização)
Base.metadata.create_all(bind=engine)


# -----------------------------------------------------------
# 3. Função de Dependência (get_db)
# -----------------------------------------------------------

def get_db():
    """
    Função auxiliar para obter uma sessão de banco de dados.
    Usada como dependência nos routers do FastAPI.
    """
    db = SessionLocal()
    try:
        # Retorna a sessão, permitindo que o FastAPI a injete e a use
        yield db
    finally:
        # Garante que a sessão é fechada após a requisição, mesmo em caso de erro
        db.close()