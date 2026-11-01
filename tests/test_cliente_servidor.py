"""Garantias na fronteira entre clientes independentes e a API real."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from server.app import create_app
from tests.helpers import cliente_identificado

ORIGEM = 'http://127.0.0.1:8080'


@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY='chave-estavel-exclusiva-para-testes')
    return app


def test_aplicacao_unica_entrega_interface_e_api(app):
    cliente = app.test_client()
    assert cliente.get('/').mimetype == 'text/html'
    assert cliente.get('/api').is_json
    assert cliente.get('/static/js/app.js').status_code == 200
    assert cliente.get('/api/health').json == {'status': 'ok'}
    assert app.extensions['livraria'].modulos.clientes.listar_clientes() == []


def test_bootstrap_explicito_emite_bearer_sem_cookie(app):
    cliente = app.test_client()
    assert cliente.get('/api/estado').status_code == 401
    resposta = cliente.post('/api/sessoes', json={})
    assert resposta.status_code == 201
    assert resposta.json['tipo'] == 'Bearer'
    assert resposta.json['expira_em_segundos'] == 86400
    assert not resposta.headers.get('Set-Cookie')
    token = resposta.json['token']
    estado = cliente.get('/api/estado', headers={'Authorization': f'Bearer {token}'})
    assert estado.status_code == 200
    assert estado.headers['Cache-Control'] == 'no-store'
    assert estado.headers['X-Request-ID']


@pytest.mark.parametrize('authorization', ['', 'Bearer invalido', 'Basic abc', 'Bearer '])
def test_token_ausente_ou_invalido_nao_muda_estado(app, authorization):
    resposta = app.test_client().post('/api/desejos', json={'livro_id': '1984'},
                                    headers={'Authorization': authorization})
    assert resposta.status_code == 401
    assert resposta.is_json
    assert app.extensions['livraria'].modulos.clientes.listar_clientes() == []


def test_token_expirado_e_token_assinado_por_outra_chave(app):
    with patch('itsdangerous.timed.time.time', return_value=1000):
        token = app.test_client().post('/api/sessoes', json={}).json['token']
    resposta = app.test_client().get('/api/estado', headers={'Authorization': f'Bearer {token}'})
    assert resposta.status_code == 401
    outro = create_app()
    outro.config['SECRET_KEY'] = 'outra-chave-totalmente-diferente'
    token = app.test_client().post('/api/sessoes', json={}).json['token']
    assert outro.test_client().get('/api/estado', headers={'Authorization': f'Bearer {token}'}).status_code == 401


def test_preflight_nao_cria_cliente_e_habilita_apenas_origem_permitida(app):
    resposta = app.test_client().options('/api/reservas', headers={
        'Origin': ORIGEM, 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'authorization, content-type',
    })
    assert resposta.status_code == 204
    assert resposta.headers['Access-Control-Allow-Origin'] == ORIGEM
    assert 'Authorization' in resposta.headers['Access-Control-Allow-Headers']
    assert 'Origin' in resposta.headers['Vary']
    assert not resposta.headers.get('Access-Control-Allow-Credentials')
    assert app.extensions['livraria'].modulos.clientes.listar_clientes() == []


@pytest.mark.parametrize('path', ['/api/sessoes', '/api/reservas'])
def test_origem_negada_nao_executa_mutacao_nem_bootstrap(app, path):
    cliente = cliente_identificado(app)
    loja = app.extensions['livraria']
    antes = loja.livro('1984')['estoque']
    clientes = len(loja.modulos.clientes.listar_clientes())
    resposta = cliente.post(path, json={'livro_id': '1984', 'prazo': '2099-01-01T12:00:00Z'},
                           headers={'Origin': 'https://site-nao-permitido.example'})
    assert resposta.status_code == 403
    assert not resposta.headers.get('Access-Control-Allow-Origin')
    assert loja.livro('1984')['estoque'] == antes
    assert len(loja.modulos.clientes.listar_clientes()) == clientes


@pytest.mark.parametrize('metodo,cabecalho', [('DELETE', 'authorization'), ('POST', 'x-perfil-admin')])
def test_preflight_recusa_metodo_ou_cabecalho_nao_suportado(app, metodo, cabecalho):
    resposta = app.test_client().options('/api/reservas', headers={
        'Origin': ORIGEM, 'Access-Control-Request-Method': metodo,
        'Access-Control-Request-Headers': cabecalho,
    })
    assert resposta.status_code in {403, 405}


def test_sessoes_isoladas_compartilham_catalogo_sem_compartilhar_reservas(app):
    ana, bia = cliente_identificado(app), cliente_identificado(app)
    prazo = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    reserva = ana.post('/api/reservas', json={'livro_id': '1984', 'prazo': prazo})
    assert reserva.status_code == 201
    assert bia.get('/api/livros/1984').json['estoque'] == 2
    assert bia.get('/api/estado').json['reservas'] == []
    assert bia.post(f'/api/reservas/{reserva.json["id"]}/cancelar').status_code == 404


def test_reservas_http_concorrentes_nao_vendem_ultimo_exemplar_duas_vezes(app):
    app.extensions['livraria'].atualizar_estoque('1984', 1)
    clientes = [cliente_identificado(app), cliente_identificado(app)]
    prazo = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    def reservar(cliente):
        return cliente.post('/api/reservas', json={'livro_id': '1984', 'prazo': prazo}).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(reservar, clientes)) == [201, 409]
    assert app.extensions['livraria'].livro('1984')['estoque'] == 0


def test_erros_inesperados_sao_json_sem_expor_excecao(app, monkeypatch):
    cliente = cliente_identificado(app)
    def falhar(*args):
        raise RuntimeError('segredo-interno-nao-pode-aparecer')
    monkeypatch.setattr(app.extensions['livraria'], 'estado', falhar)
    resposta = cliente.get('/api/estado', headers={'Origin': ORIGEM})
    assert resposta.status_code == 500
    assert resposta.is_json
    assert 'segredo-interno' not in resposta.get_data(as_text=True)
    assert resposta.headers['Access-Control-Allow-Origin'] == ORIGEM


def test_corpo_grande_e_json_invalido_nao_criam_sessao(app):
    cliente = app.test_client()
    assert cliente.post('/api/sessoes', data='{', content_type='application/json').status_code == 400
    assert cliente.post('/api/sessoes', json={'cliente_id': 'identidade-forjada'}).status_code == 400
    assert cliente.post('/api/sessoes', data='x' * (1024 * 1024 + 1), content_type='application/json').status_code == 413
    assert app.extensions['livraria'].modulos.clientes.listar_clientes() == []


@pytest.mark.parametrize('secret,origins', [('', ORIGEM), ('curta', ORIGEM), ('x' * 32, ''), ('x' * 32, '*')])
def test_producao_exige_chave_estavel_e_origem_explicita(monkeypatch, secret, origins):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', secret)
    monkeypatch.setenv('ALLOWED_ORIGINS', origins)
    with pytest.raises(ValueError):
        create_app()
