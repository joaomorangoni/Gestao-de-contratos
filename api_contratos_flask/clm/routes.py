import hashlib
import io
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo

import click
from flask import Blueprint, abort, g, jsonify, request, send_file
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from extensions import db
from .auth import authenticate, require_user, serializer
from .models import User, ContractRequest, Approval, Attachment, Contract, ROLES, DEPARTMENTS, now

bp = Blueprint('clm', __name__, url_prefix='/api')
CONSENT = 'Li o documento e confirmo meu aceite eletrônico nesta demonstração.'


def body():
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        abort(400, description='Envie um objeto JSON válido.')
    return value


def string(data, field, maximum, required=True):
    value = data.get(field, '')
    if not isinstance(value, str) or len(value.strip()) > maximum or (required and not value.strip()):
        abort(400, description=f'Campo inválido: {field} (máximo {maximum} caracteres).')
    return value.strip()


def email(data, field):
    value = string(data, field, 254).lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
        abort(400, description=f'E-mail inválido: {field}.')
    return value


def commit():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, description='Registro duplicado ou vínculo inválido. Atualize a tela.')


def get_request(request_id, lock=False):
    stmt = select(ContractRequest).where(ContractRequest.id == request_id)
    if lock:
        stmt = stmt.with_for_update()
    item = db.session.execute(stmt).scalar_one_or_none()
    if not item:
        abort(404, description='Solicitação não encontrada.')
    user = g.user
    allowed = user.role in ('GESTOR', 'APROVADOR') or item.requester_id == user.id
    if user.role == 'FORNECEDOR':
        allowed = item.supplier_email == user.email and item.status in ('EM_ASSINATURA', 'ASSINADO')
    if not allowed:
        abort(403, description='Você não tem acesso a esta solicitação.')
    return item


def serialize(item):
    contract = item.contract
    external = g.user.role == 'FORNECEDOR'
    return dict(
        id=item.id, subject=item.subject, description=item.description,
        amount=str(item.amount), cost_center=item.cost_center,
        supplier_name=item.supplier_name, supplier_document=item.supplier_document,
        supplier_email=item.supplier_email, status=item.status,
        requester=item.requester.to_dict(), created_at=item.created_at.isoformat(),
        attachments=[] if external else [dict(id=a.id, name=a.name, sha256=a.sha256) for a in item.attachments],
        approvals=[dict(id=a.id, department=a.department, decision=a.decision,
                        comment=a.comment, approver=a.approver.name,
                        created_at=a.created_at.isoformat()) for a in item.approvals] if not external else [],
        contract=None if not contract else dict(
            id=contract.id, starts_at=contract.starts_at.isoformat(), ends_at=contract.ends_at.isoformat(),
            document_name=contract.document_name, document_sha256=contract.document_sha256,
            signed_at=contract.signed_at.isoformat() if contract.signed_at else None,
            signer_name=contract.signer_name, signer_email=contract.signer_email,
        ),
    )


def upload(file, final=False):
    if not file or not file.filename:
        abort(400, description='Selecione um arquivo.')
    name = secure_filename(file.filename)[:200]
    suffix = Path(name).suffix.lower()
    types = {'.pdf': 'application/pdf', '.txt': 'text/plain'}
    if suffix not in types or (final and suffix != '.pdf'):
        abort(400, description='Use PDF para a minuta; anexos aceitam PDF ou TXT.')
    content = file.stream.read(5 * 1024 * 1024 + 1)
    if not content or len(content) > 5 * 1024 * 1024:
        abort(400, description='O arquivo deve ter entre 1 byte e 5 MB.')
    if suffix == '.pdf' and not content.startswith(b'%PDF-'):
        abort(400, description='O arquivo não contém um cabeçalho PDF válido.')
    if suffix == '.txt':
        try:
            content.decode('utf-8')
        except UnicodeDecodeError:
            abort(400, description='O TXT deve estar em UTF-8.')
    return name, types[suffix], content, hashlib.sha256(content).hexdigest()


@bp.post('/auth/login')
def login():
    data = body()
    address = email(data, 'email')
    password = string(data, 'password', 256)
    user = db.session.execute(select(User).where(User.email == address)).scalar_one_or_none()
    if not user or not check_password_hash(user.password_hash, password):
        abort(401, description='E-mail ou senha incorretos.')
    return jsonify(token=serializer().dumps({'id': user.id}), user=user.to_dict())


@bp.get('/auth/me')
@require_user()
def me():
    return jsonify(g.user.to_dict())


@bp.get('/users')
@require_user('GESTOR')
def users():
    return jsonify([u.to_dict() for u in db.session.scalars(select(User).order_by(User.name))])


@bp.post('/users')
@require_user('GESTOR')
def create_user():
    data = body()
    role = string(data, 'role', 20)
    department = data.get('department')
    if role not in ROLES or (role == 'APROVADOR' and department not in DEPARTMENTS):
        abort(400, description='Papel ou departamento inválido.')
    password = string(data, 'password', 256)
    if len(password) < 10:
        abort(400, description='A senha deve ter pelo menos 10 caracteres.')
    user = User(name=string(data, 'name', 120), email=email(data, 'email'),
                role=role, department=department if role == 'APROVADOR' else None,
                password_hash=generate_password_hash(password))
    db.session.add(user)
    commit()
    return jsonify(user.to_dict()), 201


@bp.post('/requests')
@require_user('REQUISITANTE', 'GESTOR')
def create_request():
    # Multipart permite gravar pedido e anexos na mesma transação.
    if request.mimetype == 'multipart/form-data':
        data = request.form.to_dict()
        files = request.files.getlist('attachments')
    else:
        data, files = body(), []
    try:
        amount = Decimal(str(data.get('amount')))
        if not amount.is_finite() or amount < 0 or amount >= Decimal('10000000000') or amount.as_tuple().exponent < -2:
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        abort(400, description='Informe um valor positivo ou zero, com até duas casas decimais.')
    if len(files) > 5:
        abort(400, description='Envie no máximo cinco anexos.')
    item = ContractRequest(
        requester_id=g.user.id, subject=string(data, 'subject', 200),
        description=string(data, 'description', 10000), amount=amount,
        cost_center=string(data, 'cost_center', 100), supplier_name=string(data, 'supplier_name', 150),
        supplier_document=string(data, 'supplier_document', 30), supplier_email=email(data, 'supplier_email'),
    )
    for file in files:
        name, content_type, content, digest = upload(file)
        item.attachments.append(Attachment(name=name, content_type=content_type, content=content, sha256=digest))
    db.session.add(item)
    commit()
    return jsonify(serialize(item)), 201


@bp.get('/requests')
@require_user()
def list_requests():
    stmt = select(ContractRequest).order_by(ContractRequest.created_at.desc())
    if g.user.role == 'REQUISITANTE':
        stmt = stmt.where(ContractRequest.requester_id == g.user.id)
    elif g.user.role == 'FORNECEDOR':
        stmt = stmt.where(ContractRequest.supplier_email == g.user.email, ContractRequest.status.in_(['EM_ASSINATURA', 'ASSINADO']))
    # Aprovadores veem o fluxo inteiro; as pendências são filtradas por departamento nas notificações.
    return jsonify([serialize(item) for item in db.session.scalars(stmt)])


@bp.get('/requests/<int:request_id>')
@require_user()
def request_detail(request_id):
    return jsonify(serialize(get_request(request_id)))


@bp.patch('/requests/<int:request_id>/approve')
@require_user('APROVADOR')
def approve(request_id):
    item = get_request(request_id, lock=True)
    if item.status != 'EM_APROVACAO':
        abort(409, description='Esta solicitação não está em aprovação.')
    if item.requester_id == g.user.id:
        abort(403, description='Você não pode aprovar sua própria solicitação.')
    if any(a.department == g.user.department for a in item.approvals):
        abort(409, description='Seu departamento já decidiu sobre esta solicitação.')
    data = body()
    decision = data.get('decision')
    if decision not in ('APROVAR', 'REPROVAR'):
        abort(400, description='Use APROVAR ou REPROVAR.')
    comment = string(data, 'comment', 2000, required=decision == 'REPROVAR')
    approval = Approval(request_id=item.id, approver_id=g.user.id,
                        department=g.user.department, decision=decision, comment=comment)
    db.session.add(approval)
    if decision == 'REPROVAR':
        item.status = 'REPROVADO'
    elif {a.department for a in item.approvals if a.decision == 'APROVAR'} | {g.user.department} == set(DEPARTMENTS):
        item.status = 'APROVADO'
    commit()
    db.session.expire(item, ['approvals'])
    return jsonify(serialize(item))


@bp.get('/requests/<int:request_id>/attachments/<int:attachment_id>')
@require_user()
def attachment(request_id, attachment_id):
    item = get_request(request_id)
    if g.user.role == 'FORNECEDOR':
        abort(403, description='Somente o documento final é disponibilizado ao fornecedor.')
    file = next((a for a in item.attachments if a.id == attachment_id), None)
    if not file:
        abort(404, description='Anexo não encontrado.')
    return send_file(io.BytesIO(file.content), mimetype=file.content_type, as_attachment=True, download_name=file.name)


@bp.post('/requests/<int:request_id>/contract')
@require_user('GESTOR')
def prepare_contract(request_id):
    item = get_request(request_id, lock=True)
    if item.status != 'APROVADO' or item.contract:
        abort(409, description='É necessário um pedido aprovado e ainda sem minuta.')
    try:
        starts = date.fromisoformat(request.form.get('starts_at', ''))
        ends = date.fromisoformat(request.form.get('ends_at', ''))
        if ends < starts:
            raise ValueError
    except ValueError:
        abort(400, description='Informe a vigência válida no formato AAAA-MM-DD.')
    name, _, content, digest = upload(request.files.get('document'), final=True)
    contract = Contract(request_id=item.id, manager_id=g.user.id, starts_at=starts, ends_at=ends,
                        document_name=name, document=content, document_sha256=digest)
    db.session.add(contract)
    commit()
    db.session.expire(item, ['contract'])
    return jsonify(serialize(item)), 201


@bp.post('/requests/<int:request_id>/send-signature')
@require_user('GESTOR')
def send_signature(request_id):
    item = get_request(request_id, lock=True)
    if item.status not in ('APROVADO', 'EM_ASSINATURA') or not item.contract:
        abort(409, description='Prepare a minuta de um pedido aprovado antes de enviar.')
    token = secrets.token_urlsafe(32)
    item.contract.signature_token_hash = hashlib.sha256(token.encode()).hexdigest()
    item.contract.signature_expires_at = now() + timedelta(days=7)
    item.status = 'EM_ASSINATURA'
    commit()
    return jsonify(signature_url=f"{os.getenv('FRONTEND_URL', 'http://127.0.0.1:5173')}/sign/{token}",
                   expires_at=item.contract.signature_expires_at.isoformat(),
                   message='Link gerado. Compartilhe com o fornecedor; não há envio de e-mail configurado.')


def signature_contract(token, lock=False):
    stmt = select(Contract).where(Contract.signature_token_hash == hashlib.sha256(token.encode()).hexdigest())
    if lock:
        # Mesma ordem de locks do envio: solicitação antes do contrato.
        request_id = db.session.scalar(select(Contract.request_id).where(
            Contract.signature_token_hash == hashlib.sha256(token.encode()).hexdigest()))
        if request_id is not None:
            db.session.execute(select(ContractRequest).where(ContractRequest.id == request_id).with_for_update())
        stmt = stmt.with_for_update()
    contract = db.session.execute(stmt).scalar_one_or_none()
    if not contract or not contract.signature_expires_at:
        abort(404, description='Link de assinatura inválido.')
    expires = contract.signature_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now():
        abort(410, description='Link expirado. Solicite um novo ao gestor.')
    return contract


@bp.get('/signatures/<token>')
def signature_info(token):
    contract = signature_contract(token)
    item = db.session.get(ContractRequest, contract.request_id)
    return jsonify(subject=item.subject, supplier_name=item.supplier_name,
                   document_name=contract.document_name, sha256=contract.document_sha256,
                   signed=contract.signed_at is not None, consent_text=CONSENT)


@bp.get('/signatures/<token>/document')
def signature_document(token):
    contract = signature_contract(token)
    return send_file(io.BytesIO(contract.document), mimetype='application/pdf',
                     as_attachment=True, download_name=contract.document_name)


@bp.post('/signatures/<token>')
def sign(token):
    contract = signature_contract(token, lock=True)
    if contract.signed_at:
        abort(409, description='Este documento já foi aceito.')
    data = body()
    if data.get('consent') is not True:
        abort(400, description='É necessário confirmar a leitura e o aceite.')
    item = db.session.get(ContractRequest, contract.request_id)
    if email(data, 'email') != item.supplier_email:
        abort(400, description='Informe o e-mail do fornecedor cadastrado no pedido.')
    contract.signer_name = string(data, 'name', 150)
    contract.signer_email = item.supplier_email
    contract.consent_text = CONSENT
    contract.signed_at = now()
    item.status = 'ASSINADO'
    commit()
    return jsonify(message='Aceite demonstrativo registrado. Contrato arquivado no sistema.')


@bp.get('/requests/<int:request_id>/document')
@require_user()
def archived_document(request_id):
    item = get_request(request_id)
    if not item.contract:
        abort(404, description='Minuta ainda não disponível.')
    return send_file(io.BytesIO(item.contract.document), mimetype='application/pdf',
                     as_attachment=True, download_name=item.contract.document_name)


@bp.get('/notifications')
@require_user()
def notifications():
    result = []
    if g.user.role == 'APROVADOR':
        decided = select(Approval.request_id).where(Approval.department == g.user.department)
        pending = db.session.scalars(select(ContractRequest).where(
            ContractRequest.status == 'EM_APROVACAO', ~ContractRequest.id.in_(decided),
            ContractRequest.requester_id != g.user.id))
        result += [dict(id=f'pending-{r.id}', request_id=r.id, message=f'Aprovação pendente: {r.subject}', kind='approval') for r in pending]
    if g.user.role in ('GESTOR', 'REQUISITANTE'):
        today = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        stmt = select(ContractRequest).join(Contract, Contract.request_id == ContractRequest.id).where(
            ContractRequest.status == 'ASSINADO', Contract.ends_at <= today + timedelta(days=30))
        if g.user.role == 'REQUISITANTE':
            stmt = stmt.where(ContractRequest.requester_id == g.user.id)
        result += [dict(id=f'expiry-{r.id}', request_id=r.id, message=f"{'Vencido' if r.contract.ends_at < today else 'Vence em breve'}: {r.subject} ({r.contract.ends_at.isoformat()})", kind='expiry') for r in db.session.scalars(stmt)]
    if g.user.role == 'GESTOR':
        result += [dict(id=f'ready-{r.id}', request_id=r.id, message=f'Preparar contrato: {r.subject}', kind='ready')
                   for r in db.session.scalars(select(ContractRequest).where(ContractRequest.status == 'APROVADO'))]
    return jsonify(result)


def register_clm(app):
    secret_file = Path(app.instance_path) / 'session-secret'
    if not os.getenv('SECRET_KEY') and not secret_file.exists():
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        secret_file.write_text(secrets.token_hex(32), encoding='utf-8')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or secret_file.read_text(encoding='utf-8')
    app.config['MAX_CONTENT_LENGTH'] = 26 * 1024 * 1024
    app.register_blueprint(bp)

    @app.errorhandler(HTTPException)
    def http_error(exc):
        db.session.rollback()
        return jsonify(erro=exc.description), exc.code

    @app.before_request
    def protect_legacy():
        legacy = {'clientes', 'usuarios', 'contratos', 'clausulas', 'aditivos', 'historico-status'}
        if request.path.strip('/').split('/')[0] in legacy:
            if authenticate().role != 'GESTOR':
                abort(403, description='Cadastros legados são restritos ao gestor.')

    @app.cli.command('create-user')
    @click.option('--name', prompt='Nome')
    @click.option('--email', 'address', prompt='E-mail')
    @click.option('--role', type=click.Choice(ROLES), default='GESTOR')
    @click.option('--department', type=click.Choice(DEPARTMENTS))
    @click.password_option()
    def create_user_cli(name, address, role, department, password):
        """Provisiona contas sem cadastro público de papéis privilegiados."""
        if len(password) < 10 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', address) or not name.strip():
            raise click.ClickException('Nome, e-mail ou senha inválidos (mínimo 10 caracteres).')
        if role == 'APROVADOR' and department not in DEPARTMENTS:
            raise click.ClickException('Informe --department para um aprovador.')
        if db.session.scalar(select(User).where(User.email == address.strip().lower())):
            raise click.ClickException('E-mail já cadastrado.')
        db.session.add(User(name=name.strip(), email=address.strip().lower(), role=role,
                            department=department if role == 'APROVADOR' else None,
                            password_hash=generate_password_hash(password)))
        db.session.commit()
        click.echo('Usuário criado.')
