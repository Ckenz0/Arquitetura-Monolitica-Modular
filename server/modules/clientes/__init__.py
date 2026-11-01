"""API pública e composição do módulo de clientes."""

from .api import ClientesAPI
from ._service import Clientes


def criar_clientes(contexto) -> ClientesAPI:
    return Clientes(contexto)
