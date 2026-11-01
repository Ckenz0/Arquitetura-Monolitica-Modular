"""CORS, erros e observabilidade da fronteira HTTP, sem dados privados."""

from time import perf_counter
from uuid import uuid4

from flask import g, jsonify, request
from werkzeug.exceptions import HTTPException

from server.shared.errors import ErroLivraria


def registrar_http(app):
    def origem_permitida(origem):
        # A interface do próprio monólito funciona em qualquer porta configurada.
        # A lista explícita continua controlando consumidores de outras origens.
        return origem is not None and (
            origem == request.host_url.rstrip('/') or origem in app.config['ALLOWED_ORIGINS']
        )

    @app.before_request
    def preparar_requisicao():
        g.inicio = perf_counter()
        g.request_id = uuid4().hex
        origem = request.headers.get('Origin')
        if origem and not origem_permitida(origem):
            raise ErroLivraria('Origem não permitida.', 403)
        if request.method == 'OPTIONS' and request.url_rule is not None:
            metodo = request.headers.get('Access-Control-Request-Method', '')
            headers = {h.strip().lower() for h in request.headers.get('Access-Control-Request-Headers', '').split(',') if h.strip()}
            if metodo and metodo not in request.url_rule.methods - {'OPTIONS', 'HEAD'}:
                raise ErroLivraria('Método não permitido.', 405)
            if headers - {'authorization', 'content-type', 'accept'}:
                raise ErroLivraria('Cabeçalho não permitido.', 403)
            return '', 204

    @app.after_request
    def finalizar_requisicao(resposta):
        resposta.headers['Cache-Control'] = 'no-store'
        resposta.headers['X-Content-Type-Options'] = 'nosniff'
        resposta.headers['X-Request-ID'] = g.get('request_id', uuid4().hex)
        resposta.vary.add('Origin')
        origem = request.headers.get('Origin')
        if origem_permitida(origem):
            resposta.headers['Access-Control-Allow-Origin'] = origem
            resposta.headers['Access-Control-Expose-Headers'] = 'X-Request-ID'
            if request.method == 'OPTIONS' and resposta.status_code == 204:
                resposta.headers['Access-Control-Allow-Methods'] = ', '.join(sorted(request.url_rule.methods - {'OPTIONS', 'HEAD'}))
                resposta.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, Accept'
                resposta.headers['Access-Control-Max-Age'] = '600'
        duracao = (perf_counter() - g.get('inicio', perf_counter())) * 1000
        caminho = request.url_rule.rule if request.url_rule else '<rota-desconhecida>'
        app.logger.info('%s %s %s %.1fms request_id=%s', request.method, caminho,
                        resposta.status_code, duracao, resposta.headers['X-Request-ID'])
        return resposta

    @app.errorhandler(ErroLivraria)
    def erro_dominio(erro):
        return jsonify(erro=str(erro)), erro.status

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        mensagens = {400: 'Requisição inválida. Confira o JSON enviado.',
                     404: 'Recurso não encontrado.', 405: 'Método não permitido.',
                     413: 'Requisição muito grande.', 415: 'Envie um objeto JSON.'}
        resposta = erro.get_response()
        resposta.set_data(app.json.dumps({'erro': mensagens.get(erro.code, 'Não foi possível atender à requisição.')}))
        resposta.content_type = 'application/json'
        return resposta

    @app.errorhandler(Exception)
    def erro_inesperado(erro):
        app.logger.error('Erro interno request_id=%s tipo=%s', g.get('request_id'), type(erro).__name__)
        return jsonify(erro='Não foi possível concluir a operação. Tente novamente.'), 500
