import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")


def requisicao(metodo, rota, dados=None):
    try:
        resposta = requests.request(
            metodo,
            f"{API_URL}{rota}",
            json=dados,
            timeout=15
        )

        print(f"\nStatus: {resposta.status_code}")

        try:
            print(
                json.dumps(
                    resposta.json(),
                    indent=4,
                    ensure_ascii=False
                )
            )
        except ValueError:
            print(resposta.text)

    except requests.exceptions.RequestException as erro:
        print(f"\nErro na requisição: {erro}")


def crud(recurso, opcao):
    rota = f"/{recurso}"

    # LISTAR
    if opcao == "1":
        requisicao("GET", rota)
        return

    # CADASTRAR
    if opcao == "3":
        texto = input("Digite o JSON: ")

        try:
            dados = json.loads(texto)
        except json.JSONDecodeError:
            print("JSON inválido.")
            return

        requisicao("POST", rota, dados)
        return

    # As operações abaixo precisam de ID
    id_registro = input("Digite o ID: ").strip()

    if not id_registro.isdigit():
        print("ID inválido.")
        return

    rota = f"{rota}/{id_registro}"

    # BUSCAR
    if opcao == "2":
        requisicao("GET", rota)

    # ATUALIZAR
    elif opcao == "4":
        texto = input("Digite o JSON com os campos para alterar: ")

        try:
            dados = json.loads(texto)
        except json.JSONDecodeError:
            print("JSON inválido.")
            return

        requisicao("PUT", rota, dados)

    # EXCLUIR
    elif opcao == "5":
        confirmacao = input("Tem certeza? (s/n): ").lower()

        if confirmacao == "s":
            requisicao("DELETE", rota)


def menu_recurso(nome, recurso):
    while True:
        print(f"\n=== {nome.upper()} ===")
        print("1 - Listar")
        print("2 - Buscar por ID")
        print("3 - Cadastrar")
        print("4 - Atualizar")
        print("5 - Excluir")
        print("0 - Voltar")

        opcao = input("Escolha: ").strip()

        if opcao == "0":
            break

        if opcao in ["1", "2", "3", "4", "5"]:
            crud(recurso, opcao)
        else:
            print("Opção inválida.")


def menu_principal():
    recursos = {
        "1": ("Clientes", "clientes"),
        "2": ("Usuários", "usuarios"),
        "3": ("Contratos", "contratos"),
        "4": ("Cláusulas", "clausulas"),
        "5": ("Aditivos", "aditivos"),
        "6": ("Histórico de Status", "historico-status"),
    }

    while True:
        print("\n=== GESTOR DE CONTRATOS ===")
        print(f"API: {API_URL}\n")

        for chave, (nome, _) in recursos.items():
            print(f"{chave} - {nome}")

        print("0 - Sair")

        opcao = input("Escolha: ").strip()

        if opcao == "0":
            print("Programa encerrado.")
            break

        if opcao in recursos:
            nome, recurso = recursos[opcao]
            menu_recurso(nome, recurso)
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu_principal()