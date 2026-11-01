"""Aplicação real com frontend e API no mesmo servidor HTTP."""

from pathlib import Path
from threading import Thread
from types import SimpleNamespace
import os

import pytest
from werkzeug.serving import make_server

from server.app import create_app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def servidores():
    app = create_app(config={'SECRET_KEY': 'ambiente-de-interface-chave-estavel'})
    servidor = make_server('127.0.0.1', 0, app, threaded=True)
    origem = f'http://127.0.0.1:{servidor.server_port}'
    thread = Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    try:
        yield SimpleNamespace(app=app, api=servidor, api_url=origem, cliente_url=origem)
    finally:
        servidor.shutdown()
        servidor.server_close()
        thread.join(timeout=5)


@pytest.fixture
def browser():
    playwright = pytest.importorskip('playwright.sync_api')
    executavel = os.environ.get('PLAYWRIGHT_BROWSER_EXECUTABLE') or next((p for p in (
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
        'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    ) if Path(p).is_file()), None)
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executavel, headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={'width': 1366, 'height': 900}, locale='pt-BR')
    page = context.new_page()
    page.set_default_timeout(6000)
    yield page
    context.close()
