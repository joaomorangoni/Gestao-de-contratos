import io
from pathlib import Path

from flask import Blueprint, abort, jsonify, request
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from clm.auth import require_user
from .service import AIServiceError, analyze_risks, extract_proposal

bp = Blueprint('ai', __name__, url_prefix='/api/ai')
MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 60000


def read_pdf() -> bytes:
    file = request.files.get('file')
    if not file or not file.filename or Path(file.filename).suffix.lower() != '.pdf':
        abort(400, description='Envie um arquivo PDF no campo file.')
    content = file.stream.read(MAX_PDF_BYTES + 1)
    if len(content) > MAX_PDF_BYTES:
        abort(413, description='O PDF deve ter no máximo 5 MB.')
    if not content.startswith(b'%PDF-'):
        abort(400, description='Arquivo PDF inválido.')
    try:
        reader = PdfReader(io.BytesIO(content), strict=True)
        if reader.is_encrypted:
            abort(400, description='Remova a senha do PDF antes de enviar.')
        if not 1 <= len(reader.pages) <= 100:
            abort(400, description='Envie um PDF com 1 a 100 páginas.')
    except (PdfReadError, ValueError, KeyError, TypeError, OSError):
        abort(400, description='O PDF está corrompido ou não pode ser lido.')
    return content


@bp.errorhandler(AIServiceError)
def service_error(exc):
    return jsonify(erro=str(exc)), exc.status


@bp.post('/extrair-proposta')
@require_user('REQUISITANTE', 'GESTOR')
def proposal():
    result = extract_proposal(read_pdf())
    return jsonify(result.model_dump())


@bp.post('/analisar-riscos')
@require_user('REQUISITANTE', 'APROVADOR', 'GESTOR')
def risks():
    if request.files.get('file'):
        if request.form.get('text', '').strip():
            abort(400, description='Envie apenas PDF ou texto, não ambos.')
        result = analyze_risks(pdf=read_pdf())
    else:
        data = request.get_json(silent=True) if request.is_json else request.form
        text = data.get('text') if isinstance(data, dict) or hasattr(data, 'get') else None
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
            abort(400, description='Envie um PDF ou texto com 1 a 60.000 caracteres no campo text.')
        result = analyze_risks(text=text.strip())
    return jsonify(result.model_dump())
