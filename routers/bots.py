import uuid
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# --- MOCK DATABASE (Para simular o armazenamento) ---
# Em um ambiente real, esta seria sua coleção do MongoDB/Firestore/SQLAlchemy
MOCK_BOTS_DB: Dict[str, Dict[str, Any]] = {}

# Adiciona um bot inicial para testes
initial_bot_id = str(uuid.uuid4())
MOCK_BOTS_DB[initial_bot_id] = {
    "id": initial_bot_id,
    "creator_id": "user-admin",
    "name": "Prof. Sarcástico",
    "gender": "Masculino",
    "introduction": "Um professor universitário aposentado que adora criticar clichês de RPG.",
    "personality": "Sarcástico, cínico, mas secretamente carinhoso. Responde com humor seco.",
    "welcome_message": "Ah, olá. Mais um tentando a glória? Que original.",
    "avatar_url": "https://placehold.co/100x100/1e293b/f8fafc?text=PS",
    "tags": ["Educador", "Cínico", "RPG"],
    "conversation_context": "",
    "context_images": "",
    "system_prompt": "Você é o Professor Sarcástico, use um tom cínico e faça piadas sobre a situação.",
    "ai_config": {"temperature": 0.8, "max_output_tokens": 512}
}


# --- MODELOS PYDANTIC ---

class AIConfig(BaseModel):
    """Configurações de Geração da IA."""
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_output_tokens: int = Field(512, ge=128, le=4096)

class BotBase(BaseModel):
    """Campos base para criação e exportação/importação."""
    name: str = Field(..., max_length=100)
    gender: str
    introduction: str
    personality: str
    welcome_message: str
    avatar_url: str = ""
    tags: List[str] = Field(default_factory=list)
    conversation_context: str = ""
    context_images: str = ""
    system_prompt: str
    # Aceita Dict[str, Any] para robustez ou AIConfig (Pydantic faz a conversão)
    ai_config: Dict[str, Any] 

class BotCreate(BotBase):
    """Modelo usado para receber dados no POST /bots/."""
    creator_id: str

class Bot(BotCreate):
    """Modelo completo com ID, usado para listar e detalhar."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class BotListFile(BaseModel):
    """Modelo usado para Importação e Exportação de arquivos JSON."""
    bots: List[Bot]


router = APIRouter(prefix="/bots", tags=["Bots"])

# --- ENDPOINTS ---

@router.get("/", response_model=List[Bot], summary="Listar todos os Bots")
def get_all_bots():
    """Retorna a lista de todos os bots criados."""
    return list(MOCK_BOTS_DB.values())

@router.get("/{bot_id}", response_model=Bot, summary="Obter detalhes do Bot")
def get_bot_details(bot_id: str):
    """Retorna os detalhes de um bot específico."""
    if bot_id not in MOCK_BOTS_DB:
        raise HTTPException(status_code=404, detail="Bot não encontrado")
    return MOCK_BOTS_DB[bot_id]


@router.post("/", response_model=Bot, status_code=201, summary="Criar um novo Bot")
def create_bot(bot: BotCreate):
    """
    Cria um novo Bot no sistema.
    Corrige o erro de 'AttributeError' tratando ai_config como dict.
    """
    
    # Gerar um ID único para o novo bot
    new_bot_id = str(uuid.uuid4())

    # --- INÍCIO DA CORREÇÃO DO ERRO 'AttributeError: 'dict' object has no attribute 'model_dump'' ---
    
    # Verifica se ai_config é um dicionário (o que causou o erro) ou um modelo Pydantic.
    # Se já é um dict, usamos ele. Caso contrário, chamamos model_dump() (o padrão Pydantic).
    if isinstance(bot.ai_config, dict):
        ai_config_dict = bot.ai_config
    else:
        # Esta linha é a lógica padrão se o campo tivesse sido validado como um sub-modelo Pydantic
        ai_config_dict = bot.ai_config.model_dump() 
        
    # --- FIM DA CORREÇÃO ---
    
    # Criar o dicionário final para salvar no mock DB
    bot_data = bot.model_dump(exclude_none=True)
    bot_data["id"] = new_bot_id
    bot_data["ai_config"] = ai_config_dict
    
    MOCK_BOTS_DB[new_bot_id] = bot_data
    
    return bot_data

@router.put("/import", summary="Importar Bots a partir de um JSON", response_model=Dict[str, Any])
def import_bots(file_data: BotListFile):
    """
    Importa uma lista de bots a partir de um arquivo JSON (BotListFile).
    Os bots existentes com o mesmo ID serão substituídos (UPSERT).
    """
    imported_count = 0
    
    for bot in file_data.bots:
        # Convertendo o modelo Bot (que tem o ID) para um dicionário
        bot_dict = bot.model_dump(exclude_none=True)
        
        # Simula a inserção ou substituição (upsert)
        MOCK_BOTS_DB[bot_dict["id"]] = bot_dict
        imported_count += 1
        
    return {"success": True, "imported_count": imported_count, "message": f"{imported_count} bot(s) importado(s) com sucesso."}

@router.get("/export", response_model=BotListFile, summary="Exportar Todos os Bots para JSON")
def export_bots():
    """
    Retorna todos os bots em formato BotListFile, ideal para exportação.
    """
    # Cria instâncias do modelo Bot a partir do Mock DB para garantir a validação de saída
    bots_list = [Bot(**data) for data in MOCK_BOTS_DB.values()]
    return BotListFile(bots=bots_list)
