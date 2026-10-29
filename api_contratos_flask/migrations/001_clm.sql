-- Esquema CLM aditivo. Não remove nem altera as tabelas legadas.

BEGIN;


CREATE TABLE IF NOT EXISTS clm_user (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash TEXT NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	department VARCHAR(20), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (role IN ('REQUISITANTE','APROVADOR','GESTOR','FORNECEDOR')), 
	CHECK ((role = 'APROVADOR' AND department IN ('FINANCEIRO','JURIDICO','COMPLIANCE')) OR (role <> 'APROVADOR' AND department IS NULL)), 
	UNIQUE (email)
)

;


CREATE TABLE IF NOT EXISTS clm_request (
	id SERIAL NOT NULL, 
	requester_id INTEGER NOT NULL, 
	subject VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	cost_center VARCHAR(100) NOT NULL, 
	supplier_name VARCHAR(150) NOT NULL, 
	supplier_document VARCHAR(30) NOT NULL, 
	supplier_email VARCHAR(254) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (amount >= 0), 
	CHECK (status IN ('EM_APROVACAO','REPROVADO','APROVADO','EM_ASSINATURA','ASSINADO')), 
	FOREIGN KEY(requester_id) REFERENCES clm_user (id)
)

;

CREATE INDEX IF NOT EXISTS ix_clm_request_supplier_email ON clm_request (supplier_email);

CREATE INDEX IF NOT EXISTS ix_clm_request_status ON clm_request (status);

CREATE INDEX IF NOT EXISTS ix_clm_request_requester_id ON clm_request (requester_id);


CREATE TABLE IF NOT EXISTS clm_approval (
	id SERIAL NOT NULL, 
	request_id INTEGER NOT NULL, 
	approver_id INTEGER NOT NULL, 
	department VARCHAR(20) NOT NULL, 
	decision VARCHAR(10) NOT NULL, 
	comment TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_clm_approval_department UNIQUE (request_id, department), 
	CHECK (decision IN ('APROVAR','REPROVAR')), 
	CHECK (department IN ('FINANCEIRO','JURIDICO','COMPLIANCE')), 
	CHECK (decision <> 'REPROVAR' OR length(trim(comment)) > 0 AND comment IS NOT NULL), 
	FOREIGN KEY(request_id) REFERENCES clm_request (id), 
	FOREIGN KEY(approver_id) REFERENCES clm_user (id)
)

;


CREATE TABLE IF NOT EXISTS clm_attachment (
	id SERIAL NOT NULL, 
	request_id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	content_type VARCHAR(100) NOT NULL, 
	content BYTEA NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(request_id) REFERENCES clm_request (id)
)

;

CREATE INDEX IF NOT EXISTS ix_clm_attachment_request_id ON clm_attachment (request_id);


CREATE TABLE IF NOT EXISTS clm_contract (
	id SERIAL NOT NULL, 
	request_id INTEGER NOT NULL, 
	manager_id INTEGER NOT NULL, 
	starts_at DATE NOT NULL, 
	ends_at DATE NOT NULL, 
	document_name VARCHAR(200) NOT NULL, 
	document BYTEA NOT NULL, 
	document_sha256 VARCHAR(64) NOT NULL, 
	signature_token_hash VARCHAR(64), 
	signature_expires_at TIMESTAMP WITH TIME ZONE, 
	signed_at TIMESTAMP WITH TIME ZONE, 
	signer_name VARCHAR(150), 
	signer_email VARCHAR(254), 
	consent_text TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (ends_at >= starts_at), 
	UNIQUE (request_id), 
	FOREIGN KEY(request_id) REFERENCES clm_request (id), 
	FOREIGN KEY(manager_id) REFERENCES clm_user (id), 
	UNIQUE (signature_token_hash)
)

;

CREATE INDEX IF NOT EXISTS ix_clm_contract_ends_at ON clm_contract (ends_at);

ALTER TABLE clm_user ENABLE ROW LEVEL SECURITY;

ALTER TABLE clm_request ENABLE ROW LEVEL SECURITY;

ALTER TABLE clm_approval ENABLE ROW LEVEL SECURITY;

ALTER TABLE clm_attachment ENABLE ROW LEVEL SECURITY;

ALTER TABLE clm_contract ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE clm_user FROM anon, authenticated;

REVOKE ALL ON TABLE clm_request FROM anon, authenticated;

REVOKE ALL ON TABLE clm_approval FROM anon, authenticated;

REVOKE ALL ON TABLE clm_attachment FROM anon, authenticated;

REVOKE ALL ON TABLE clm_contract FROM anon, authenticated;

COMMIT;
