import requests

API = "http://127.0.0.1:5000/api"
token = None


def headers():
    return {"Authorization": f"Bearer {token}"}


def login():
    global token

    email = input("E-mail: ")
    senha = input("Senha: ")

    r = requests.post(
        f"{API}/auth/login",
        json={
            "email": email,
            "password": senha
        }
    )

    if r.status_code == 200:
        token = r.json()["access_token"]
        print("Login realizado com sucesso!")
    else:
        print("Erro:", r.json())


def cadastrar_usuario():
    global token

    nome = input("Nome: ")
    email = input("E-mail: ")
    senha = input("Senha: ")

    r = requests.post(
        f"{API}/auth/register",
        json={
            "name": nome,
            "email": email,
            "password": senha
        }
    )

    print(r.json())

    if r.status_code == 201:
        token = r.json()["access_token"]


def listar_contratos():
    r = requests.get(
        f"{API}/contracts",
        headers=headers()
    )

    if r.status_code == 200:
        contratos = r.json()

        if not contratos:
            print("Nenhum contrato cadastrado.")
            return

        for c in contratos:
            print("\n--------------------")
            print("ID:", c["id"])
            print("Nome:", c["full_name"])
            print("CPF:", c["cpf"])
            print("Status:", c["status"])

    else:
        print("Erro:", r.json())


def criar_contrato():
    nome = input("Nome completo: ")
    cpf = input("CPF: ")
    nascimento = input("Nascimento (YYYY-MM-DD): ")

    r = requests.post(
        f"{API}/contracts",
        headers=headers(),
        json={
            "full_name": nome,
            "cpf": cpf,
            "birth_date": nascimento
        }
    )

    print(r.json())


def atualizar_contrato():
    contrato_id = input("ID do contrato: ")
    novo_nome = input("Novo nome: ")

    r = requests.put(
        f"{API}/contracts/{contrato_id}",
        headers=headers(),
        json={
            "full_name": novo_nome
        }
    )

    print(r.json())


def excluir_contrato():
    contrato_id = input("ID do contrato: ")

    r = requests.delete(
        f"{API}/contracts/{contrato_id}",
        headers=headers()
    )

    print(r.json())


while True:

    print("""
==============================
     GESTÃO DE CONTRATOS
==============================

1 - Cadastrar usuário
2 - Login
3 - Listar contratos
4 - Cadastrar contrato
5 - Atualizar contrato
6 - Excluir contrato
0 - Sair
""")

    opcao = input("Escolha: ")

    if opcao == "1":
        cadastrar_usuario()

    elif opcao == "2":
        login()

    elif opcao == "3":
        listar_contratos()

    elif opcao == "4":
        criar_contrato()

    elif opcao == "5":
        atualizar_contrato()

    elif opcao == "6":
        excluir_contrato()

    elif opcao == "0":
        break

    else:
        print("Opção inválida.")