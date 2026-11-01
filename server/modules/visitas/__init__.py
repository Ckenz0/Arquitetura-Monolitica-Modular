"""API pública e composição do módulo de visitas."""

from .api import VisitasAPI
from ._service import Visitas


def criar_visitas(contexto, clientes) -> VisitasAPI:
    return Visitas(contexto, clientes)
