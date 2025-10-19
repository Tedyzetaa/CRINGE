# c:\cringe\3.0\add_pip_group.py

# Importa do arquivo database.py e models.py na raiz
from database import SessionLocal
from models import Group, Bot 

db = SessionLocal()

# 🔍 1. Localiza o bot 'Pimenta' (necessário para associar ao grupo)
pip_bot = db.query(Bot).filter(Bot.name == "Pimenta").first()

if not pip_bot:
    db.close()
    # Este erro é importante, pois o Bot precisa existir antes do Grupo
    raise Exception("❌ Bot 'Pimenta' não encontrado. Execute add_pip_bot.py primeiro.")

# 🏰 2. Verifica se o grupo já existe para evitar duplicatas
existing_group = db.query(Group).filter(Group.name == "Grupo da Pip").first()

if existing_group:
    print(f"Grupo 'Grupo da Pip' já existe! ID: {existing_group.id}")
    db.close()
else:
    # 🏰 3. Cria o grupo com o bot associado
    group = Group(
        name="Grupo da Pip",
        scenario="Pip se encontra em um mundo novo, e não sabe como foi parar lá",
        # Adiciona o objeto Bot à lista de 'bots' do Group
        bots=[pip_bot] 
    )

    db.add(group)
    db.commit()
    db.refresh(group)

    print(f"✅ Grupo criado com sucesso! Nome: {group.name}, ID: {group.id}")
    
    db.close()