# db/repos/bots.py (CORRIGIDO)
from sqlalchemy.orm import Session
# ⚠️ Importe o modelo ORM com o alias (se o nome for longo)
from models.orm import BotORM
# ⚠️ Importe o schema de entrada e o schema de SAÍDA (BotOut)
from models.schemas import BotCreate, BotOut
from typing import List

def create_bot_repo(db: Session, bot_data: BotCreate) -> BotORM:
    # A criação está correta (retorna o objeto ORM)
    bot = BotORM(**bot_data.model_dump())
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot

# 💥 CORREÇÃO AQUI: O retorno deve ser uma lista de BotOut (Pydantic)
def list_bots_repo(db: Session) -> List[BotOut]:
    """
    Busca os objetos ORM e os converte para o schema Pydantic BotOut,
    garantindo que o JSON da API contenha a chave 'bot_id' para o frontend.
    """
    bots_orm = db.query(BotORM).all() 
    
    # 🌟 Solução: Usa model_validate para converter a lista de objetos ORM
    # para a lista de schemas Pydantic (BotOut).
    return [BotOut.model_validate(b) for b in bots_orm]