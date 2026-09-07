# API de Gestão de Contratos

API REST em Flask para cadastro de usuários, entrada de contratos e armazenamento do resultado da análise de IA.

## Arquitetura

- `users`: contas e autenticação do sistema.
- `contracts_unreviewed`: contratos recebidos e ainda não revisados.
- `contracts_reviewed`: resultado da análise, com score de 0 a 100.
- `source_contract_id`: liga a revisão ao contrato original.

A senha nunca é salva em texto puro: o projeto usa hash via Werkzeug.

## 1. Instalação

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e ajuste a chave JWT.

## 2. Rodar

```bash
python run.py
```

API: `http://localhost:5000`

## Autenticação

### POST `/api/auth/register`

```json
{
  "name": "João Silva",
  "email": "joao@email.com",
  "password": "SenhaSegura123",
  "cpf": "12345678900",
  "phone": "11999999999",
  "birth_date": "1999-05-20"
}
```

### POST `/api/auth/login`

```json
{
  "email": "joao@email.com",
  "password": "SenhaSegura123"
}
```

O login retorna `access_token`. Nas demais rotas, envie:

```text
Authorization: Bearer SEU_TOKEN
```

## Usuários

- `GET /api/users` — lista todos (admin).
- `GET /api/users/<id>` — consulta usuário.
- `PUT /api/users/<id>` — atualiza usuário.
- `DELETE /api/users/<id>` — remove usuário.
- `GET /api/auth/me` — usuário autenticado.

## Contratos não revisados

- `GET /api/contracts`
- `GET /api/contracts/<id>`
- `POST /api/contracts`
- `PUT /api/contracts/<id>`
- `DELETE /api/contracts/<id>`

### POST exemplo

```json
{
  "full_name": "João Silva",
  "cpf": "12345678900",
  "birth_date": "1999-05-20",
  "email": "joao@email.com",
  "phone": "11999999999",
  "address": "Rua Exemplo, 100",
  "job_title": "Desenvolvedor",
  "employer_name": "Empresa XPTO",
  "salary": 4500.00,
  "contract_start_date": "2026-09-01",
  "contract_end_date": "2027-09-01",
  "document_filename": "contrato_joao.pdf",
  "document_path": "uploads/contrato_joao.pdf",
  "content_text": "Texto extraído do contrato..."
}
```

## Contratos revisados

- `GET /api/reviewed-contracts`
- `GET /api/reviewed-contracts/<id>`
- `POST /api/reviewed-contracts`
- `PUT /api/reviewed-contracts/<id>`
- `DELETE /api/reviewed-contracts/<id>`

### POST da análise de IA

```json
{
  "source_contract_id": 1,
  "score": 87.5,
  "classification": "aprovado",
  "ai_summary": "Contrato apresenta os campos principais e não foram detectadas inconsistências relevantes.",
  "ai_findings": [
    {"campo": "salario", "status": "ok"},
    {"campo": "data_fim", "status": "ok"}
  ],
  "reviewed_by": "modelo-ia-v1"
}
```

Quando essa rota é usada, o contrato original passa de `pending` para `reviewed`.

## Integração com o modelo de IA

A arquitetura já separa o contrato recebido da revisão. O fluxo recomendado é:

1. Frontend envia o contrato para `POST /api/contracts`.
2. Backend salva com `status = pending`.
3. Um serviço de IA recebe o `content_text` (ou o documento já extraído) e produz score, classificação, resumo e achados.
4. O resultado é enviado para `POST /api/reviewed-contracts`.
5. O sistema muda o status do contrato original para `reviewed`.

Para produção, é recomendável colocar a análise de IA em fila (Celery/RQ + Redis, por exemplo) em vez de bloquear a requisição HTTP.

## Segurança e LGPD

Este projeto contém CPF, data de nascimento e outros dados pessoais. Para produção, implemente HTTPS, controle de acesso mais granular, logs de auditoria, política de retenção, backups protegidos e criptografia adequada para dados pessoais sensíveis. Nunca registre senhas ou tokens nos logs.
