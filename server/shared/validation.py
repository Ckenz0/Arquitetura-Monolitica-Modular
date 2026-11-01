"""Validação técnica de tipos e datas, independente de Flask."""

from datetime import datetime

from .errors import ErroLivraria

NAO_INFORMADO = object()


def texto_obrigatorio(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        raise ErroLivraria(f'Informe {campo}.')
    return valor.strip()


def inteiro_nao_negativo(valor, campo):
    if type(valor) is not int or valor < 0:
        raise ErroLivraria(f'{campo} deve ser um inteiro não negativo.')
    return valor


def data_iso(valor, agora, futuro=False):
    try:
        data = datetime.fromisoformat(texto_obrigatorio(valor, 'uma data ISO válida'))
        if data.tzinfo is None:
            data = data.astimezone()
    except (ValueError, TypeError, OSError, OverflowError):
        raise ErroLivraria('Informe uma data e hora válidas.') from None
    if futuro and data <= agora():
        raise ErroLivraria('A data deve estar no futuro.')
    return data
