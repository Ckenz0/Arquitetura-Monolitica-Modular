"""Identificação anônima assinada, sem cookies ou login de usuários."""

from uuid import uuid4

from flask import current_app, request
from itsdangerous import BadData, URLSafeTimedSerializer

from server.shared.errors import ErroLivraria


def assinador():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='entrelinhas-sessao-v1')


def emitir_sessao():
    cliente_id = uuid4().hex
    return cliente_id, {
        'token': assinador().dumps({'cliente_id': cliente_id}),
        'tipo': 'Bearer',
        'expira_em_segundos': current_app.config['SESSION_TOKEN_MAX_AGE'],
    }


def identificar_cliente():
    partes = request.headers.get('Authorization', '').split()
    if len(partes) != 2 or partes[0].lower() != 'bearer':
        raise ErroLivraria('Informe uma sessão anônima válida.', 401)
    try:
        dados = assinador().loads(partes[1], max_age=current_app.config['SESSION_TOKEN_MAX_AGE'])
        cliente_id = dados['cliente_id']
        if not isinstance(cliente_id, str) or len(cliente_id) != 32:
            raise ValueError('Identidade inválida.')
    except (BadData, KeyError, TypeError, ValueError):
        raise ErroLivraria('Sua sessão expirou ou é inválida. Inicie uma nova sessão.', 401) from None
    return cliente_id
