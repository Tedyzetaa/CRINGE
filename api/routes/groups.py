# api/routes/groups.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Importe suas dependências de DB e Repositório
from db.db import get_db 
from db.repos.groups import list_groups_repo 

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.get("/") # Esta rota será acessível via /groups/
def list_groups(db: Session = Depends(get_db)):
    # Chama o repositório corrigido
    return list_groups_repo(db) 

# Você também precisa da rota POST para criar grupos
# Você pode adicionar a rota aqui:
# from models.schemas import GroupIn
# @router.post("/", status_code=201)
# def create_group_endpoint(group_in: GroupIn, db: Session = Depends(get_db)):
#     # ... chame a função de criação de grupo do repositório
#     pass