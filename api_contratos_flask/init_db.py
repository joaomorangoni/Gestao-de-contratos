"""Inicializa o esquema sem exibir credenciais em mensagens de erro."""
from app import app, db
from sqlalchemy.exc import SQLAlchemyError
from clm.schema import protect_supabase_tables

with app.app_context():
    try:
        db.create_all()
        protect_supabase_tables()
        print('Supabase conectado. Tabelas prontas.')
    except SQLAlchemyError as exc:
        print(f'Falha de conexão: {exc.orig}')
        raise SystemExit(1)
