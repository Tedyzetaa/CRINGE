# db/repos/groups.py
from sqlalchemy.orm import Session
from typing import List

# ⚠️ Verifique se estes são os nomes corretos dos seus modelos/schemas
from models.groups import ChatGroup # Assumindo que ChatGroup é o seu modelo ORM
from models.schemas import GroupOut, GroupCreate 


def list_groups_repo(db: Session) -> List[GroupOut]:
    """
    Lista todos os grupos e converte para o schema GroupOut.
    CORREÇÃO para o Erro 500: Garante que 'bot_ids' seja serializado corretamente.
    """
    
    groups_orm = db.query(ChatGroup).all() 
    
    return [
        GroupOut(
            group_id=g.group_id,
            name=g.name,
            scenario=g.scenario,
            # 🌟 CORREÇÃO DE SERIALIZAÇÃO: Mapeia objetos Bot para lista de strings
            bot_ids=[b.bot_id for b in g.bots] 
        )
        for g in groups_orm
    ]

# Você também precisará da função de criação de grupo, chamada pelo main.py
def create_group_repo(db: Session, group_data: GroupCreate) -> ChatGroup:
    # ⚠️ IMPORTANTE: Você precisa implementar a lógica aqui para:
    # 1. Buscar os objetos Bot (ORM) com base nos group_data.bot_ids
    # 2. Criar uma nova instância de ChatGroup com os objetos Bot relacionados
    # 3. Adicionar e commitar a instância no DB
    pass