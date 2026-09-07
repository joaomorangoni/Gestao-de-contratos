from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..extensions import db
from ..models import User


users_bp = Blueprint("users", __name__)


def current_user():
    return db.session.get(User, int(get_jwt_identity()))


def date_or_none(value):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


@users_bp.get("")
@jwt_required()
def list_users():
    user = current_user()
    if user.role != "admin":
        return jsonify({"error": "Acesso permitido apenas para administradores"}), 403
    return jsonify([u.to_dict() for u in User.query.order_by(User.id.desc()).all()])


@users_bp.get("/<int:user_id>")
@jwt_required()
def get_user(user_id):
    user = current_user()
    if user.role != "admin" and user.id != user_id:
        return jsonify({"error": "Sem permissão"}), 403
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify(target.to_dict())


@users_bp.put("/<int:user_id>")
@jwt_required()
def update_user(user_id):
    user = current_user()
    if user.role != "admin" and user.id != user_id:
        return jsonify({"error": "Sem permissão"}), 403

    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "Usuário não encontrado"}), 404

    data = request.get_json(silent=True) or {}
    for field in ["name", "phone", "cpf"]:
        if field in data:
            setattr(target, field, data[field])
    if "email" in data:
        target.email = data["email"].strip().lower()
    if "birth_date" in data:
        try:
            target.birth_date = date_or_none(data["birth_date"])
        except ValueError:
            return jsonify({"error": "birth_date deve estar no formato YYYY-MM-DD"}), 400
    if "is_active" in data and user.role == "admin":
        target.is_active = bool(data["is_active"])
    if "role" in data and user.role == "admin":
        target.role = data["role"]
    if "password" in data:
        if len(data["password"]) < 8:
            return jsonify({"error": "A senha deve ter pelo menos 8 caracteres"}), 400
        target.set_password(data["password"])

    db.session.commit()
    return jsonify({"message": "Usuário atualizado", "user": target.to_dict()})


@users_bp.delete("/<int:user_id>")
@jwt_required()
def delete_user(user_id):
    user = current_user()
    if user.role != "admin" and user.id != user_id:
        return jsonify({"error": "Sem permissão"}), 403
    target = db.session.get(User, user_id)
    if not target:
        return jsonify({"error": "Usuário não encontrado"}), 404
    db.session.delete(target)
    db.session.commit()
    return jsonify({"message": "Usuário excluído com sucesso"})
