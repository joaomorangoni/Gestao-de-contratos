from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StructuredResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Proposal(StructuredResponse):
    nome_fornecedor: str = Field(min_length=1, max_length=150)
    cnpj_fornecedor: str | None = Field(max_length=30)
    valor_total: float | None = Field(ge=0, lt=10_000_000_000, allow_inf_nan=False)
    prazo_vigencia_meses: int | None = Field(ge=0, le=1200, strict=True)
    objeto_resumido: str = Field(min_length=1, max_length=200)


class RiskClause(StructuredResponse):
    clausula: str = Field(min_length=1, max_length=2000)
    motivo_risco: str = Field(min_length=1, max_length=3000)
    sugestao_correcao: str = Field(min_length=1, max_length=3000)


class RiskAnalysis(StructuredResponse):
    nivel_risco_geral: Literal['Baixo', 'Médio', 'Alto']
    clausulas_atencao: list[RiskClause] = Field(max_length=30)
