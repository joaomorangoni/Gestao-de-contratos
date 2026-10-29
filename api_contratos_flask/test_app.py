import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
from app import app, db
from clm.models import User
from clm.auth import serializer
from werkzeug.security import generate_password_hash


class ContractFlowTest(unittest.TestCase):
    def setUp(self):
        self.context = app.app_context()
        self.context.push()
        db.create_all()
        self.client = app.test_client()
        manager = User(name='Gestor', email='gestor@example.com', role='GESTOR', password_hash=generate_password_hash('test-password'))
        db.session.add(manager)
        db.session.commit()
        self.client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + serializer().dumps({'id': manager.id})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def test_contract_lifecycle_and_history(self):
        customer = self.client.post('/clientes', json={'nome': 'Cliente teste'}).json
        payload = dict(numero='CT-01', titulo='Prestação de serviços',
                       cliente_id=customer['id'], data_inicio='2026-10-01', status='Rascunho')
        response = self.client.post('/contratos', json=payload)
        self.assertEqual(response.status_code, 201)
        contract_id = response.json['id']
        self.assertEqual(self.client.put(f'/contratos/{contract_id}', json={'status': 'Ativo'}).status_code, 200)
        history = self.client.get('/historico-status').json
        self.assertEqual(history[0]['status_anterior'], 'Rascunho')
        self.assertEqual(history[0]['status_novo'], 'Ativo')
        self.assertEqual(self.client.post('/contratos', json=payload).status_code, 409)
        self.assertEqual(self.client.get('/health').status_code, 200)

    def test_invalid_input_and_password_redaction(self):
        self.assertEqual(self.client.post('/clientes', json={'nome': ' '}).status_code, 400)
        self.assertEqual(self.client.post('/contratos', json={'valor_total': 'abc'}).status_code, 400)
        self.assertEqual(self.client.post('/contratos', json={'cliente_id': 1.5}).status_code, 400)
        user = self.client.post('/usuarios', json={'nome': 'Teste', 'email': 'teste@example.com', 'senha': 'segredo'})
        self.assertEqual(user.status_code, 201)
        self.assertNotIn('senha_hash', user.json)
        self.assertNotIn('senha', user.json)


if __name__ == '__main__':
    unittest.main()
