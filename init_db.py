# init_db.py

import os
import json
from sqlalchemy.orm import Session
from database import SessionLocal 

# CORRIGIDO: Removida a importação de AIConfig. Usamos apenas Bot.
try:
    from models import Bot
except ImportError:
    # Esta mensagem de erro será exibida se models.py ou a classe Bot não for encontrada.
    print("ERRO: Certifique-se de que 'models.py' e a classe 'Bot' estão disponíveis.")
    Bot = None
    
# Nome do arquivo de dados para importação
BOTS_DATA_FILE = "pimenta_import.json" 

def initialize_database_with_data():
    """
    Inicializa/popula o banco de dados com dados de bots.
    Serializa os campos 'ai_config' e 'tags' de volta para strings JSON.
    """
    # Verifica se a classe Bot está disponível
    if not Bot:
        print("❌ Inicialização de dados pulada: Modelo de DB Bot não encontrado.")
        return
    
    # Verifica se o arquivo de dados existe
    if not os.path.exists(BOTS_DATA_FILE):
        print(f"❌ ERRO DE IMPORTAÇÃO: Arquivo de dados '{BOTS_DATA_FILE}' não encontrado. Pulando importação.")
        return

    # Tenta carregar os dados do arquivo JSON
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
        # Verifica se já existem bots para evitar reimportação em DBs persistentes
        if db.query(Bot).first():
            print("✅ Bots já existem no banco de dados. Pulando importação.")
            return

        for bot_data in bots_to_import:
            
            # 1. Extrai o dicionário de configurações de AI
            ai_config_data = bot_data.pop('ai_config', None)
            
            # 2. Serializa as configurações de AI em JSON string para o campo 'ai_config_json'
            if ai_config_data:
                bot_data['ai_config_json'] = json.dumps(ai_config_data) 
            else:
                bot_data['ai_config_json'] = json.dumps({}) 
                
            # 3. Serializa a lista de tags em JSON string
            tags_list = bot_data.pop('tags', [])
            if tags_list:
                bot_data['tags'] = json.dumps(tags_list)
            else:
                bot_data['tags'] = json.dumps([])

            # 4. Constrói o objeto Bot (filtrando chaves para apenas aquelas existentes no modelo)
            fields_to_keep = [c.key for c in Bot.__table__.columns]
            
            new_bot_data = {}
            for k, v in bot_data.items():
                if k in fields_to_keep:
                     new_bot_data[k] = v

            new_bot = Bot(**new_bot_data)
            
            db.add(new_bot)
            
        db.commit()
        print("✅ Todos os bots iniciais importados com sucesso.")
    
    except Exception as e:
        db.rollback()
        print(f"❌ ERRO CRÍTICO durante a inserção de bots no DB: {e}")
        
    finally:
        db.close()
