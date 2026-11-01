"""Adaptador HTTP do módulo de catalogo."""

from flask import Blueprint, g, jsonify, request
from server.shared.errors import ErroLivraria
from server.transport.json import dados
from .api import CatalogoAPI


def registrar_rotas(app, api: CatalogoAPI):
    bp = Blueprint('catalogo', __name__)

    @bp.get("/api/livros")
    def livros():
        return jsonify(api.buscar(request.args.get("q", ""), request.args.get("genero", ""),
                                  request.args.get("lancamentos") == "1"))


    @bp.get("/api/livros/<livro_id>")
    def livro(livro_id):
        return jsonify(api.livro(livro_id, g.cliente_id))


    @bp.post("/api/livros/<livro_id>/avaliacoes")
    def avaliar(livro_id):
        corpo = dados("texto")
        if set(corpo) - {"nota", "texto"}:
            raise ErroLivraria("Envie apenas nota e texto da avaliação.")
        return jsonify(api.publicar_avaliacao(
            g.cliente_id, livro_id, corpo.get("nota"), corpo["texto"],
        )), 201


    @bp.get("/api/codigo/<codigo>")
    def codigo(codigo):
        return jsonify(api.por_codigo(codigo))


    @bp.post("/api/avisos-estoque")
    def avisos_estoque():
        corpo = dados("livro_id")
        return jsonify(api.acompanhar_estoque(g.cliente_id, corpo["livro_id"])), 201


    @bp.post("/api/desejos")
    def desejo():
        return jsonify(api.adicionar_desejo(g.cliente_id, dados("livro_id")["livro_id"])), 201


    app.register_blueprint(bp)
