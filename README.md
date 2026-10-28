# Gestor de Contratos — Accordo

Aplicação local de gestão de contratos com frontend React e API Flask conectada ao PostgreSQL do Supabase.

## Funcionalidades

- Visão geral com quantidade de contratos, valor do portfólio, contratos ativos e vencimentos nos próximos 30 dias.
- Busca e filtro de contratos por status.
- Cadastro, edição e exclusão de clientes, responsáveis, contratos, cláusulas e aditivos.
- Histórico automático quando o status de um contrato é alterado.
- Documentação da API em `/swagger/` e verificação da conexão em `/health`.

## Estrutura

- `api_contratos_flask/`: API, modelos SQLAlchemy, inicialização e testes.
- `frontend/`: React, Vite e estilos responsivos.
- `backend/cliente.py`: cliente de terminal opcional para a API.
- `iniciar.ps1`: inicia a API e o frontend em segundo plano no Windows.

## Configuração

Use Python 3.10 ou superior e Node.js 20.19+ ou 22.12+.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r api_contratos_flask/requirements.txt
npm.cmd install --prefix frontend
Copy-Item api_contratos_flask/.env.example api_contratos_flask/.env
```

Se o comando `python` for um atalho sem instalação, use o caminho completo do executável Python instalado.

Edite `api_contratos_flask/.env` com a conexão PostgreSQL do seu projeto. O arquivo local já foi configurado nesta instalação. Não envie a senha ao repositório nem ao frontend.

```dotenv
DATABASE_URL=postgresql://postgres:SUA_SENHA@db.fzkhvucaccgfwevctmnn.supabase.co:5432/postgres
DB_SSLMODE=require
```

Alternativamente, sem `DATABASE_URL`, use `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`. A conexão utiliza SSL por padrão. Caracteres reservados da senha devem ser codificados em URLs.

A conexão direta do Supabase requer IPv6 quando o projeto não possui o adicional IPv4. Esta máquina não conseguiu alcançar o endereço IPv6 do projeto. Para redes somente IPv4, copie a conexão de **Connect → Session pooler** no painel Supabase e substitua `DATABASE_URL` no `.env`. Copie o host real do painel; o usuário do pooler tem o formato `postgres.REFERENCIA_DO_PROJETO`.

Referência: https://supabase.com/docs/guides/database/connecting-to-postgres

## Inicializar o banco

Depois de configurar uma conexão acessível:

```powershell
.venv\Scripts\python.exe api_contratos_flask/init_db.py
```

O comando cria somente tabelas ausentes. Não apaga tabelas nem importa o banco antigo. Alterações futuras no esquema de tabelas existentes precisarão de migrações.

## Executar localmente

```powershell
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
```

- Interface: http://127.0.0.1:5173
- API: http://127.0.0.1:5000
- Swagger: http://127.0.0.1:5000/swagger/

Ou execute cada serviço em um terminal:

```powershell
.venv\Scripts\python.exe api_contratos_flask/app.py
```

```powershell
npm.cmd run dev --prefix frontend
```

O Vite encaminha `/api/*` para a API Flask. A credencial PostgreSQL permanece exclusivamente no servidor. Comece cadastrando um cliente e, em seguida, um contrato. Responsáveis são opcionais. As exclusões podem ser bloqueadas quando existem registros vinculados.

Os logs dos serviços iniciados pelo script ficam em `.runtime/`. Os identificadores ficam em `.runtime/processos.json` e podem ser usados com `Stop-Process -Id NUMERO` para encerrar os serviços.

## Verificações

```powershell
.venv\Scripts\python.exe -m unittest discover -s api_contratos_flask -v
npm.cmd run build --prefix frontend
```

Os testes usam SQLite em memória, sem modificar o Supabase, e verificam cadastro de contrato, alteração de status, histórico, duplicidade, validação e omissão de senha na resposta.

## Limites atuais

A aplicação foi preparada para uso local: ainda não há login nem autorização nos endpoints. O cadastro de responsáveis armazena hashes de senha, mas não constitui autenticação. Antes de disponibilizar publicamente, implemente autenticação e autorização. O acesso atual ocorre pelo Flask com a conexão PostgreSQL; não usa a Data API pública do Supabase.

Não há modelo de inteligência artificial implementado no código recebido. A interface não apresenta análises de risco simuladas. Cláusulas e aditivos são registros associados; criar um aditivo não altera automaticamente o valor ou a vigência do contrato principal.
