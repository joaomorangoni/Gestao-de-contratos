# Gestor de Contratos — API Flask

## Nome do projeto

**Gestor de Contratos**

## Descrição

O projeto consiste em uma API REST desenvolvida em Python com Flask para realizar o gerenciamento de contratos e das informações relacionadas a eles.

A API permite cadastrar, consultar, atualizar e remover dados de clientes, usuários, contratos, cláusulas, aditivos e histórico de status, utilizando os métodos HTTP `GET`, `POST`, `PUT` e `DELETE`.

A aplicação foi estruturada para ficar disponível em ambiente de nuvem na **AWS**. Um sistema externo, cujo backend já está implementado, será responsável por consumir a API e realizar as requisições necessárias.

O banco de dados utilizado é o **PostgreSQL**, hospedado no **Amazon RDS**, e o acesso aos dados é realizado por meio do SQLAlchemy.

---

## Problema escolhido

O gerenciamento de contratos envolve diferentes tipos de informações, como:

- clientes;
- usuários responsáveis;
- dados dos contratos;
- cláusulas;
- aditivos;
- valores;
- datas;
- alterações de status.

Quando essas informações são armazenadas ou controladas de maneira descentralizada, torna-se mais difícil manter os dados organizados, atualizados e disponíveis para consulta por outros sistemas.

Além disso, um sistema de gestão precisa de uma forma padronizada para acessar e modificar essas informações sem depender diretamente do banco de dados.

---

## Solução proposta

A solução proposta é a criação de uma **API REST** responsável por centralizar o acesso aos dados do sistema de gestão de contratos.

A API disponibiliza operações de CRUD para as principais entidades do projeto e funciona como intermediária entre o sistema consumidor e o banco de dados.

O fluxo principal da solução é:

```text
Sistema de Gestão
        |
        | Requisições HTTP
        | GET / POST / PUT / DELETE
        v
API REST Flask
        |
        | SQLAlchemy
        v
PostgreSQL
(Amazon RDS)
```

Dessa forma, o sistema não precisa acessar o banco de dados diretamente. Ele realiza as requisições para a API, e a API é responsável por validar, processar e armazenar os dados.

---

## Integrantes

| Nome | RM |
| --- | --- |
| Davi Oliveira da Silva | RM569108 |
| João Pedro Morangoni | RM570073 |
| João Vitor Xavier de Carvalho | RM570633 |

---

## Tecnologias utilizadas

- **Python** — linguagem principal utilizada no desenvolvimento;
- **Flask** — framework utilizado para criação da API REST;
- **Flask-SQLAlchemy** — integração do Flask com o SQLAlchemy;
- **SQLAlchemy** — ORM utilizado para comunicação com o banco de dados;
- **PostgreSQL** — banco de dados relacional;
- **Amazon RDS** — serviço utilizado para hospedar o banco PostgreSQL na AWS;
- **AWS Lambda** — ambiente de nuvem utilizado para disponibilizar a API;
- **psycopg2** — driver utilizado para conexão com PostgreSQL;
- **python-dotenv** — carregamento das variáveis de ambiente;
- **Werkzeug** — utilizado em funcionalidades do Flask, incluindo geração segura de hash de senha;
- **Swagger / OpenAPI** — documentação e testes dos endpoints da API;
- **Git** — controle de versão;
- **GitHub** — hospedagem do repositório do projeto.

---

## Arquitetura inicial

A arquitetura inicial do projeto é composta por três partes principais:

```text
┌─────────────────────────────────────┐
│ Sistema de Gestão de Contratos      │
│ Backend consumidor da API           │
└─────────────────┬───────────────────┘
                  │
                  │ HTTP / JSON
                  │ GET / POST
                  │ PUT / DELETE
                  ▼
┌─────────────────────────────────────┐
│ API REST                            │
│ Python + Flask                      │
│ Hospedada na AWS                    │
└─────────────────┬───────────────────┘
                  │
                  │ SQLAlchemy
                  ▼
┌─────────────────────────────────────┐
│ PostgreSQL                          │
│ Amazon RDS                          │
└─────────────────────────────────────┘
```

### Responsabilidades

**Sistema consumidor**

O sistema de gestão é responsável por utilizar os endpoints disponibilizados pela API. Nesta etapa do projeto, o backend responsável por realizar essas requisições já está implementado.

**API Flask**

A API recebe as requisições HTTP, processa os dados enviados, executa as operações necessárias e retorna respostas em JSON.

**SQLAlchemy**

Realiza o mapeamento entre os objetos da aplicação Python e as tabelas do PostgreSQL.

**PostgreSQL / Amazon RDS**

Responsável pela persistência dos dados do sistema.

---

# Banco de dados utilizado

O projeto utiliza **PostgreSQL**, hospedado no **Amazon RDS**.

As principais tabelas são:

- `cliente`;
- `usuario`;
- `contrato`;
- `clausula`;
- `aditivo`;
- `historico_status`.

### Relacionamentos principais

- um cliente pode possuir contratos;
- um usuário pode estar associado a contratos;
- um contrato pode possuir várias cláusulas;
- um contrato pode possuir vários aditivos;
- um contrato pode possuir vários registros no histórico de status;
- alterações de status podem registrar o usuário responsável pela alteração.

---

# Instalação

## 1. Clonar o repositório

```bash
git clone https://github.com/joaomorangoni/Gestao-de-contratos.git
cd api_contratos_flask
```

---

## 2. Criar o ambiente virtual

No Windows PowerShell:

```powershell
python -m venv venv
```

Ative o ambiente:

```powershell
.\venv\Scripts\Activate.ps1
```

Caso o PowerShell bloqueie a execução:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Quando o ambiente estiver ativo, o terminal deverá apresentar:

```text
(venv)
```

---

## 3. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

---

# Configuração das variáveis de ambiente

As credenciais e informações de conexão com o banco não ficam diretamente no código-fonte.

Crie um arquivo chamado:

```text
.env
```

na raiz do projeto.

Exemplo:

```env
DB_HOST=seu-endpoint-rds.amazonaws.com
DB_PORT=5432
DB_NAME=nome_do_banco
DB_USER=usuario_do_banco
DB_PASSWORD=senha_do_banco
```

A aplicação utiliza:

```python
import os
from dotenv import load_dotenv

load_dotenv()  # lê o .env e injeta em os.environ

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
```

## Segurança das credenciais

O arquivo `.env` não deve ser enviado ao GitHub porque contém dados sensíveis.

O `.gitignore` deve possuir:

```gitignore
.env
.env.*
!.env.example
```

O arquivo `.env.example` pode ser versionado para demonstrar quais variáveis são necessárias, mas sem conter credenciais reais.

---

# Instruções para execução

## Execução local

Com o ambiente virtual ativado:

```powershell
python app.py
```

Durante o desenvolvimento, a API pode ser acessada localmente em:

```text
http://127.0.0.1:5000
```

## Execução em produção

Na arquitetura do projeto, a API será disponibilizada pela **AWS**.

Após o deploy, o sistema consumidor deverá utilizar a URL pública disponibilizada para a API.

Exemplo:

```text
https://URL_PUBLICA_DA_API
```

O backend do sistema de gestão deverá realizar as requisições HTTP utilizando essa URL como endereço base.

Exemplo:

```text
GET https://URL_PUBLICA_DA_API/contratos
```

> Substituir `URL_PUBLICA_DA_API` pelo endereço real gerado no ambiente AWS antes da entrega final.

---

# Principais endpoints

Cada entidade possui endpoints para consulta, criação, alteração e exclusão.

## Clientes

| Método | Endpoint | Função |
| --- | --- | --- |
| GET | `/clientes` | Lista todos os clientes |
| GET | `/clientes/<id>` | Consulta um cliente |
| POST | `/clientes` | Cadastra um cliente |
| PUT | `/clientes/<id>` | Atualiza um cliente |
| DELETE | `/clientes/<id>` | Remove um cliente |

## Usuários

| Método | Endpoint | Função |
| --- | --- | --- |
| GET | `/usuarios` | Lista todos os usuários |
| GET | `/usuarios/<id>` | Consulta um usuário |
| POST | `/usuarios` | Cadastra um usuário |
| PUT | `/usuarios/<id>` | Atualiza um usuário |
| DELETE | `/usuarios/<id>` | Remove um usuário |

## Contratos

| Método | Endpoint | Função |
| --- | --- | --- |
| GET | `/contratos` | Lista todos os contratos |
| GET | `/contratos/<id>` | Consulta um contrato |
| POST | `/contratos` | Cadastra um contrato |
| PUT | `/contratos/<id>` | Atualiza um contrato |
| DELETE | `/contratos/<id>` | Remove um contrato |

## Cláusulas

| Método | Endpoint | Função |
| --- | --- | --- |
| GET | `/clausulas` | Lista todas as cláusulas |
| GET | `/clausulas/<id>` | Consulta uma cláusula |
| POST | `/clausulas` | Cadastra uma cláusula |
| PUT | `/clausulas/<id>` | Atualiza uma cláusula |
| DELETE | `/clausulas/<id>` | Remove uma cláusula |

## Aditivos

| Método | Endpoint | Função |
| --- | --- | --- |
| GET | `/aditivos` | Lista todos os aditivos |
| GET | `/aditivos/<id>` | Consulta um aditivo |
| POST | `/aditivos` | Cadastra um aditivo |
| PUT | `/aditivos/<id>` | Atualiza um aditivo |
| DELETE | `/aditivos/<id>` | Remove um aditivo |

## Histórico de status

| Método | Endpoint | Função |
| --- | --- | --- |
| GET | `/historico-status` | Lista o histórico de status |
| GET | `/historico-status/<id>` | Consulta um registro |
| POST | `/historico-status` | Cria um registro de histórico |
| PUT | `/historico-status/<id>` | Atualiza um registro |
| DELETE | `/historico-status/<id>` | Remove um registro |

---

# Exemplos de requisições

## Criar cliente

### `POST /clientes`

```json
{
  "nome": "Empresa ABC",
  "tipo": "PJ",
  "documento": "12345678000190",
  "email": "contato@empresa.com",
  "telefone": "11999999999"
}
```

---

## Criar usuário

### `POST /usuarios`

```json
{
  "nome": "João",
  "email": "joao@email.com",
  "senha": "123456",
  "papel": "ADMIN"
}
```

A API recebe a senha, gera um hash e armazena somente o valor protegido no campo `senha_hash`.

O hash não é retornado nos endpoints de consulta.

---

## Criar contrato

### `POST /contratos`

```json
{
  "numero": "CTR-001",
  "titulo": "Contrato de prestação de serviços",
  "cliente_id": 1,
  "usuario_id": 1,
  "tipo_contrato": "SERVICO",
  "valor_total": 15000.00,
  "data_inicio": "2026-09-07",
  "data_fim": "2027-09-07",
  "status": "ATIVO"
}
```

---

## Criar cláusula

### `POST /clausulas`

```json
{
  "contrato_id": 1,
  "titulo": "Prazo",
  "descricao": "O contrato terá validade de 12 meses.",
  "ordem": 1
}
```

---

## Criar aditivo

### `POST /aditivos`

```json
{
  "contrato_id": 1,
  "descricao": "Aumento do valor do contrato",
  "novo_valor": 17500.00,
  "nova_data_fim": "2028-01-01",
  "data_assinatura": "2026-10-01"
}
```

---

## Criar histórico de status

### `POST /historico-status`

```json
{
  "contrato_id": 1,
  "status_anterior": "PENDENTE",
  "status_novo": "ATIVO",
  "alterado_por": 1
}
```

---

# Comunicação com o sistema

A API foi criada para ser consumida pelo sistema de gestão de contratos.

Nesta etapa do trabalho, o **backend do sistema consumidor está pronto** e realiza as requisições necessárias para a API.

A comunicação ocorre por meio de requisições HTTP e respostas no formato JSON.

Exemplo de fluxo:

```text
Usuário
   |
   v
Sistema de Gestão
   |
   | solicita contratos
   v
GET /contratos
   |
   v
API Flask na AWS
   |
   v
Amazon RDS
   |
   v
Resposta JSON
   |
   v
Sistema de Gestão
```

Essa separação permite manter o backend consumidor independente da implementação interna do banco de dados.

---

# Documentação Swagger

A API possui documentação utilizando **Swagger/OpenAPI**.

Quando executada localmente, a documentação pode ser acessada em:

```text
http://127.0.0.1:5000/swagger/
```

Quando a API estiver publicada na AWS, a documentação deverá ser acessada utilizando a URL pública da aplicação:

```text
https://URL_PUBLICA_DA_API/swagger/
```

O Swagger permite visualizar e testar:

- endpoints disponíveis;
- métodos HTTP;
- parâmetros;
- corpo das requisições;
- exemplos de dados;
- códigos HTTP;
- respostas da API.

O arquivo de especificação Swagger utilizado pelo projeto pode estar localizado em:

```text
app/static/swagger.json
```

> Caso a estrutura final do projeto utilize outro caminho, atualizar esta informação no README.

---

# Link para documentação Swagger

### Desenvolvimento local

```text
http://127.0.0.1:5000/swagger/
```

### AWS

```text
https://URL_PUBLICA_DA_API/swagger/
```

> Atualizar com a URL pública real da API após o deploy.

---

# Estrutura básica do projeto

```text
api_contratos_flask/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env
└── .env.example
```

O arquivo `.env` permanece apenas no ambiente local ou no ambiente seguro de execução e não deve ser enviado ao repositório.

---

# Link do Trello ou Notion

Adicionar abaixo o link utilizado pelo grupo para organização do projeto:

```text
https://trello.com/invite/b/6a982f1afac57a4b37efe2db/ATTI93e793cb437404ce67b3bed5de1bf146603D5766/gestor-de-contratos
```
---
