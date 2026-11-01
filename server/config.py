"""Configuração externa; segredos pertencem somente ao servidor."""

import os
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


def configuracao(overrides=None):
    load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)
    producao = os.environ.get('APP_ENV', 'development') == 'production'
    chave = os.environ.get('SECRET_KEY', '')
    origens = os.environ.get('ALLOWED_ORIGINS', '')
    config = {
        'SECRET_KEY': chave or (None if producao else secrets.token_hex(32)),
        'ALLOWED_ORIGINS': origens or (() if producao else (
            'http://127.0.0.1:5000', 'http://localhost:5000',
            'http://127.0.0.1:8080', 'http://localhost:8080',
        )),
        'SESSION_TOKEN_MAX_AGE': 86400,
        'MAX_CONTENT_LENGTH': 1024 * 1024,
    }
    config.update(overrides or {})
    if producao and (not isinstance(config['SECRET_KEY'], str) or len(config['SECRET_KEY']) < 32):
        raise ValueError('Produção exige SECRET_KEY estável com pelo menos 32 caracteres.')
    origens = config['ALLOWED_ORIGINS']
    if isinstance(origens, str):
        origens = [origem.strip() for origem in origens.split(',') if origem.strip()]
    if not origens:
        raise ValueError('Informe ALLOWED_ORIGINS explicitamente.')
    for origem in origens:
        url = urlsplit(origem)
        if (url.scheme not in {'http', 'https'} or not url.netloc or url.path
                or url.query or url.fragment or url.username or url.password):
            raise ValueError('ALLOWED_ORIGINS aceita origens exatas, sem caminho ou curingas.')
        if '*' in origem:
            raise ValueError('Não use curingas em ALLOWED_ORIGINS.')
    config['ALLOWED_ORIGINS'] = tuple(origens)
    return config
