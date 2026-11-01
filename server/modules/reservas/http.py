"""Adaptador HTTP do módulo de reservas."""

from flask import Blueprint, g, jsonify, request
from server.shared.errors import ErroLivraria
from server.transport.json import dados
from .api import ReservasAPI


def registrar_rotas(app, api: ReservasAPI):
    bp = Blueprint('reservas', __name__)

    @bp.post("/api/reservas")
    def reservar():
        corpo = dados("livro_id", "prazo")
        return jsonify(api.reservar(g.cliente_id, corpo["livro_id"], corpo["prazo"],
                                    corpo.get("embrulho", False))), 201


    @bp.patch("/api/reservas/<reserva_id>")
    def alterar_reserva(reserva_id):
        return jsonify(api.alterar_prazo(g.cliente_id, reserva_id, dados("prazo")["prazo"]))


    @bp.post("/api/reservas/<reserva_id>/cancelar")
    def cancelar(reserva_id):
        return jsonify(api.cancelar_reserva(g.cliente_id, reserva_id))


    app.register_blueprint(bp)
