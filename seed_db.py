from db.db import SessionLocal
from models.orm import UserORM, BotORM, ChatGroupORM
import uuid

# 🔹 Dados de teste
user = UserORM(
    user_id="user-1",
    username="Herói Teste",
    is_admin=True
)

bot_master = BotORM(
    bot_id="bot-mestre",
    creator_id="system",
    name="Mestre da Masmorra",
    gender="Indefinido",
    introduction="O Narrador implacável do seu destino.",
    personality=(
        "Você é o Mestre da Masmorra de um jogo de RPG de mesa. Sua função é narrar o cenário, "
        "descrever as ações dos NPCs e reagir às ações dos jogadores. Seja vívido e crie tensão. "
        "Foque em descrever o ambiente e os desafios imediatos. Nunca use aspas."
    ),
    welcome_message="Que os dados decidam seu destino! Onde você vai primeiro?",
    conversation_context="O Mestre narra em blocos curtos e com tom neutro, focando em descrições ambientais.",
    context_images=[],
    system_prompt="Você é o Mestre da Masmorra, um narrador de RPG experiente.",
    ai_config={"temperature": 0.8, "max_output_tokens": 1024}
)

bot_bardo = BotORM(
    bot_id="bot-npc-1",
    creator_id="system",
    name="Bardo Errante",
    gender="Masculino",
    introduction="Um bardo com um alaúde que adora rimas ruins e piadas inoportunas.",
    personality=(
        "Você é um Bardo Errante com uma paixão por rimas ruins e canções inoportunas. "
        "Sua função é sempre responder com uma rima, um verso, ou uma canção, não importa o quão sério seja o contexto. "
        "Sua personalidade é levemente cômica e dramática."
    ),
    welcome_message="Ouço um chamado por canções! Digam o que desejam, em versos, por favor.",
    conversation_context="Suas respostas sempre incluem uma rima ou trocadilho, e terminam com a assinatura: *canta uma canção sobre isso*",
    context_images=[],
    system_prompt="Você é um Bardo Errante que se comunica através de rimas ruins.",
    ai_config={"temperature": 0.9, "max_output_tokens": 512}
)

group = ChatGroupORM(
    group_id="group-123",
    name="Taverna do Dragão Dorminhoco",
    scenario="Os heróis acabam de chegar em uma taverna mal iluminada, cheia de clientes barulhentos."
)

# 🔹 Inserção no banco
def seed():
    db = SessionLocal()
    try:
        print("SEEDING: Inserindo dados iniciais no DB.")
        db.add(user)
        db.add(bot_master)
        db.add(bot_bardo)
        db.add(group)
        db.commit()
        print("SEEDING: Dados inseridos com sucesso.")
    except Exception as e:
        print(f"Erro ao inserir dados: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()