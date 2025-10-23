# c:\cringe\3.0\init_db.py

import os
import json
from sqlalchemy.orm import Session
from database import SessionLocal 

# CORRIGIDO: De AICofig para AIConfig.
try:
    from models import Bot, AIConfig 
except ImportError:
    print("ERRO: Certifique-se de que 'models.py' e as classes 'Bot'/'AIConfig' estão disponíveis.")
    Bot = None
    AIConfig = None
    
BOTS_DATA_FILE = "pimenta_import.json" 

def initialize_database_with_data():
    """
    Inicializa/popula o banco de dados com dados de bots.
    """
    if not Bot or not AIConfig:
        print("❌ Inicialização de dados pulada: Modelos de DB não encontrados.")
        return
    
    if not os.path.exists(BOTS_DATA_FILE):
        print(f"❌ ERRO DE IMPORTAÇÃO: Arquivo de dados '{BOTS_DATA_FILE}' não encontrado. Pulando importação.")
        return

    try:
        with open(BOTS_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        bots_to_import = data.get('bots', [])
        print(f"Lido {len(bots_to_import)} bots do arquivo JSON.")
    except Exception as e:
        print(f"❌ ERRO ao carregar dados: {e}. Pulando importação.")
        return

    db: Session = SessionLocal()
    
    try:
        if db.query(Bot).first():
            print("✅ Bots já existem no banco de dados. Pulando importação.")
            return

        for bot_data in bots_to_import:
            
            bot_data.pop('id', None)
            
            # 1. Extrai e constrói a AI Config (usando AIConfig)
            ai_config_data = bot_data.pop('ai_config', {})
            ai_config_instance = AIConfig(**ai_config_data)

            # 2. Constrói o objeto Bot
            new_bot = Bot(
                **{k: v for k, v in bot_data.items() if hasattr(Bot, k)},
                ai_config=ai_config_instance
            )
            
            db.add(new_bot)
            
        db.commit()
        print("✅ Todos os bots iniciais importados com sucesso.")
    
    except Exception as e:
        db.rollback()
        print(f"❌ ERRO durante a inserção de bots no DB: {e}")
        
    finally:
        db.close()
