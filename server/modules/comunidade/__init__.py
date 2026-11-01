"""API pública e composição do módulo de comunidade."""

from .api import ComunidadeAPI
from ._service import Comunidade


def criar_comunidade(contexto, clientes) -> ComunidadeAPI:
    return Comunidade(contexto, clientes)
