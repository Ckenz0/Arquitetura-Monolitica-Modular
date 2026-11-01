"""Adaptador HTTP do módulo de visitas."""

from flask import Blueprint, g, jsonify, request
from server.shared.errors import ErroLivraria
from server.transport.json import dados
from .api import VisitasAPI


def registrar_rotas(app, api: VisitasAPI):
    bp = Blueprint('visitas', __name__)

    @bp.post("/api/fila")
    def fila():
        return jsonify(api.entrar_fila(g.cliente_id)), 201


    @bp.post("/api/agendamentos")
    def agendar():
        return jsonify(api.agendar(g.cliente_id, dados("horario_id")["horario_id"])), 201


    app.register_blueprint(bp)
