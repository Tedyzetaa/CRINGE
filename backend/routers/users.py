# c:\cringe\3.0\routers\users.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError 
from database import get_db
# Importa apenas os Schemas e ORMs necessários
from models import User, UserRead, UserCreate 

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    """Lista todos os usuários do banco de dados."""
    return db.query(User).all()

@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Encontra o usuário pelo nome ou o cria se ele não existir."""
    
    # 1. Tenta encontrar o usuário existente
    existing_user = db.query(User).filter(User.name == user.name).first()
    if existing_user:
        return existing_user
        
    # 2. Se não existir, tenta criar o novo usuário
    db_user = User(name=user.name)
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    except IntegrityError:
        # Lógica de fallback caso uma condição de corrida ocorra
        db.rollback()
        return db.query(User).filter(User.name == user.name).first()