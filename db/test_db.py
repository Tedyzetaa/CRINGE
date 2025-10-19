from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.orm import Base

# Banco de dados de testes
TEST_DATABASE_URL = "sqlite:///test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)