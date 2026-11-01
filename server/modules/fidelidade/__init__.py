"""API pública e composição do módulo de fidelidade."""

from .api import FidelidadeAPI
from ._service import Fidelidade


def criar_fidelidade(contexto, catalogo, clientes) -> FidelidadeAPI:
    return Fidelidade(contexto, catalogo, clientes)
