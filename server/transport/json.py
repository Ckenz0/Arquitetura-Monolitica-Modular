"""Validação de formato das requisições; regras de negócio ficam nos módulos."""

from flask import request

from server.shared.errors import ErroLivraria


def dados(*obrigatorios):
    if not request.is_json:
        raise ErroLivraria('Envie um objeto JSON.')
    corpo = request.get_json()
    if not isinstance(corpo, dict):
        raise ErroLivraria('Envie um objeto JSON.')
    for campo in obrigatorios:
        if not isinstance(corpo.get(campo), str) or not corpo[campo].strip():
            raise ErroLivraria(f'Informe {campo}.')
    return corpo
