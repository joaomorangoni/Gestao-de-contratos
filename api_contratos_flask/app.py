import os
from datetime import datetime
from decimal import Decimal

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

load_dotenv()  

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# MODELOS
# ============================================================

class Cliente(db.Model):
    __tablename__ = "cliente"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    tipo = db.Column(db.String)
    documento = db.Column(db.String, unique=True)
    email = db.Column(db.String)
    telefone = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contratos = db.relationship("Contrato", back_populates="cliente")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "documento": self.documento,
            "email": self.email,
            "telefone": self.telefone,
            "created_at": iso(self.created_at),
        }


class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    senha_hash = db.Column(db.String, nullable=False)
    papel = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contratos = db.relationship("Contrato", back_populates="usuario")
    alteracoes_status = db.relationship("HistoricoStatus", back_populates="usuario")

    def to_dict(self):
        # O hash da senha não é exposto pela API.
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "papel": self.papel,
            "created_at": iso(self.created_at),
        }


class Contrato(db.Model):
    __tablename__ = "contrato"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String, nullable=False, unique=True)
    titulo = db.Column(db.String, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    tipo_contrato = db.Column(db.String)
    valor_total = db.Column(db.Numeric(12, 2))
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date)
    status = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    cliente = db.relationship("Cliente", back_populates="contratos")
    usuario = db.relationship("Usuario", back_populates="contratos")
    clausulas = db.relationship("Clausula", back_populates="contrato")
    aditivos = db.relationship("Aditivo", back_populates="contrato")
    historicos = db.relationship("HistoricoStatus", back_populates="contrato")

    def to_dict(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "titulo": self.titulo,
            "cliente_id": self.cliente_id,
            "usuario_id": self.usuario_id,
            "tipo_contrato": self.tipo_contrato,
            "valor_total": numero_decimal(self.valor_total),
            "data_inicio": iso(self.data_inicio),
            "data_fim": iso(self.data_fim),
            "status": self.status,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }


class Clausula(db.Model):
    __tablename__ = "clausula"

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(
        db.Integer,
        db.ForeignKey("contrato.id"),
        nullable=False,
    )
    titulo = db.Column(db.String)
    descricao = db.Column(db.Text)
    ordem = db.Column(db.Integer)

    contrato = db.relationship("Contrato", back_populates="clausulas")

    def to_dict(self):
        return {
            "id": self.id,
            "contrato_id": self.contrato_id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "ordem": self.ordem,
        }


class Aditivo(db.Model):
    __tablename__ = "aditivo"

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(
        db.Integer,
        db.ForeignKey("contrato.id"),
        nullable=False,
    )
    descricao = db.Column(db.Text, nullable=False)
    novo_valor = db.Column(db.Numeric(12, 2))
    nova_data_fim = db.Column(db.Date)
    data_assinatura = db.Column(db.Date, nullable=False)

    contrato = db.relationship("Contrato", back_populates="aditivos")

    def to_dict(self):
        return {
            "id": self.id,
            "contrato_id": self.contrato_id,
            "descricao": self.descricao,
            "novo_valor": numero_decimal(self.novo_valor),
            "nova_data_fim": iso(self.nova_data_fim),
            "data_assinatura": iso(self.data_assinatura),
        }


class HistoricoStatus(db.Model):
    __tablename__ = "historico_status"

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(
        db.Integer,
        db.ForeignKey("contrato.id"),
        nullable=False,
    )
    status_anterior = db.Column(db.String)
    status_novo = db.Column(db.String)
    alterado_em = db.Column(db.DateTime, default=datetime.utcnow)
    alterado_por = db.Column(db.Integer, db.ForeignKey("usuario.id"))

    contrato = db.relationship("Contrato", back_populates="historicos")
    usuario = db.relationship("Usuario", back_populates="alteracoes_status")

    def to_dict(self):
        return {
            "id": self.id,
            "contrato_id": self.contrato_id,
            "status_anterior": self.status_anterior,
            "status_novo": self.status_novo,
            "alterado_em": iso(self.alterado_em),
            "alterado_por": self.alterado_por,
        }


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def iso(valor):
    return valor.isoformat() if valor is not None else None


def numero_decimal(valor):
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def parse_date(valor):
    if valor in (None, ""):
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


def parse_datetime(valor):
    if valor in (None, ""):
        return None

    # Aceita: 2026-09-07T18:30:00 ou 2026-09-07 18:30:00
    valor = valor.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")


def erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def obter_json():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return None
    return dados


def salvar():
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        return erro(
            "Não foi possível salvar. Verifique campos únicos e chaves estrangeiras.",
            409,
        )
    return None


# ============================================================
# ROTA INICIAL
# ============================================================

@app.get("/")
def inicio():
    return jsonify({
        "mensagem": "API de contratos funcionando",
        "recursos": [
            "/clientes",
            "/usuarios",
            "/contratos",
            "/clausulas",
            "/aditivos",
            "/historico-status",
        ]
    })


# ============================================================
# CLIENTE - GET / POST / PUT / DELETE
# ============================================================

@app.get("/clientes")
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.id).all()
    return jsonify([cliente.to_dict() for cliente in clientes])


@app.get("/clientes/<int:id>")
def buscar_cliente(id):
    cliente = db.session.get(Cliente, id)
    if not cliente:
        return erro("Cliente não encontrado.", 404)
    return jsonify(cliente.to_dict())


@app.post("/clientes")
def criar_cliente():
    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    if not dados.get("nome"):
        return erro("O campo 'nome' é obrigatório.")

    cliente = Cliente(
        nome=dados["nome"],
        tipo=dados.get("tipo"),
        documento=dados.get("documento"),
        email=dados.get("email"),
        telefone=dados.get("telefone"),
    )

    db.session.add(cliente)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(cliente.to_dict()), 201


@app.put("/clientes/<int:id>")
def atualizar_cliente(id):
    cliente = db.session.get(Cliente, id)
    if not cliente:
        return erro("Cliente não encontrado.", 404)

    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    for campo in ["nome", "tipo", "documento", "email", "telefone"]:
        if campo in dados:
            setattr(cliente, campo, dados[campo])

    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(cliente.to_dict())


@app.delete("/clientes/<int:id>")
def deletar_cliente(id):
    cliente = db.session.get(Cliente, id)
    if not cliente:
        return erro("Cliente não encontrado.", 404)

    db.session.delete(cliente)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify({"mensagem": "Cliente removido com sucesso."})


# ============================================================
# USUÁRIO - GET / POST / PUT / DELETE
# ============================================================

@app.get("/usuarios")
def listar_usuarios():
    usuarios = Usuario.query.order_by(Usuario.id).all()
    return jsonify([usuario.to_dict() for usuario in usuarios])


@app.get("/usuarios/<int:id>")
def buscar_usuario(id):
    usuario = db.session.get(Usuario, id)
    if not usuario:
        return erro("Usuário não encontrado.", 404)
    return jsonify(usuario.to_dict())


@app.post("/usuarios")
def criar_usuario():
    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    obrigatorios = ["nome", "email", "senha"]
    faltando = [campo for campo in obrigatorios if not dados.get(campo)]
    if faltando:
        return erro(f"Campos obrigatórios: {', '.join(faltando)}.")

    usuario = Usuario(
        nome=dados["nome"],
        email=dados["email"],
        senha_hash=generate_password_hash(dados["senha"]),
        papel=dados.get("papel"),
    )

    db.session.add(usuario)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(usuario.to_dict()), 201


@app.put("/usuarios/<int:id>")
def atualizar_usuario(id):
    usuario = db.session.get(Usuario, id)
    if not usuario:
        return erro("Usuário não encontrado.", 404)

    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    for campo in ["nome", "email", "papel"]:
        if campo in dados:
            setattr(usuario, campo, dados[campo])

    if "senha" in dados and dados["senha"]:
        usuario.senha_hash = generate_password_hash(dados["senha"])

    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(usuario.to_dict())


@app.delete("/usuarios/<int:id>")
def deletar_usuario(id):
    usuario = db.session.get(Usuario, id)
    if not usuario:
        return erro("Usuário não encontrado.", 404)

    db.session.delete(usuario)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify({"mensagem": "Usuário removido com sucesso."})


# ============================================================
# CONTRATO - GET / POST / PUT / DELETE
# ============================================================

@app.get("/contratos")
def listar_contratos():
    contratos = Contrato.query.order_by(Contrato.id).all()
    return jsonify([contrato.to_dict() for contrato in contratos])


@app.get("/contratos/<int:id>")
def buscar_contrato(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        return erro("Contrato não encontrado.", 404)
    return jsonify(contrato.to_dict())


@app.post("/contratos")
def criar_contrato():
    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    obrigatorios = ["numero", "titulo", "cliente_id", "data_inicio"]
    faltando = [campo for campo in obrigatorios if dados.get(campo) in (None, "")]
    if faltando:
        return erro(f"Campos obrigatórios: {', '.join(faltando)}.")

    try:
        contrato = Contrato(
            numero=dados["numero"],
            titulo=dados["titulo"],
            cliente_id=dados["cliente_id"],
            usuario_id=dados.get("usuario_id"),
            tipo_contrato=dados.get("tipo_contrato"),
            valor_total=dados.get("valor_total"),
            data_inicio=parse_date(dados["data_inicio"]),
            data_fim=parse_date(dados.get("data_fim")),
            status=dados.get("status"),
        )
    except (ValueError, TypeError):
        return erro("Datas devem usar o formato YYYY-MM-DD.")

    db.session.add(contrato)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(contrato.to_dict()), 201


@app.put("/contratos/<int:id>")
def atualizar_contrato(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        return erro("Contrato não encontrado.", 404)

    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    campos_simples = [
        "numero",
        "titulo",
        "cliente_id",
        "usuario_id",
        "tipo_contrato",
        "valor_total",
        "status",
    ]

    for campo in campos_simples:
        if campo in dados:
            setattr(contrato, campo, dados[campo])

    try:
        if "data_inicio" in dados:
            contrato.data_inicio = parse_date(dados["data_inicio"])
        if "data_fim" in dados:
            contrato.data_fim = parse_date(dados["data_fim"])
    except (ValueError, TypeError):
        return erro("Datas devem usar o formato YYYY-MM-DD.")

    contrato.updated_at = datetime.utcnow()

    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(contrato.to_dict())


@app.delete("/contratos/<int:id>")
def deletar_contrato(id):
    contrato = db.session.get(Contrato, id)
    if not contrato:
        return erro("Contrato não encontrado.", 404)

    db.session.delete(contrato)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify({"mensagem": "Contrato removido com sucesso."})


# ============================================================
# CLÁUSULA - GET / POST / PUT / DELETE
# ============================================================

@app.get("/clausulas")
def listar_clausulas():
    clausulas = Clausula.query.order_by(Clausula.id).all()
    return jsonify([clausula.to_dict() for clausula in clausulas])


@app.get("/clausulas/<int:id>")
def buscar_clausula(id):
    clausula = db.session.get(Clausula, id)
    if not clausula:
        return erro("Cláusula não encontrada.", 404)
    return jsonify(clausula.to_dict())


@app.post("/clausulas")
def criar_clausula():
    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    if dados.get("contrato_id") in (None, ""):
        return erro("O campo 'contrato_id' é obrigatório.")

    clausula = Clausula(
        contrato_id=dados["contrato_id"],
        titulo=dados.get("titulo"),
        descricao=dados.get("descricao"),
        ordem=dados.get("ordem"),
    )

    db.session.add(clausula)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(clausula.to_dict()), 201


@app.put("/clausulas/<int:id>")
def atualizar_clausula(id):
    clausula = db.session.get(Clausula, id)
    if not clausula:
        return erro("Cláusula não encontrada.", 404)

    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    for campo in ["contrato_id", "titulo", "descricao", "ordem"]:
        if campo in dados:
            setattr(clausula, campo, dados[campo])

    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(clausula.to_dict())


@app.delete("/clausulas/<int:id>")
def deletar_clausula(id):
    clausula = db.session.get(Clausula, id)
    if not clausula:
        return erro("Cláusula não encontrada.", 404)

    db.session.delete(clausula)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify({"mensagem": "Cláusula removida com sucesso."})


# ============================================================
# ADITIVO - GET / POST / PUT / DELETE
# ============================================================

@app.get("/aditivos")
def listar_aditivos():
    aditivos = Aditivo.query.order_by(Aditivo.id).all()
    return jsonify([aditivo.to_dict() for aditivo in aditivos])


@app.get("/aditivos/<int:id>")
def buscar_aditivo(id):
    aditivo = db.session.get(Aditivo, id)
    if not aditivo:
        return erro("Aditivo não encontrado.", 404)
    return jsonify(aditivo.to_dict())


@app.post("/aditivos")
def criar_aditivo():
    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    obrigatorios = ["contrato_id", "descricao", "data_assinatura"]
    faltando = [campo for campo in obrigatorios if dados.get(campo) in (None, "")]
    if faltando:
        return erro(f"Campos obrigatórios: {', '.join(faltando)}.")

    try:
        aditivo = Aditivo(
            contrato_id=dados["contrato_id"],
            descricao=dados["descricao"],
            novo_valor=dados.get("novo_valor"),
            nova_data_fim=parse_date(dados.get("nova_data_fim")),
            data_assinatura=parse_date(dados["data_assinatura"]),
        )
    except (ValueError, TypeError):
        return erro("Datas devem usar o formato YYYY-MM-DD.")

    db.session.add(aditivo)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(aditivo.to_dict()), 201


@app.put("/aditivos/<int:id>")
def atualizar_aditivo(id):
    aditivo = db.session.get(Aditivo, id)
    if not aditivo:
        return erro("Aditivo não encontrado.", 404)

    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    for campo in ["contrato_id", "descricao", "novo_valor"]:
        if campo in dados:
            setattr(aditivo, campo, dados[campo])

    try:
        if "nova_data_fim" in dados:
            aditivo.nova_data_fim = parse_date(dados["nova_data_fim"])
        if "data_assinatura" in dados:
            aditivo.data_assinatura = parse_date(dados["data_assinatura"])
    except (ValueError, TypeError):
        return erro("Datas devem usar o formato YYYY-MM-DD.")

    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(aditivo.to_dict())


@app.delete("/aditivos/<int:id>")
def deletar_aditivo(id):
    aditivo = db.session.get(Aditivo, id)
    if not aditivo:
        return erro("Aditivo não encontrado.", 404)

    db.session.delete(aditivo)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify({"mensagem": "Aditivo removido com sucesso."})


# ============================================================
# HISTÓRICO DE STATUS - GET / POST / PUT / DELETE
# ============================================================

@app.get("/historico-status")
def listar_historico_status():
    historicos = HistoricoStatus.query.order_by(HistoricoStatus.id).all()
    return jsonify([historico.to_dict() for historico in historicos])


@app.get("/historico-status/<int:id>")
def buscar_historico_status(id):
    historico = db.session.get(HistoricoStatus, id)
    if not historico:
        return erro("Histórico de status não encontrado.", 404)
    return jsonify(historico.to_dict())


@app.post("/historico-status")
def criar_historico_status():
    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    if dados.get("contrato_id") in (None, ""):
        return erro("O campo 'contrato_id' é obrigatório.")

    try:
        historico = HistoricoStatus(
            contrato_id=dados["contrato_id"],
            status_anterior=dados.get("status_anterior"),
            status_novo=dados.get("status_novo"),
            alterado_em=(
                parse_datetime(dados["alterado_em"])
                if dados.get("alterado_em")
                else datetime.utcnow()
            ),
            alterado_por=dados.get("alterado_por"),
        )
    except (ValueError, TypeError):
        return erro("Use uma data/hora ISO, por exemplo 2026-09-07T18:30:00.")

    db.session.add(historico)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(historico.to_dict()), 201


@app.put("/historico-status/<int:id>")
def atualizar_historico_status(id):
    historico = db.session.get(HistoricoStatus, id)
    if not historico:
        return erro("Histórico de status não encontrado.", 404)

    dados = obter_json()
    if dados is None:
        return erro("Envie um JSON válido.")

    for campo in [
        "contrato_id",
        "status_anterior",
        "status_novo",
        "alterado_por",
    ]:
        if campo in dados:
            setattr(historico, campo, dados[campo])

    try:
        if "alterado_em" in dados:
            historico.alterado_em = parse_datetime(dados["alterado_em"])
    except (ValueError, TypeError):
        return erro("Use uma data/hora ISO, por exemplo 2026-09-07T18:30:00.")

    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify(historico.to_dict())


@app.delete("/historico-status/<int:id>")
def deletar_historico_status(id):
    historico = db.session.get(HistoricoStatus, id)
    if not historico:
        return erro("Histórico de status não encontrado.", 404)

    db.session.delete(historico)
    resposta_erro = salvar()
    if resposta_erro:
        return resposta_erro

    return jsonify({"mensagem": "Histórico de status removido com sucesso."})


# ============================================================
# TRATAMENTO DE ERROS
# ============================================================

@app.errorhandler(404)
def rota_nao_encontrada(_):
    return erro("Rota não encontrada.", 404)


@app.errorhandler(500)
def erro_interno(_):
    db.session.rollback()
    return erro("Erro interno do servidor.", 500)


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    # Se o banco já possui as tabelas, db.create_all() apenas confere/cria
    # as que estiverem faltando. Para projetos com migrations, use Alembic.
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)
