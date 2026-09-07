import os

from flask import Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv

from .extensions import db, jwt
from .routes.auth import auth_bp
from .routes.users import users_bp
from .routes.contracts import contracts_bp
from .routes.reviewed_contracts import reviewed_bp

load_dotenv()


def create_app():

    app = Flask(__name__)

    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///contratos.db"
    )

    # Alguns provedores usam postgres://;
    # SQLAlchemy 2 espera postgresql://.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY",
        "troque-esta-chave-em-producao"
    )

    app.config["JSON_SORT_KEYS"] = False

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    app.register_blueprint(
        users_bp,
        url_prefix="/api/users"
    )

    app.register_blueprint(
        contracts_bp,
        url_prefix="/api/contracts"
    )

    app.register_blueprint(
        reviewed_bp,
        url_prefix="/api/reviewed-contracts"
    )

    # Swagger
    swagger_bp = get_swaggerui_blueprint(
        "/swagger",
        "/static/swagger.json",
        config={
            "app_name": "API de Gestão de Contratos"
        }
    )

    app.register_blueprint(
        swagger_bp,
        url_prefix="/swagger"
    )

    @app.get("/")
    def health():
        return jsonify({
            "message": "API de Gestão de Contratos online",
            "status": "ok",
            "endpoints": [
                "/api/auth",
                "/api/users",
                "/api/contracts",
                "/api/reviewed-contracts",
                "/swagger/"
            ],
        })

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({
            "error": "Rota não encontrada"
        }), 404

    with app.app_context():
        db.create_all()

    return app