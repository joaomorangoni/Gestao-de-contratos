-- Esquema conceitual PostgreSQL.
-- A aplicação Flask/SQLAlchemy também cria as tabelas automaticamente no primeiro início.

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    phone VARCHAR(30),
    birth_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    role VARCHAR(30) NOT NULL DEFAULT 'worker',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE contracts_unreviewed (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) NOT NULL,
    birth_date DATE NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    address VARCHAR(255),
    job_title VARCHAR(150),
    employer_name VARCHAR(200),
    salary NUMERIC(12,2),
    contract_start_date DATE,
    contract_end_date DATE,
    document_filename VARCHAR(255),
    document_path VARCHAR(500),
    content_text TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    ai_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE contracts_reviewed (
    id SERIAL PRIMARY KEY,
    source_contract_id INTEGER NOT NULL UNIQUE REFERENCES contracts_unreviewed(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score NUMERIC(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    classification VARCHAR(50) NOT NULL DEFAULT 'pending',
    ai_summary TEXT,
    ai_findings JSONB,
    reviewed_by VARCHAR(100) DEFAULT 'ai',
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contracts_unreviewed_user_id ON contracts_unreviewed(user_id);
CREATE INDEX idx_contracts_unreviewed_cpf ON contracts_unreviewed(cpf);
CREATE INDEX idx_contracts_unreviewed_status ON contracts_unreviewed(status);
CREATE INDEX idx_contracts_reviewed_user_id ON contracts_reviewed(user_id);
CREATE INDEX idx_contracts_reviewed_source_id ON contracts_reviewed(source_contract_id);
