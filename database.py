# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Define o URL de conexão com o banco de dados.
# Vamos usar SQLite para desenvolvimento (cria um arquivo 'sql_app.db' no diretório raiz)
# Para produção no Render/Heroku, você mudaria isso para um URL de PostgreSQL/MySQL
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# O 'check_same_thread=False' é necessário apenas para SQLite
# para permitir múltiplas requisições em threads diferentes.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Cria uma SessionLocal, que será usada para cada requisição de banco de dados.
# O 'autocommit=False' e 'autoflush=False' garante que a transação deve ser fechada manualmente.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para todos os modelos de dados (tabelas) que criaremos.
Base = declarative_base()

# --- Função de Dependência (Generator) ---
# Usada pelo FastAPI para obter a sessão de banco de dados para cada rota.
def get_db():
    """
    Cria uma sessão DB para a requisição e garante que ela seja fechada.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()