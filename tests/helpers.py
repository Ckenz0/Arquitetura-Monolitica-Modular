"""Bootstrap HTTP real compartilhado pelos testes de regressão."""


def cliente_identificado(app):
    cliente = app.test_client()
    resposta = cliente.post('/api/sessoes', json={})
    assert resposta.status_code == 201
    cliente.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {resposta.json["token"]}'
    return cliente
