"""API pública e composição do módulo de catalogo."""

from .api import CatalogoAPI
from ._service import Catalogo
from ._domain import filtrar_livros


def criar_catalogo(livros, contexto, clientes) -> CatalogoAPI:
    return Catalogo(livros, contexto, clientes)
