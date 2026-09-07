from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_
from ..extensions import db
from ..models import User, UnreviewedContract


contracts_bp = Blueprint("contracts", __name__)


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def current_user():
    return db.session.get(User, int(get_jwt_identity()))


def allowed_to_access(contract, user):
    return user.role == "admin" or contract.user_id == user.id


@contracts_bp.get("")
@jwt_required()
def list_contracts():
    user = current_user()
    query = UnreviewedContract.query
    if user.role != "admin":
        query = query.filter_by(user_id=user.id)

    status = request.args.get("status")
    cpf = request.args.get("cpf")
    if status:
        query = query.filter_by(status=status)
    if cpf:
        query = query.filter(UnreviewedContract.cpf == cpf)

    return jsonify([c.to_dict() for c in query.order_by(UnreviewedContract.id.desc()).all()])


@contracts_bp.get("/<int:contract_id>")
@jwt_required()
def get_contract(contract_id):
    contract = db.session.get(UnreviewedContract, contract_id)
    user = current_user()
    if not contract:
        return jsonify({"error": "Contrato não encontrado"}), 404
    if not allowed_to_access(contract, user):
        return jsonify({"error": "Sem permissão"}), 403
    return jsonify(contract.to_dict())


@contracts_bp.post("")
@jwt_required()
def create_contract():
    user = current_user()
    data = request.get_json(silent=True) or {}
    required = ["full_name", "cpf", "birth_date"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": "Campos obrigatórios", "fields": missing}), 400

    try:
        birth_date = parse_date(data["birth_date"])
        start_date = parse_date(data.get("contract_start_date"))
        end_date = parse_date(data.get("contract_end_date"))
    except ValueError:
        return jsonify({"error": "Datas devem estar no formato YYYY-MM-DD"}), 400

    contract = UnreviewedContract(
        user_id=user.id,
        full_name=data["full_name"].strip(),
        cpf=data["cpf"],
        birth_date=birth_date,
        email=data.get("email"),
        phone=data.get("phone"),
        address=data.get("address"),
        job_title=data.get("job_title"),
        employer_name=data.get("employer_name"),
        salary=data.get("salary"),
        contract_start_date=start_date,
        contract_end_date=end_date,
        document_filename=data.get("document_filename"),
        document_path=data.get("document_path"),
        content_text=data.get("content_text"),
        status="pending",
    )
    db.session.add(contract)
    db.session.commit()
    return jsonify({"message": "Contrato enviado para análise", "contract": contract.to_dict()}), 201


@contracts_bp.put("/<int:contract_id>")
@jwt_required()
def update_contract(contract_id):
    contract = db.session.get(UnreviewedContract, contract_id)
    user = current_user()
    if not contract:
        return jsonify({"error": "Contrato não encontrado"}), 404
    if not allowed_to_access(contract, user):
        return jsonify({"error": "Sem permissão"}), 403
    if contract.status == "reviewed":
        return jsonify({"error": "Contrato já revisado; altere a versão revisada"}), 409

    data = request.get_json(silent=True) or {}
    simple_fields = [
        "full_name", "cpf", "email", "phone", "address", "job_title",
        "employer_name", "salary", "document_filename", "document_path", "content_text", "status", "ai_error"
    ]
    for field in simple_fields:
        if field in data:
            setattr(contract, field, data[field])

    for field in ["birth_date", "contract_start_date", "contract_end_date"]:
        if field in data:
            try:
                setattr(contract, field, parse_date(data[field]))
            except ValueError:
                return jsonify({"error": f"{field} deve estar no formato YYYY-MM-DD"}), 400

    db.session.commit()
    return jsonify({"message": "Contrato atualizado", "contract": contract.to_dict()})


@contracts_bp.delete("/<int:contract_id>")
@jwt_required()
def delete_contract(contract_id):
    contract = db.session.get(UnreviewedContract, contract_id)
    user = current_user()
    if not contract:
        return jsonify({"error": "Contrato não encontrado"}), 404
    if not allowed_to_access(contract, user):
        return jsonify({"error": "Sem permissão"}), 403
    db.session.delete(contract)
    db.session.commit()
    return jsonify({"message": "Contrato excluído com sucesso"})
