"""API pública e composição do módulo de reservas."""

from .api import ReservasAPI
from ._service import Reservas


def criar_reservas(contexto, catalogo, clientes) -> ReservasAPI:
    return Reservas(contexto, catalogo, clientes)
