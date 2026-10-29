export type Role = 'REQUISITANTE' | 'APROVADOR' | 'GESTOR' | 'FORNECEDOR';
export type Department = 'FINANCEIRO' | 'JURIDICO' | 'COMPLIANCE';
export type Status = 'EM_APROVACAO' | 'REPROVADO' | 'APROVADO' | 'EM_ASSINATURA' | 'ASSINADO';
export interface User {id: number; name: string; email: string; role: Role; department: Department | null}
export interface Approval {id: number; department: Department; decision: 'APROVAR' | 'REPROVAR'; comment: string; approver: string; created_at: string}
export interface Contract {id: number; starts_at: string; ends_at: string; document_name: string; document_sha256: string; signed_at: string | null; signer_name: string | null; signer_email: string | null}
export interface ContractRequest {id: number; subject: string; description: string; amount: string; cost_center: string; supplier_name: string; supplier_document: string; supplier_email: string; status: Status; created_at: string; requester: User; approvals: Approval[]; attachments: {id: number; name: string; sha256: string}[]; contract: Contract | null}
export interface Notification {id: string; request_id: number; message: string; kind: string}
