import io
import os
import unittest
from datetime import timedelta

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
from app import app, db
from clm.models import User, Contract, ContractRequest, now
from clm.auth import serializer
from werkzeug.security import generate_password_hash

PDF = b'%PDF-1.4\nTest fixture document\n%%EOF'


class CLMFlowTest(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = app.test_client()
        self.users = {}
        for name, role, department in [('owner','REQUISITANTE',None),('other','REQUISITANTE',None),
                                      ('manager','GESTOR',None),('finance','APROVADOR','FINANCEIRO'),
                                      ('legal','APROVADOR','JURIDICO'),('compliance','APROVADOR','COMPLIANCE'),
                                      ('supplier','FORNECEDOR',None)]:
            user = User(name=name, email=name+'@example.com', role=role, department=department,
                        password_hash=generate_password_hash('test-password'))
            db.session.add(user)
            self.users[name] = user
        db.session.commit()
        self.as_user('owner')

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    def as_user(self, name):
        self.client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + serializer().dumps({'id': self.users[name].id})

    def create(self, **changes):
        data = dict(subject='Serviços de TI', description='Escopo de teste', amount='1250.50',
                    cost_center='TI', supplier_name='Fornecedor', supplier_document='12345678900',
                    supplier_email='supplier@example.com')
        data.update(changes)
        return self.client.post('/api/requests', json=data)

    def approve_all(self, request_id):
        for name in ('finance','legal','compliance'):
            self.as_user(name)
            response = self.client.patch(f'/api/requests/{request_id}/approve', json={'decision':'APROVAR'})
            self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json['status'], 'APROVADO')

    def test_login_and_role_isolation(self):
        self.client.environ_base.pop('HTTP_AUTHORIZATION')
        self.assertEqual(self.client.get('/api/requests').status_code, 401)
        self.assertEqual(self.client.post('/api/auth/login', json={'email':'owner@example.com','password':'wrong'}).status_code, 401)
        result = self.client.post('/api/auth/login', json={'email':'owner@example.com','password':'test-password'})
        self.assertEqual(result.status_code, 200)
        self.assertNotIn('password_hash', result.json['user'])
        self.as_user('owner')
        item = self.create().json
        self.assertEqual(self.client.post('/api/users', json={}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/requests/{item['id']}/approve", json={'decision':'APROVAR'}).status_code, 403)
        self.as_user('other')
        self.assertEqual(self.client.get('/api/requests').json, [])
        self.assertEqual(self.client.get(f"/api/requests/{item['id']}").status_code, 403)
        self.assertEqual(self.client.get('/contratos').status_code, 403)

    def test_approvals_rejection_and_notifications(self):
        item = self.create().json
        path = f"/api/requests/{item['id']}/approve"
        self.as_user('finance')
        self.assertEqual(len(self.client.get('/api/notifications').json), 1)
        self.assertEqual(self.client.patch(path, json={'decision':'REPROVAR'}).status_code, 400)
        approved = self.client.patch(path, json={'decision':'APROVAR'})
        self.assertEqual(approved.json['status'], 'EM_APROVACAO')
        self.assertEqual(self.client.patch(path, json={'decision':'APROVAR'}).status_code, 409)
        self.assertEqual(self.client.get('/api/notifications').json, [])
        self.as_user('legal')
        rejected = self.client.patch(path, json={'decision':'REPROVAR','comment':'Falta escopo.'})
        self.assertEqual(rejected.json['status'], 'REPROVADO')
        self.assertEqual(rejected.json['approvals'][-1]['comment'], 'Falta escopo.')
        self.as_user('compliance')
        self.assertEqual(self.client.patch(path, json={'decision':'APROVAR'}).status_code, 409)

    def test_full_flow_document_signature_archive_and_expiry(self):
        item = self.create().json
        request_id = item['id']
        self.as_user('manager')
        self.assertEqual(self.client.post(f'/api/requests/{request_id}/send-signature').status_code, 409)
        self.approve_all(request_id)
        self.as_user('manager')
        response = self.client.post(f'/api/requests/{request_id}/contract', data={
            'starts_at':'2026-01-01','ends_at':'2026-01-02','document':(io.BytesIO(PDF),'contrato.pdf')})
        self.assertEqual(response.status_code, 201, response.json)
        link = self.client.post(f'/api/requests/{request_id}/send-signature').json['signature_url']
        token = link.rsplit('/',1)[1]
        public = app.test_client()
        self.assertEqual(public.get(f'/api/signatures/{token}/document').data, PDF)
        self.assertEqual(public.get('/api/requests').status_code, 401)
        self.assertEqual(public.post(f'/api/signatures/{token}', json={'name':'Fornecedor','email':'supplier@example.com','consent':False}).status_code, 400)
        signed = public.post(f'/api/signatures/{token}', json={'name':'Fornecedor','email':'supplier@example.com','consent':True})
        self.assertEqual(signed.status_code, 200, signed.json)
        self.assertEqual(public.post(f'/api/signatures/{token}', json={'name':'Fornecedor','email':'supplier@example.com','consent':True}).status_code, 409)
        self.assertEqual(self.client.get(f'/api/requests/{request_id}').json['status'], 'ASSINADO')
        self.assertEqual(self.client.get(f'/api/requests/{request_id}/document').data, PDF)
        self.assertTrue(any(n['kind']=='expiry' for n in self.client.get('/api/notifications').json))
        self.assertEqual(self.client.post(f'/api/requests/{request_id}/send-signature').status_code, 409)

    def test_upload_atomicity_and_access(self):
        data = dict(subject='Contrato',description='Escopo',amount='10.00',cost_center='TI',
                    supplier_name='Empresa',supplier_document='123',supplier_email='supplier@example.com')
        invalid = self.client.post('/api/requests', data={**data,'attachments':(io.BytesIO(b'fake'),'fake.pdf')})
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(db.session.query(ContractRequest).count(), 0)
        valid = self.client.post('/api/requests', data={**data,'attachments':(io.BytesIO(PDF),'proposta.pdf')})
        self.assertEqual(valid.status_code, 201, valid.json)
        item = valid.json
        path = f"/api/requests/{item['id']}/attachments/{item['attachments'][0]['id']}"
        self.assertEqual(self.client.get(path).data, PDF)
        self.as_user('other')
        self.assertEqual(self.client.get(path).status_code, 403)

    def test_validation_and_link_rotation(self):
        for amount in ('NaN','-1','1.005','10000000000'):
            self.assertEqual(self.create(amount=amount).status_code, 400)
        self.assertEqual(self.create(supplier_email='invalid').status_code, 400)
        item = self.create().json
        self.approve_all(item['id'])
        self.as_user('manager')
        path = f"/api/requests/{item['id']}"
        invalid_dates = self.client.post(path+'/contract', data={'starts_at':'2026-02-01','ends_at':'2026-01-01','document':(io.BytesIO(PDF),'x.pdf')})
        self.assertEqual(invalid_dates.status_code, 400)
        self.client.post(path+'/contract',data={'starts_at':'2026-01-01','ends_at':'2027-01-01','document':(io.BytesIO(PDF),'x.pdf')})
        old = self.client.post(path+'/send-signature').json['signature_url'].rsplit('/',1)[1]
        new = self.client.post(path+'/send-signature').json['signature_url'].rsplit('/',1)[1]
        self.assertEqual(self.client.get('/api/signatures/'+old).status_code, 404)
        contract = db.session.query(Contract).one()
        contract.signature_expires_at = now()-timedelta(days=1)
        db.session.commit()
        self.assertEqual(self.client.get('/api/signatures/'+new).status_code, 410)


if __name__ == '__main__':
    unittest.main()
