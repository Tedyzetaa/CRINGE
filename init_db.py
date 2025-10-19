# c:\cringe\3.0\init_db.py

import database

# Ao importar 'database', o código dentro dele é executado,
# incluindo a linha 'Base.metadata.create_all(bind=engine)'
# que cria o arquivo cringe.db e todas as tabelas.

print("✅ O banco de dados cringe.db e as tabelas foram checados/criados com sucesso.")

# Para fins de demonstração, podemos tentar fechar uma sessão, embora não seja estritamente necessário
# apenas para o Base.metadata.create_all.
try:
    db = database.SessionLocal()
    db.close()
    print("Sessão de banco de dados fechada.")
except Exception:
    pass