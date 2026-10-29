import io
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
from app import app, db
from ai.schemas import Proposal, RiskAnalysis
from ai.service import AIServiceError, extract_proposal, generate
from clm.auth import serializer
from clm.models import User
from google.genai import errors
from httpx import ReadTimeout
from pypdf import PdfWriter
from werkzeug.security import generate_password_hash

PROPOSAL = dict(nome_fornecedor='Empresa Exemplo', cnpj_fornecedor=None, valor_total=1250.50,
                prazo_vigencia_meses=12, objeto_resumido='Licenciamento anual')
RISK = dict(nivel_risco_geral='Alto', clausulas_atencao=[dict(
    clausula='Cláusula 5: responsabilidade ilimitada', motivo_risco='Exposição sem limite financeiro.',
    sugestao_correcao='Negociar limite proporcional ao valor contratado.')])


def pdf_bytes():
    stream = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(stream)
    return stream.getvalue()


class AIEndpointsTest(unittest.TestCase):
    def setUp(self):
        self.context = app.app_context()
        self.context.push()
        db.create_all()
        self.user = User(name='Teste IA', email='ia@example.com', role='REQUISITANTE',
                         password_hash=generate_password_hash('test-password'))
        db.session.add(self.user)
        db.session.commit()
        self.client = app.test_client()
        self.client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + serializer().dumps({'id':self.user.id})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def post_pdf(self, path, content=None, filename='proposta.pdf'):
        return self.client.post('/api/ai/'+path, data={'file':(io.BytesIO(content if content is not None else pdf_bytes()),filename)})

    @patch('ai.routes.extract_proposal', return_value=Proposal(**PROPOSAL))
    def test_extract_success_and_private_access(self, extract):
        response = self.post_pdf('extrair-proposta')
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json, PROPOSAL)
        self.assertTrue(extract.call_args.args[0].startswith(b'%PDF-'))
        self.client.environ_base.pop('HTTP_AUTHORIZATION')
        self.assertEqual(self.post_pdf('extrair-proposta').status_code, 401)
        self.user.role = 'FORNECEDOR'
        db.session.commit()
        self.client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + serializer().dumps({'id':self.user.id})
        self.assertEqual(self.post_pdf('analisar-riscos').status_code, 403)

    @patch('ai.routes.analyze_risks', return_value=RiskAnalysis(**RISK))
    def test_risks_accept_pdf_and_text(self, analyze):
        response = self.client.post('/api/ai/analisar-riscos', json={'text':'Cláusula 5: responsabilidade ilimitada'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, RISK)
        analyze.assert_called_with(text='Cláusula 5: responsabilidade ilimitada')
        self.assertEqual(self.post_pdf('analisar-riscos').status_code, 200)
        self.assertIn('pdf', analyze.call_args.kwargs)

    @patch('ai.routes.extract_proposal')
    def test_invalid_pdf_never_calls_gemini(self, extract):
        self.assertEqual(self.post_pdf('extrair-proposta', b'fake').status_code, 400)
        self.assertEqual(self.post_pdf('extrair-proposta', b'%PDF-invalid').status_code, 400)
        self.assertEqual(self.post_pdf('extrair-proposta', filename='x.txt').status_code, 400)
        self.assertEqual(self.post_pdf('extrair-proposta', b'%PDF-'+b'x'*(5*1024*1024)).status_code, 413)
        writer = PdfWriter(); writer.add_blank_page(width=200,height=200); writer.encrypt('secret')
        stream = io.BytesIO(); writer.write(stream)
        self.assertEqual(self.post_pdf('extrair-proposta', stream.getvalue()).status_code, 400)
        extract.assert_not_called()

    def test_invalid_text_and_missing_key(self):
        for value in ('', ' '*10, 'x'*60001, 42):
            self.assertEqual(self.client.post('/api/ai/analisar-riscos', json={'text':value}).status_code, 400)
        with patch.dict(os.environ, {'GEMINI_API_KEY':''}):
            self.assertEqual(self.post_pdf('extrair-proposta').status_code, 503)


class GeminiServiceTest(unittest.TestCase):
    @patch.dict(os.environ, {'GEMINI_API_KEY':'test-key'})
    @patch('ai.service.genai.Client')
    def test_structured_sdk_call_and_validation(self, client):
        model = client.return_value.__enter__.return_value.models
        model.generate_content.return_value = SimpleNamespace(text=json.dumps(PROPOSAL))
        self.assertEqual(extract_proposal(b'pdf').valor_total, 1250.50)
        args = model.generate_content.call_args.kwargs
        self.assertEqual(args['model'], 'gemini-2.5-flash')
        self.assertEqual(args['config'].response_mime_type, 'application/json')
        self.assertEqual(args['contents'][0].inline_data.mime_type, 'application/pdf')
        model.generate_content.return_value = SimpleNamespace(text='```json\n{}\n```')
        with self.assertRaises(AIServiceError) as error:
            extract_proposal(b'pdf')
        self.assertEqual(error.exception.status, 502)
        model.generate_content.return_value = SimpleNamespace(text=json.dumps({**PROPOSAL,'valor_total':None}))
        with self.assertRaises(AIServiceError) as error:
            extract_proposal(b'pdf')
        self.assertEqual(error.exception.status, 422)

    @patch.dict(os.environ, {'GEMINI_API_KEY':'test-key'})
    @patch('ai.service.genai.Client')
    def test_provider_errors_and_empty_response(self, client):
        model = client.return_value.__enter__.return_value.models
        for failure, status in ((errors.ClientError(429, {'error':{'message':'secret'}}),429),
                                (errors.ClientError(403, {'error':{'message':'secret'}}),503),
                                (errors.ServerError(500, {'error':{'message':'secret'}}),502),
                                (ReadTimeout('secret'),504)):
            model.generate_content.side_effect = failure
            with self.assertRaises(AIServiceError) as error:
                generate(RiskAnalysis,'audit',text='contract')
            self.assertEqual(error.exception.status,status)
            self.assertNotIn('secret',str(error.exception))
        model.generate_content.side_effect = None
        model.generate_content.return_value = SimpleNamespace(text=None)
        with self.assertRaises(AIServiceError) as error:
            generate(RiskAnalysis,'audit',text='contract')
        self.assertEqual(error.exception.status,422)


if __name__ == '__main__':
    unittest.main()
