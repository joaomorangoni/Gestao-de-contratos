from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(30), nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    role = db.Column(db.String(30), nullable=False, default="worker")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    contracts = db.relationship(
        "UnreviewedContract",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "cpf": self.cpf,
            "phone": self.phone,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "is_active": self.is_active,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UnreviewedContract(db.Model):
    __tablename__ = "contracts_unreviewed"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=False, index=True)
    birth_date = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    job_title = db.Column(db.String(150), nullable=True)
    employer_name = db.Column(db.String(200), nullable=True)
    salary = db.Column(db.Numeric(12, 2), nullable=True)
    contract_start_date = db.Column(db.Date, nullable=True)
    contract_end_date = db.Column(db.Date, nullable=True)
    document_filename = db.Column(db.String(255), nullable=True)
    document_path = db.Column(db.String(500), nullable=True)
    content_text = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    ai_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    user = db.relationship("User", back_populates="contracts")
    reviewed = db.relationship(
        "ReviewedContract",
        back_populates="source_contract",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "cpf": self.cpf,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "job_title": self.job_title,
            "employer_name": self.employer_name,
            "salary": float(self.salary) if self.salary is not None else None,
            "contract_start_date": self.contract_start_date.isoformat() if self.contract_start_date else None,
            "contract_end_date": self.contract_end_date.isoformat() if self.contract_end_date else None,
            "document_filename": self.document_filename,
            "document_path": self.document_path,
            "content_text": self.content_text,
            "status": self.status,
            "ai_error": self.ai_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ReviewedContract(db.Model):
    __tablename__ = "contracts_reviewed"

    id = db.Column(db.Integer, primary_key=True)
    source_contract_id = db.Column(
        db.Integer,
        db.ForeignKey("contracts_unreviewed.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = db.Column(db.Numeric(5, 2), nullable=False)
    classification = db.Column(db.String(50), nullable=False, default="pending")
    ai_summary = db.Column(db.Text, nullable=True)
    ai_findings = db.Column(db.JSON, nullable=True)
    reviewed_by = db.Column(db.String(100), nullable=True, default="ai")
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    source_contract = db.relationship("UnreviewedContract", back_populates="reviewed")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "source_contract_id": self.source_contract_id,
            "user_id": self.user_id,
            "score": float(self.score),
            "classification": self.classification,
            "ai_summary": self.ai_summary,
            "ai_findings": self.ai_findings,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "contract": self.source_contract.to_dict() if self.source_contract else None,
        }
