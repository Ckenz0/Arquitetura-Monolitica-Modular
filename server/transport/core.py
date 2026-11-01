"""Sessão anônima e projeção agregada, sem acesso a repositórios privados."""

from datetime import timedelta

from flask import Blueprint, g, jsonify, request

from server.shared.errors import ErroLivraria
from .identity import emitir_sessao, identificar_cliente
from .json import dados


def registrar_core(app, loja, *, demonstracao):
    bp = Blueprint('core', __name__)

    @app.before_request
    def preparar_api():
        if not request.endpoint or not request.path.startswith('/api'):
            return
        if request.endpoint not in {'core.info', 'core.health', 'core.sessoes'}:
            g.cliente_id = identificar_cliente()
        if request.method in {'POST', 'PATCH'} and request.get_data(cache=True):
            dados()

    @bp.get('/api')
    def info():
        return jsonify(servico='Entrelinhas API', health='/api/health')

    @bp.get('/api/health')
    def health():
        return jsonify(status='ok')

    @bp.post('/api/sessoes')
    def sessoes():
        if request.get_data(cache=True) and dados():
            raise ErroLivraria('A sessão não aceita campos de identificação.')
        cliente_id, sessao = emitir_sessao()
        if demonstracao:
            agora = loja.agora()
            loja.registrar_compra(cliente_id, '1984', 20,
                                  expira_em=(agora + timedelta(days=3)).isoformat(),
                                  avisar_em=agora.isoformat())
            loja.conceder_cupom(cliente_id, 'BOASLEITURAS',
                               'Cupom ilustrativo: consulte as condições no caixa.')
        return jsonify(sessao), 201

    @bp.get('/api/estado')
    def estado():
        return jsonify(loja.estado(g.cliente_id))

    app.register_blueprint(bp)
