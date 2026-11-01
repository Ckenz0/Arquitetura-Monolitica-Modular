"""Adaptador HTTP do módulo de clientes."""

from flask import Blueprint, g, jsonify, request
from server.shared.errors import ErroLivraria
from server.transport.json import dados
from .api import ClientesAPI


def registrar_rotas(app, api: ClientesAPI):
    bp = Blueprint('clientes', __name__)

    @bp.patch("/api/preferencias")
    def preferencias():
        corpo = dados()
        if not corpo or set(corpo) - {"generos", "temas_notificacao"}:
            raise ErroLivraria("Informe gêneros e/ou temas de notificação.")
        return jsonify(api.preferencias(g.cliente_id, **corpo))


    app.register_blueprint(bp)
