"""Reservas coordenadas com o catálogo por contrato público."""

from copy import deepcopy
from uuid import uuid4

from server.modules.catalogo.api import CatalogoAPI
from server.modules.clientes.api import ClientesAPI
from server.shared.context import atomico
from server.shared.errors import ErroLivraria
from server.shared.validation import data_iso, texto_obrigatorio
from ._repository import RepositorioReservas


class Reservas:
    def __init__(self, contexto, catalogo: CatalogoAPI, clientes: ClientesAPI):
        self._contexto, self._catalogo, self._clientes = contexto, catalogo, clientes
        self._repo = RepositorioReservas()

    @atomico
    def reservar(self, cliente_id, livro_id, prazo, embrulho=False):
        # Validar cliente e prazo antes de solicitar a baixa ao módulo dono.
        data = data_iso(prazo, self._contexto.agora, futuro=True)
        texto_obrigatorio(cliente_id, 'o identificador do cliente')
        livro = self._catalogo.reservar_exemplar(livro_id, embrulho)
        self._clientes.obter_perfil(cliente_id)
        reserva = {'id': uuid4().hex, 'cliente_id': cliente_id, 'livro_id': livro_id,
                   'titulo': livro['titulo'], 'prazo': data.isoformat(),
                   'embrulho': embrulho, 'status': 'pendente'}
        self._repo.reservas[reserva['id']] = reserva
        return deepcopy(reserva)

    @atomico
    def reservas(self, cliente_id):
        return [deepcopy(r) for r in self._repo.reservas.values() if r['cliente_id'] == cliente_id]

    @atomico
    def alterar_prazo(self, cliente_id, reserva_id, prazo):
        reserva = self._repo.obter(reserva_id, cliente_id)
        data = data_iso(prazo, self._contexto.agora, futuro=True)
        if reserva['status'] == 'cancelada':
            raise ErroLivraria('A reserva já foi cancelada.', 409)
        reserva['prazo'] = data.isoformat()
        return deepcopy(reserva)

    @atomico
    def cancelar_reserva(self, cliente_id, reserva_id):
        reserva = self._repo.obter(reserva_id, cliente_id)
        if reserva['status'] != 'cancelada':
            self._catalogo.devolver_exemplar(reserva['livro_id'])
            reserva['status'] = 'cancelada'
        return deepcopy(reserva)

    @atomico
    def marcar_pronta(self, reserva_id):
        reserva = self._repo.obter(reserva_id)
        if reserva['status'] == 'cancelada':
            raise ErroLivraria('A reserva já foi cancelada.', 409)
        if reserva['status'] != 'pronta':
            reserva['status'] = 'pronta'
            self._clientes.notificar(reserva['cliente_id'], 'reservas',
                                    f'Sua reserva de {reserva["titulo"]} está pronta para retirada.')
        return deepcopy(reserva)
