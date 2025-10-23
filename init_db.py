# c:\cringe\3.0\init_db.py

import os
import json
from sqlalchemy.orm import Session
from database import SessionLocal # Importa a função para criar sessões
# Importe seus modelos: Certifique-se de que os nomes Bot e AIConfig estão corretos
# Se seus modelos estiverem em models.py, a importação deve ser assim:
try:
    from models import Bot, AICofig
except ImportError:
    # Fallback se a importação falhar (para evitar quebrar o main.py)
    print("ERRO: Certifique-se de que 'models.py' e as classes 'Bot'/'AICofig' estão disponíveis.")
    Bot = None
    AICofig = None
    
# Nome do arquivo JSON contendo os dados dos bots para importação
# (Ajuste este nome se o seu arquivo for outro)
BOTS_DATA_FILE = "pimenta_import.json" 

def initialize_database_with_data():
    """
    Inicializa/popula o banco de dados com dados de bots.
    Esta função é chamada pelo main.py para garantir que os dados existam
    sempre que o servidor é reiniciado no Render (DB volátil).
    """
    if not Bot or not AICofig:
        print("❌ Inicialização de dados pulada: Modelos de DB não encontrados.")
        return
        
    if not os.path.exists(BOTS_DATA_FILE):
        print(f"❌ ERRO DE IMPORTAÇÃO: Arquivo de dados '{BOTS_DATA_FILE}' não encontrado. Pulando importação.")
        return

    # Tenta ler o arquivo JSON
    try:
        with open(BOTS_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        bots_to_import = data.get('bots', [])
        print(f"Lido {len(bots_to_import)} bots do arquivo JSON.")
    except json.JSONDecodeError:
        print(f"❌ ERRO: O arquivo '{BOTS_DATA_FILE}' não é um JSON válido. Pulando importação.")
        return
    except Exception as e:
        print(f"❌ ERRO ao carregar dados: {e}. Pulando importação.")
        return

    # Inicia uma sessão de DB
    db: Session = SessionLocal()
    
    try:
        for bot_data in bots_to_import:
            
            # Remove o ID para que o SQLAlchemy trate a chave primária
            bot_id = bot_data.pop('id', None)
            
            # Verifica se o bot já existe pelo nome ou outro campo exclusivo, se necessário.
            # Como o DB é limpo no Render, focamos na inserção direta.

            # 1. Extrai e constrói a AI Config
            ai_config_data = bot_data.pop('ai_config', {})
            
            # Se a AIConfig for uma relação 1:1, crie a instância.
            ai_config_instance = AICofig(**ai_config_data)

            # 2. Constrói o objeto Bot
            new_bot = Bot(
                # Mapeia campos simples do JSON para o modelo Bot
                **{k: v for k, v in bot_data.items() if hasattr(Bot, k)},
                
                # Adiciona a instância de AI Config
                ai_config=ai_config_instance
            )
            
            db.add(new_bot)
            print(f"✅ Bot '{new_bot.name}' importado com sucesso (ID: {bot_id or 'novo'}).")

        # Commita todas as alterações
        db.commit()
    
    except Exception as e:
        db.rollback()
        print(f"❌ ERRO durante a inserção de bots no DB: {e}")
        
    finally:
        db.close()
