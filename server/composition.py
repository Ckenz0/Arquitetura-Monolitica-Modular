"""Único ponto que conhece as factories de todos os módulos de negócio."""

from dataclasses import dataclass

from server.shared.context import Contexto
from server.modules.clientes import ClientesAPI, criar_clientes
from server.modules.catalogo import CatalogoAPI, criar_catalogo
from server.modules.reservas import ReservasAPI, criar_reservas
from server.modules.visitas import VisitasAPI, criar_visitas
from server.modules.fidelidade import FidelidadeAPI, criar_fidelidade
from server.modules.comunidade import ComunidadeAPI, criar_comunidade


@dataclass(frozen=True)
class Modulos:
    contexto: Contexto
    clientes: ClientesAPI
    catalogo: CatalogoAPI
    reservas: ReservasAPI
    visitas: VisitasAPI
    fidelidade: FidelidadeAPI
    comunidade: ComunidadeAPI


def criar_modulos(livros=None, agora=None):
    contexto = Contexto(agora)
    clientes = criar_clientes(contexto)
    catalogo = criar_catalogo(livros, contexto, clientes)
    reservas = criar_reservas(contexto, catalogo, clientes)
    visitas = criar_visitas(contexto, clientes)
    fidelidade = criar_fidelidade(contexto, catalogo, clientes)
    comunidade = criar_comunidade(contexto, clientes)
    return Modulos(contexto, clientes, catalogo, reservas, visitas, fidelidade, comunidade)
