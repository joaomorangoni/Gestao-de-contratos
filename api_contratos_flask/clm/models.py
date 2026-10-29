from datetime import datetime, timezone
from extensions import db

ROLES = ('REQUISITANTE', 'APROVADOR', 'GESTOR', 'FORNECEDOR')
DEPARTMENTS = ('FINANCEIRO', 'JURIDICO', 'COMPLIANCE')
STATUSES = ('EM_APROVACAO', 'REPROVADO', 'APROVADO', 'EM_ASSINATURA', 'ASSINADO')


def now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = 'clm_user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(20))
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    __table_args__ = (
        db.CheckConstraint("role IN ('REQUISITANTE','APROVADOR','GESTOR','FORNECEDOR')"),
        db.CheckConstraint("(role = 'APROVADOR' AND department IN ('FINANCEIRO','JURIDICO','COMPLIANCE')) OR (role <> 'APROVADOR' AND department IS NULL)"),
    )

    def to_dict(self):
        return dict(id=self.id, name=self.name, email=self.email, role=self.role, department=self.department)


class ContractRequest(db.Model):
    __tablename__ = 'clm_request'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('clm_user.id'), nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    cost_center = db.Column(db.String(100), nullable=False)
    supplier_name = db.Column(db.String(150), nullable=False)
    supplier_document = db.Column(db.String(30), nullable=False)
    supplier_email = db.Column(db.String(254), nullable=False, index=True)
    status = db.Column(db.String(20), default='EM_APROVACAO', nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    __table_args__ = (
        db.CheckConstraint('amount >= 0'),
        db.CheckConstraint("status IN ('EM_APROVACAO','REPROVADO','APROVADO','EM_ASSINATURA','ASSINADO')"),
    )
    requester = db.relationship(User)
    approvals = db.relationship('Approval', order_by='Approval.created_at')
    attachments = db.relationship('Attachment', order_by='Attachment.id')
    contract = db.relationship('Contract', uselist=False)


class Approval(db.Model):
    __tablename__ = 'clm_approval'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('clm_request.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('clm_user.id'), nullable=False)
    department = db.Column(db.String(20), nullable=False)
    decision = db.Column(db.String(10), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    approver = db.relationship(User)
    __table_args__ = (
        db.UniqueConstraint('request_id', 'department', name='uq_clm_approval_department'),
        db.CheckConstraint("decision IN ('APROVAR','REPROVAR')"),
        db.CheckConstraint("department IN ('FINANCEIRO','JURIDICO','COMPLIANCE')"),
        db.CheckConstraint("decision <> 'REPROVAR' OR length(trim(comment)) > 0 AND comment IS NOT NULL"),
    )


class Attachment(db.Model):
    __tablename__ = 'clm_attachment'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('clm_request.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    content = db.deferred(db.Column(db.LargeBinary, nullable=False))
    sha256 = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)


class Contract(db.Model):
    __tablename__ = 'clm_contract'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('clm_request.id'), nullable=False, unique=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('clm_user.id'), nullable=False)
    starts_at = db.Column(db.Date, nullable=False)
    ends_at = db.Column(db.Date, nullable=False, index=True)
    document_name = db.Column(db.String(200), nullable=False)
    document = db.deferred(db.Column(db.LargeBinary, nullable=False))
    document_sha256 = db.Column(db.String(64), nullable=False)
    signature_token_hash = db.Column(db.String(64), unique=True)
    signature_expires_at = db.Column(db.DateTime(timezone=True))
    signed_at = db.Column(db.DateTime(timezone=True))
    signer_name = db.Column(db.String(150))
    signer_email = db.Column(db.String(254))
    consent_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    __table_args__ = (db.CheckConstraint('ends_at >= starts_at'),)
