# c:\cringe\3.0\export_data.py (Versão Final de Localização)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Bot, Group, Message 
import json
import os

# Conexão com o seu banco de dados SQLite local
SQLALCHEMY_DATABASE_URL = "sqlite:///./cringe.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_local_data():
    """Lê os dados e os formata em JSON."""
    db = SessionLocal()
    data = {}
    
    # 1. Exportar Bots
    bots_list = []
    for bot in db.query(Bot).all():
        bots_list.append({
            "id": bot.id,
            "name": bot.name,
            "personality": bot.personality,
            "system_prompt": bot.system_prompt,
            # Inclua todos os campos importantes que você quer preservar
            "creator_id": bot.creator_id,
            "gender": bot.gender,
            "introduction": bot.introduction,
            "welcome_message": bot.welcome_message,
            "ai_config": bot.ai_config,
        })
    data['bots'] = bots_list

    # 2. Exportar Usuários
    users_list = []
    for user in db.query(User).all():
         users_list.append({
             "id": user.id,
             "name": user.name,
         })
    data['users'] = users_list

    # NOTA: Grupos e Mensagens não estão incluídos aqui para manter a simplicidade, 
    # mas o esquema de Bots/Usuários já permite recriar o ambiente base.

    db.close()
    return data

if __name__ == "__main__":
    exported_data = get_local_data()
    
    # --- Lógica para forçar o caminho de saída ---
    
    # Obtém o diretório do script, que deve ser C:\cringe\3.0
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file_path = os.path.join(script_dir, "exported_test_data.json")

    try:
        # Tenta criar e salvar o arquivo
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(exported_data, f, indent=4, ensure_ascii=False)
        
        print("\n" + "="*50)
        print("✅ SUCESSO! Dados exportados.")
        print(f"O arquivo foi criado em:")
        print(f"🔗 {output_file_path}")
        print("="*50 + "\n")

    except Exception as e:
        print(f"❌ ERRO GRAVE: Não foi possível gravar o arquivo. Detalhes: {e}")
        print("Verifique permissões de escrita na pasta.")