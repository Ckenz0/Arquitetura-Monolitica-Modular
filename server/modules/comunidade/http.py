"""Adaptador HTTP do módulo de comunidade."""

from flask import Blueprint, g, jsonify, request
from server.shared.errors import ErroLivraria
from server.transport.json import dados
from .api import ComunidadeAPI


def registrar_rotas(app, api: ComunidadeAPI):
    bp = Blueprint('comunidade', __name__)

    @bp.post("/api/eventos/<evento_id>/inscricoes")
    def inscrever(evento_id):
        return jsonify(api.inscrever(g.cliente_id, evento_id)), 201


    @bp.post("/api/clubes/<clube_id>/participar")
    def participar(clube_id):
        return jsonify(api.participar_clube(g.cliente_id, clube_id)), 201


    @bp.post("/api/clubes/<clube_id>/opinioes")
    def opinar(clube_id):
        return jsonify(api.publicar_opiniao(g.cliente_id, clube_id, dados("texto")["texto"])), 201


    app.register_blueprint(bp)
