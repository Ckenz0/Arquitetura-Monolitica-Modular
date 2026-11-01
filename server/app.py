"""Aplicação única: frontend e todos os módulos de negócio no mesmo processo."""

import logging
import os
from pathlib import Path

from flask import Flask, send_from_directory

from server.config import configuracao
from server.demonstracao import criar_demonstracao
from server.transport.http import registrar_http
from server.transport.core import registrar_core
from server.modules.catalogo.http import registrar_rotas as registrar_catalogo
from server.modules.clientes.http import registrar_rotas as registrar_clientes
from server.modules.reservas.http import registrar_rotas as registrar_reservas
from server.modules.visitas.http import registrar_rotas as registrar_visitas
from server.modules.comunidade.http import registrar_rotas as registrar_comunidade


def create_app(livraria=None, config=None):
    web = Path(__file__).resolve().parents[1] / 'web'
    app = Flask(__name__, static_folder=str(web), static_url_path='/static', template_folder=None)
    app.config.update(configuracao(config))
    app.logger.setLevel(logging.INFO)
    app.json.ensure_ascii = False
    loja = criar_demonstracao() if livraria is None else livraria
    app.extensions['livraria'] = loja
    app.extensions['modulos'] = loja.modulos
    registrar_http(app)
    registrar_core(app, loja, demonstracao=livraria is None)
    registrar_catalogo(app, loja.modulos.catalogo)
    registrar_clientes(app, loja.modulos.clientes)
    registrar_reservas(app, loja.modulos.reservas)
    registrar_visitas(app, loja.modulos.visitas)
    registrar_comunidade(app, loja.modulos.comunidade)

    @app.get('/')
    def index():
        return send_from_directory(web, 'index.html')

    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    app = create_app()
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '5000')), debug=False)
