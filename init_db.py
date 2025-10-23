# c:\cringe\3.0\init_db.py

import os
import json
from sqlalchemy.orm import Session
from database import SessionLocal # Importa a função para criar sessões
from models import Bot, AICofig # Assumindo que Bot e AIConfig estão em models.py

# Nome do arquivo JSON contendo os dados dos bots para importação
BOTS_DATA_FILE = "pimenta_import.json" 

def initialize_database_with_data():
    """
    Inicializa/popula o banco de dados com dados de bots.
    Esta função é chamada pelo main.py para garantir que os dados existam
    sempre que o servidor é reiniciado no Render (DB volátil).
    """
    if not os.path.exists(BOTS_DATA_FILE):
        print(f"❌ ERRO DE IMPORTAÇÃO: Arquivo de dados '{BOTS_DATA_FILE}' não encontrado.")
        return

    # Tenta ler o arquivo JSON
    try:
        with open(BOTS_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        bots_to_import = data.get('bots', [])
    except json.JSONDecodeError:
        print(f"❌ ERRO: O arquivo '{BOTS_DATA_FILE}' não é um JSON válido.")
        return
    except Exception as e:
        print(f"❌ ERRO ao carregar dados: {e}")
        return

    # Inicia uma sessão de DB
    db: Session = SessionLocal()
    
    try:
        for bot_data in bots_to_import:
            # Tenta encontrar o bot pelo ID para evitar duplicação (Embora no Render,
            # como o DB é limpo, é mais simples recriar)
            existing_bot = db.query(Bot).filter(Bot.id == bot_data.get("id")).first()

            if existing_bot:
                print(f"⚠️ Bot '{bot_data['name']}' já existe. Pulando importação.")
                continue

            # Cria a configuração de AI (se a estrutura for aninhada)
            ai_config_data = bot_data.pop('ai_config', {})
            
            # Cria a instância do bot
            new_bot = Bot(
                # Mapeia campos simples
                **{k: v for k, v in bot_data.items() if k in Bot.__table__.columns},
                
                # Mapeia a AI Config (adapte conforme seu modelo)
                ai_config=AICofig(**ai_config_data) 
            )
            
            db.add(new_bot)
            print(f"✅ Bot '{new_bot.name}' importado com sucesso.")

        # Commita todas as alterações
        db.commit()
    
    except Exception as e:
        db.rollback()
        print(f"❌ ERRO durante a inserção de bots no DB: {e}")
        
    finally:
        db.close()

# Para fins de teste, você pode descomentar esta seção:
# if __name__ == "__main__":
#     print("Iniciando inicialização do DB...")
#     initialize_database_with_data()
#     print("Finalizado.")
