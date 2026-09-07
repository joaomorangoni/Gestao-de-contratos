from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..extensions import db
from ..models import User, UnreviewedContract, ReviewedContract


reviewed_bp = Blueprint("reviewed", __name__)


def current_user():
    return db.session.get(User, int(get_jwt_identity()))


def allowed(review, user):
    return user.role == "admin" or review.user_id == user.id


@reviewed_bp.get("")
@jwt_required()
def list_reviewed():
    user = current_user()
    query = ReviewedContract.query
    if user.role != "admin":
        query = query.filter_by(user_id=user.id)
    classification = request.args.get("classification")
    if classification:
        query = query.filter_by(classification=classification)
    return jsonify([item.to_dict() for item in query.order_by(ReviewedContract.id.desc()).all()])


@reviewed_bp.get("/<int:review_id>")
@jwt_required()
def get_reviewed(review_id):
    item = db.session.get(ReviewedContract, review_id)
    user = current_user()
    if not item:
        return jsonify({"error": "Revisão não encontrada"}), 404
    if not allowed(item, user):
        return jsonify({"error": "Sem permissão"}), 403
    return jsonify(item.to_dict())


@reviewed_bp.post("")
@jwt_required()
def create_reviewed():
    user = current_user()
    data = request.get_json(silent=True) or {}
    source_id = data.get("source_contract_id")
    if not source_id or data.get("score") is None:
        return jsonify({"error": "source_contract_id e score são obrigatórios"}), 400

    source = db.session.get(UnreviewedContract, source_id)
    if not source:
        return jsonify({"error": "Contrato de origem não encontrado"}), 404
    if user.role != "admin" and source.user_id != user.id:
        return jsonify({"error": "Sem permissão"}), 403
    if source.reviewed:
        return jsonify({"error": "Esse contrato já possui revisão"}), 409

    try:
        score = float(data["score"])
    except (TypeError, ValueError):
        return jsonify({"error": "score deve ser numérico"}), 400
    if not 0 <= score <= 100:
        return jsonify({"error": "score deve ficar entre 0 e 100"}), 400

    review = ReviewedContract(
        source_contract_id=source.id,
        user_id=source.user_id,
        score=score,
        classification=data.get("classification", "analisado"),
        ai_summary=data.get("ai_summary"),
        ai_findings=data.get("ai_findings", []),
        reviewed_by=data.get("reviewed_by", "ai"),
    )
    source.status = "reviewed"
    source.ai_error = None
    db.session.add(review)
    db.session.commit()
    return jsonify({"message": "Revisão registrada", "reviewed_contract": review.to_dict()}), 201


@reviewed_bp.put("/<int:review_id>")
@jwt_required()
def update_reviewed(review_id):
    item = db.session.get(ReviewedContract, review_id)
    user = current_user()
    if not item:
        return jsonify({"error": "Revisão não encontrada"}), 404
    if not allowed(item, user):
        return jsonify({"error": "Sem permissão"}), 403

    data = request.get_json(silent=True) or {}
    if "score" in data:
        try:
            item.score = float(data["score"])
        except (TypeError, ValueError):
            return jsonify({"error": "score deve ser numérico"}), 400
        if not 0 <= item.score <= 100:
            return jsonify({"error": "score deve ficar entre 0 e 100"}), 400
    for field in ["classification", "ai_summary", "ai_findings", "reviewed_by"]:
        if field in data:
            setattr(item, field, data[field])

    db.session.commit()
    return jsonify({"message": "Revisão atualizada", "reviewed_contract": item.to_dict()})


@reviewed_bp.delete("/<int:review_id>")
@jwt_required()
def delete_reviewed(review_id):
    item = db.session.get(ReviewedContract, review_id)
    user = current_user()
    if not item:
        return jsonify({"error": "Revisão não encontrada"}), 404
    if not allowed(item, user):
        return jsonify({"error": "Sem permissão"}), 403
    source = item.source_contract
    db.session.delete(item)
    if source:
        source.status = "pending"
    db.session.commit()
    return jsonify({"message": "Revisão excluída e contrato voltou para pendente"})
