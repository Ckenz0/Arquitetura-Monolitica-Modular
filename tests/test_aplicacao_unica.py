"""O monólito entrega a interface e a API no mesmo servidor."""

import re

import pytest


def test_um_app_entrega_pagina_assets_e_api_sem_expor_arquivos_internos():
    from server.app import create_app
    cliente = create_app().test_client()
    pagina = cliente.get('/')
    assert pagina.status_code == 200 and pagina.mimetype == 'text/html'
    html = pagina.get_data(as_text=True)
    assets = re.findall(r'(?:src|href)="(/static/[^"]+)"', html)
    assert assets
    for asset in assets:
        assert cliente.get(asset).status_code == 200, asset
    assert cliente.get('/api/health').json == {'status': 'ok'}
    for path in ('/.env', '/.git/config', '/server/config.py', '/docs/arquitetura.md', '/static/../server/config.py'):
        assert cliente.get(path).status_code == 404, path


def test_frontend_carrega_modulos_de_negocio_como_es_modules():
    from server.app import create_app
    cliente = create_app().test_client()
    html = cliente.get('/').get_data(as_text=True)
    assert re.search(r'<script[^>]*type="module"[^>]*src="/static/js/app.js"', html)
    for modulo in ('catalogo', 'visita', 'comunidade', 'perfil'):
        resposta = cliente.get(f'/static/js/modules/{modulo}.js')
        assert resposta.status_code == 200
        assert 'export function renderizar' in resposta.get_data(as_text=True)


@pytest.mark.parametrize('porta', [5001, 8000])
def test_origem_do_proprio_app_funciona_em_porta_personalizada(porta):
    from server.app import create_app
    app = create_app()
    cliente = app.test_client()
    origem = f'http://127.0.0.1:{porta}'
    assert origem not in app.config['ALLOWED_ORIGINS']
    assert cliente.get('/', base_url=origem).status_code == 200
    sessao = cliente.post('/api/sessoes', json={}, base_url=origem, headers={'Origin': origem})
    assert sessao.status_code == 201
    token = sessao.json['token']
    resposta = cliente.get('/api/estado', base_url=origem,
                           headers={'Origin': origem, 'Authorization': f'Bearer {token}'})
    assert resposta.status_code == 200
    assert resposta.headers['Access-Control-Allow-Origin'] == origem
    for externa in ('http://127.0.0.1:9001', 'https://site-nao-permitido.example', 'http://127.0.0.1:5001.example'):
        negada = cliente.post('/api/sessoes', json={}, base_url=origem, headers={'Origin': externa})
        assert negada.status_code == 403
        assert 'Access-Control-Allow-Origin' not in negada.headers
