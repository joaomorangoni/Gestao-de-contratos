"""Inicializa o esquema sem exibir credenciais em mensagens de erro."""
from app import app, db
from sqlalchemy.exc import SQLAlchemyError

with app.app_context():
    try:
        db.create_all()
        print('Supabase conectado. Tabelas prontas.')
    except SQLAlchemyError as exc:
        print(f'Falha de conexão: {exc.orig}')
        raise SystemExit(1)
