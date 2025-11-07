# db/repos/users.py

from sqlalchemy.orm import Session
from models.orm import UserORM
from models.schemas import UserCreate
from typing import List
from models.schemas import UserOut # Incluindo UserOut para o list

def create_user_repo(db: Session, user_data: UserCreate):
    """Cria ou atualiza (UPSERT) um usuário no banco de dados."""
    
    # 1. TENTA ENCONTRAR O USUÁRIO PRIMEIRO
    existing_user = db.query(UserORM).filter(UserORM.user_id == user_data.user_id).first()
    
    if existing_user:
        # 2. Se o usuário já existe, APENAS ATUALIZA
        existing_user.username = user_data.username
        existing_user.is_admin = user_data.is_admin
        db.commit()
        db.refresh(existing_user)
        return existing_user
    
    # 3. Se não existe, CRIA UM NOVO - Mapeamento explícito para segurança
    db_user = UserORM(
        user_id=user_data.user_id,
        username=user_data.username,
        is_admin=user_data.is_admin,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def list_users_repo(db: Session) -> List[UserOut]:
    """Lista todos os usuários."""
    users_orm = db.query(UserORM).all() 
    
    # Converte os objetos ORM para o schema Pydantic de saída (UserOut)
    # Isso garante que a API retorne um JSON estruturado
    return [UserOut.model_validate(u) for u in users_orm]
