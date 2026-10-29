"""Gera SQL PostgreSQL revisável somente para as novas tabelas CLM."""
from pathlib import Path
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from app import db
from clm.schema import CLM_TABLES

output = Path(__file__).parent / 'migrations' / '001_clm.sql'
output.parent.mkdir(exist_ok=True)
dialect = postgresql.dialect()
statements = ['-- Esquema CLM aditivo. Não remove nem altera as tabelas legadas.', 'BEGIN;']
for table in db.metadata.sorted_tables:
    if not table.name.startswith('clm_'):
        continue
    statements.append(str(CreateTable(table, if_not_exists=True).compile(dialect=dialect)) + ';')
    statements.extend(str(CreateIndex(index, if_not_exists=True).compile(dialect=dialect)) + ';' for index in table.indexes)
statements.extend(f'ALTER TABLE {name} ENABLE ROW LEVEL SECURITY;' for name in CLM_TABLES)
statements.extend(f'REVOKE ALL ON TABLE {name} FROM anon, authenticated;' for name in CLM_TABLES)
statements.append('COMMIT;')
output.write_text('\n\n'.join(statements) + '\n', encoding='utf-8')
print('SQL gerado em api_contratos_flask/migrations/001_clm.sql')
