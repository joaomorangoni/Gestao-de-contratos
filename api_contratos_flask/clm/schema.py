from sqlalchemy import text
from extensions import db

CLM_TABLES = ('clm_user', 'clm_request', 'clm_approval', 'clm_attachment', 'clm_contract')


def protect_supabase_tables():
    """A API usa o papel postgres; anon/authenticated não acessam via Data API."""
    if db.engine.dialect.name == 'postgresql':
        for name in CLM_TABLES:
            # Identificadores são constantes internas, nunca entrada do usuário.
            db.session.execute(text(f'ALTER TABLE {name} ENABLE ROW LEVEL SECURITY'))
            for role in ('anon', 'authenticated'):
                exists = db.session.scalar(text('SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role)'), {'role': role})
                if exists:
                    db.session.execute(text(f'REVOKE ALL ON TABLE {name} FROM {role}'))
        db.session.commit()
