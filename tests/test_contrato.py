"""O contrato versionado deve descrever as respostas HTTP reais."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate
import yaml

from server.app import create_app
from tests.helpers import cliente_identificado

SPEC = yaml.safe_load((Path(__file__).resolve().parents[1] / 'server/openapi.yaml').read_text(encoding='utf-8'))


def verificar(resposta, caminho, metodo):
    contrato = SPEC['paths'][caminho][metodo]['responses'][str(resposta.status_code)]
    if '$ref' in contrato:
        contrato = SPEC['components']['responses'][contrato['$ref'].split('/')[-1]]
    schema = contrato['content']['application/json']['schema']
    Draft202012Validator({**schema, 'components': SPEC['components']}, format_checker=FormatChecker()).validate(resposta.json)


def test_contrato_valido_e_todas_as_rotas_estao_documentadas():
    validate(SPEC)
    registradas = {
        (re.sub(r'<([^>]+)>', r'{\1}', regra.rule), metodo.lower())
        for regra in create_app().url_map.iter_rules() if regra.rule.startswith('/api')
        for metodo in regra.methods - {'HEAD', 'OPTIONS'}
    }
    documentadas = {(caminho, metodo) for caminho, operacoes in SPEC['paths'].items() for metodo in operacoes}
    assert documentadas == registradas


def test_contrato_das_respostas_de_todos_os_fluxos_reais():
    app = create_app()
    cliente = app.test_client()
    verificar(cliente.get('/api'), '/api', 'get')
    verificar(cliente.get('/api/health'), '/api/health', 'get')
    verificar(cliente.post('/api/sessoes', json={}), '/api/sessoes', 'post')
    verificar(cliente.get('/api/estado'), '/api/estado', 'get')  # 401
    cliente = cliente_identificado(app)
    for url, caminho in [('/api/estado', '/api/estado'), ('/api/livros?q=orwell', '/api/livros'),
                         ('/api/livros/1984', '/api/livros/{livro_id}'),
                         ('/api/codigo/9788535914849', '/api/codigo/{codigo}')]:
        verificar(cliente.get(url), caminho, 'get')
    resposta = cliente.post('/api/livros/1984/avaliacoes', json={'nota': 5, 'texto': 'Uma boa leitura.'})
    verificar(resposta, '/api/livros/{livro_id}/avaliacoes', 'post')
    verificar(cliente.post('/api/livros/1984/avaliacoes', json={'nota': 5, 'texto': 'Repetida.'}), '/api/livros/{livro_id}/avaliacoes', 'post')
    verificar(cliente.post('/api/livros/1984/avaliacoes', json={'nota': 0, 'texto': 'Inválida.'}), '/api/livros/{livro_id}/avaliacoes', 'post')
    prazo = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    reserva = cliente.post('/api/reservas', json={'livro_id': '1984', 'prazo': prazo})
    verificar(reserva, '/api/reservas', 'post')
    url = f'/api/reservas/{reserva.json["id"]}'
    verificar(cliente.patch(url, json={'prazo': prazo}), '/api/reservas/{reserva_id}', 'patch')
    verificar(cliente.post(url + '/cancelar'), '/api/reservas/{reserva_id}/cancelar', 'post')
    estado = cliente.get('/api/estado').json
    horario = estado['horarios'][0]['id']
    evento = estado['eventos'][0]['id']
    clube = estado['clubes'][0]['id']
    for url, caminho, corpo in [
        ('/api/avisos-estoque', '/api/avisos-estoque', {'livro_id': 'esgotado'}),
        ('/api/fila', '/api/fila', {}),
        ('/api/agendamentos', '/api/agendamentos', {'horario_id': horario}),
        (f'/api/eventos/{evento}/inscricoes', '/api/eventos/{evento_id}/inscricoes', {}),
        (f'/api/clubes/{clube}/participar', '/api/clubes/{clube_id}/participar', {}),
        (f'/api/clubes/{clube}/opinioes', '/api/clubes/{clube_id}/opinioes', {'texto': 'Leitura compartilhada.'}),
        ('/api/desejos', '/api/desejos', {'livro_id': 'hobbit'}),
    ]:
        verificar(cliente.post(url, json=corpo), caminho, 'post')
    verificar(cliente.patch('/api/preferencias', json={'generos': ['Fantasia'], 'temas_notificacao': []}), '/api/preferencias', 'patch')
    verificar(cliente.get('/api/estado'), '/api/estado', 'get')
    verificar(cliente.get('/api/livros/inexistente'), '/api/livros/{livro_id}', 'get')


def test_exemplos_de_requisicao_sao_aceitos_pelo_contrato():
    exemplos = [('/api/sessoes', 'post', {}), ('/api/reservas', 'post', {
        'livro_id': '1984', 'prazo': '2099-01-01T12:00:00+00:00', 'embrulho': True,
    }), ('/api/livros/{livro_id}/avaliacoes', 'post', {'nota': 5, 'texto': 'Gostei desta leitura.'})]
    for caminho, metodo, exemplo in exemplos:
        schema = SPEC['paths'][caminho][metodo]['requestBody']['content']['application/json']['schema']
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(exemplo)
