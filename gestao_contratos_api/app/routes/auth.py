from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import or_
from ..extensions import db
from ..models import User


auth_bp = Blueprint("auth", __name__)


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    required = ["name", "email", "password"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": "Campos obrigatórios", "fields": missing}), 400

    email = data["email"].strip().lower()
    existing = User.query.filter(or_(User.email == email, User.cpf == data.get("cpf"))).first() if data.get("cpf") else User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "E-mail ou CPF já cadastrado"}), 409

    if len(data["password"]) < 8:
        return jsonify({"error": "A senha deve ter pelo menos 8 caracteres"}), 400

    user = User(
        name=data["name"].strip(),
        email=email,
        cpf=data.get("cpf"),
        phone=data.get("phone"),
        birth_date=parse_date(data.get("birth_date")) if data.get("birth_date") else None,
        role=data.get("role", "worker"),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Usuário criado com sucesso", "user": user.to_dict(), "access_token": access_token}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active or not user.check_password(password):
        return jsonify({"error": "E-mail ou senha inválidos"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Login realizado", "access_token": token, "user": user.to_dict()}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify(user.to_dict())
