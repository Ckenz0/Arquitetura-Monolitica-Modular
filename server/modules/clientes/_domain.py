"""Política de preferências dos leitores."""

from server.shared.errors import ErroLivraria
from server.shared.validation import NAO_INFORMADO

TEMAS = {'estoque', 'reservas', 'fidelidade', 'eventos'}


def validar_preferencias(generos, temas_notificacao):
    for valor, campo in [(generos, 'Gêneros'), (temas_notificacao, 'Temas')]:
        if valor is NAO_INFORMADO or (campo == 'Temas' and valor is None):
            continue
        if not isinstance(valor, list) or any(not isinstance(v, str) or not v.strip() for v in valor):
            raise ErroLivraria(f'{campo} deve ser uma lista de textos.')
    if temas_notificacao is not NAO_INFORMADO and temas_notificacao is not None:
        if not set(temas_notificacao).issubset(TEMAS):
            raise ErroLivraria('Tema de notificação inválido.')
