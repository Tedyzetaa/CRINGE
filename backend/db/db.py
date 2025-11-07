# c:\cringe\3.0\db\db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ⚠️ Verifique se sua URL está correta (exemplo para SQLite):
SQLALCHEMY_DATABASE_URL = "sqlite:///./rpg_ia.db" 

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 💡 A função get_db AGORA está no db/db.py
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()