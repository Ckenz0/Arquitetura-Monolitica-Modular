"""Estado privado das reservas."""

from server.shared.errors import ErroLivraria


class RepositorioReservas:
    def __init__(self):
        self.reservas = {}

    def obter(self, reserva_id, cliente_id=None):
        try:
            reserva = self.reservas.get(reserva_id)
        except TypeError:
            reserva = None
        if reserva is None or (cliente_id is not None and reserva['cliente_id'] != cliente_id):
            raise ErroLivraria('Reserva não encontrada.', 404)
        return reserva
