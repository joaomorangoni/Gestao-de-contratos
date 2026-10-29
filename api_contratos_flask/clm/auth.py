from functools import wraps
from flask import current_app, g, request, abort
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from extensions import db
from .models import User


def serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='clm-auth-v1')


def authenticate():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        abort(401, description='Entre para continuar.')
    try:
        payload = serializer().loads(header[7:], max_age=28800)
        user = db.session.get(User, payload['id'])
    except (BadSignature, SignatureExpired, KeyError, TypeError):
        abort(401, description='Sessão inválida ou expirada.')
    if not user:
        abort(401, description='Usuário não encontrado.')
    g.user = user
    return user


def require_user(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = authenticate()
            if roles and user.role not in roles:
                abort(403, description='Seu papel não permite esta operação.')
            return fn(*args, **kwargs)
        return wrapped
    return decorator
