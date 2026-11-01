"""Fluxos reais da aplicação modular com frontend e API na mesma origem."""

from datetime import datetime, timedelta
from pathlib import Path
import re

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.interface
CAPTURAS = Path(__file__).resolve().parents[1] / 'test-results/screenshots'


def abrir(page, servidores):
    page.goto(servidores.cliente_url)
    expect(page.locator('.book-card')).to_have_count(5)


def detalhes(page):
    page.locator('.book-card [data-action="detalhes"][data-id="1984"]').click()
    expect(page.locator('#avaliacao-form')).to_be_visible()


@pytest.mark.parametrize('width,height', [(1366, 900), (390, 844)])
def test_catalogo_avaliacao_rascunho_seguro_e_isolamento(page, browser, servidores, width, height):
    page.set_viewport_size({'width': width, 'height': height})
    erros = []
    page.on('pageerror', lambda erro: erros.append(str(erro)))
    abrir(page, servidores)
    page.locator('#busca').fill('ORWELL')
    expect(page.locator('.book-card')).to_have_count(2)
    page.locator('#busca').fill('')
    page.locator('#genero').select_option('Fantasia')
    page.locator('#lancamentos').check()
    expect(page.locator('.book-card')).to_have_count(1)
    page.locator('#lancamentos').uncheck()
    page.locator('#genero').select_option('')
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(CAPTURAS / f'catalogo-{width}.png'), full_page=True)
    detalhes(page)
    page.get_by_label('Sua nota').select_option('5')
    comentario = '<script>window.injetado=true</script> Excelente leitura.'
    page.get_by_label('Seu comentário').fill(comentario)
    page.route('**/api/livros/1984/avaliacoes', lambda rota: rota.abort('connectionfailed'))
    page.get_by_role('button', name='Publicar avaliação', exact=True).click()
    expect(page.locator('#avaliacao-erro')).to_be_visible()
    expect(page.get_by_label('Seu comentário')).to_have_value(comentario)
    expect(page.get_by_label('Sua nota')).to_have_value('5')
    page.unroute('**/api/livros/1984/avaliacoes')
    page.get_by_role('button', name='Publicar avaliação', exact=True).click()
    expect(page.locator('#avaliacao-confirmacao')).to_be_visible()
    expect(page.locator('#book-details .opinion').last).to_contain_text(comentario)
    assert page.evaluate('window.injetado') is None
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert page.locator('#book-dialog').evaluate('el => el.scrollWidth <= el.clientWidth')
    page.screenshot(path=str(CAPTURAS / f'avaliacao-{width}.png'), full_page=True)
    page.reload()
    page.locator('.book-card [data-action="detalhes"][data-id="1984"]').click()
    expect(page.locator('#avaliacao-confirmacao')).to_be_visible()
    outro = browser.new_context()
    try:
        outra = outro.new_page()
        abrir(outra, servidores)
        detalhes(outra)
        expect(outra.locator('#book-details .opinion').last).to_contain_text(comentario)
        assert outra.evaluate('sessionStorage.getItem("entrelinhas.sessao")') != page.evaluate('sessionStorage.getItem("entrelinhas.sessao")')
    finally:
        outro.close()
    assert erros == []


def test_reserva_cancelamento_visita_comunidade_e_preferencias(page, servidores):
    abrir(page, servidores)
    page.locator('.book-card [data-action="reservar"][data-id="hobbit"]').click()
    page.locator('#reserve-deadline').fill((datetime.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'))
    page.locator('#reserve-gift').check()
    page.locator('#reserve-form button[type="submit"]').click()
    expect(page.locator('#reservas')).to_contain_text('Presente com embrulho especial')
    page.locator('#reservas [data-action="prazo"]').click()
    page.locator('#new-deadline').fill((datetime.now() + timedelta(days=4)).strftime('%Y-%m-%dT%H:%M'))
    page.locator('#deadline-form button[type="submit"]').click()
    expect(page.locator('#deadline-dialog')).not_to_be_visible()
    page.locator('#reservas [data-action="cancelar"]').click()
    expect(page.locator('#reservas .status')).to_have_text('cancelada')
    page.locator('#fila-button').click()
    expect(page.locator('#fila-posicao')).to_contain_text('posição na fila: 1')
    page.locator('#agendamento-horario').select_option(index=1)
    page.locator('#agendamento-form button[type="submit"]').click()
    expect(page.locator('#agendamentos')).to_contain_text('Agendado para')
    page.locator('nav [data-tab="comunidade"]').click()
    page.locator('#eventos [data-action="inscrever"]').first.click()
    expect(page.locator('#eventos button').first).to_have_text('Inscrição confirmada ✓')
    page.locator('#clubes [data-action="clube"]').click()
    page.locator('.opiniao-form textarea').fill('Gostei da leitura compartilhada.')
    page.locator('.opiniao-form button[type="submit"]').click()
    expect(page.locator('#clubes .opinion')).to_contain_text('leitura compartilhada')
    page.locator('nav [data-tab="perfil"]').click()
    page.locator('#preferencias-form input[name="generos"][value="Fantasia"]').check()
    page.locator('#preferencias-form button[type="submit"]').click()
    expect(page.locator('#toast')).to_have_text('Suas preferências foram salvas.')
    page.reload()
    page.locator('nav [data-tab="perfil"]').click()
    expect(page.locator('#preferencias-form input[name="generos"][value="Fantasia"]')).to_be_checked()


def test_bootstrap_paralelo_usa_uma_identidade_e_sem_cookie(page, servidores):
    sessoes, chamadas = [], []
    page.on('request', lambda req: sessoes.append(req) if req.url.endswith('/api/sessoes') and req.method == 'POST' else None)
    page.on('request', lambda req: chamadas.append(req) if '/api/estado' in req.url and req.method == 'GET' else None)
    # Carrega o transporte real antes de qualquer chamada do app para exercitar
    # o bootstrap concorrente sem token, e não apenas chamadas já identificadas.
    page.route('**/js/app.js', lambda rota: rota.fulfill(content_type='application/javascript', body=''))
    page.goto(servidores.cliente_url)
    valores = page.evaluate('async () => Promise.all(Array.from({length: 4}, () => livrariaApi("/api/estado").then(e => e.cliente.id)))')
    assert len(set(valores)) == 1
    assert len(sessoes) == 1
    assert all(req.headers.get('authorization', '').startswith('Bearer ') for req in chamadas)
    assert page.context.cookies() == []


def test_api_desligada_exibe_erro_e_recuperacao(page, servidores):
    abrir(page, servidores)
    servidores.api.shutdown()
    servidores.api.server_close()
    page.evaluate("void atualizar()")
    expect(page.locator('#connection-status')).to_be_visible()
    expect(page.locator('#connection-status')).to_contain_text('conectar')
    expect(page.get_by_role('button', name='Tentar novamente')).to_be_visible()


def test_link_de_recuperacao_preserva_contraste_no_hover(page, servidores):
    abrir(page, servidores)
    link = page.locator('.store-note .btn.link')
    link.hover()
    estilos = link.evaluate('el => ({color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundColor})')
    # Contraste WCAG calculado a partir dos estilos efetivamente renderizados.
    def luminancia(css):
        canais = [int(v) / 255 for v in re.findall(r'\d+', css)[:3]]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in canais]
        return sum(c * peso for c, peso in zip(linear, (0.2126, 0.7152, 0.0722)))
    claro, escuro = sorted([luminancia(estilos['color']), luminancia(estilos['background'])], reverse=True)
    assert (claro + 0.05) / (escuro + 0.05) >= 4.5


def test_sessao_expirada_preserva_rascunho_e_nao_reenvia_mutacao(page, servidores):
    abrir(page, servidores)
    detalhes(page)
    page.get_by_label('Sua nota').select_option('4')
    page.get_by_label('Seu comentário').fill('Meu rascunho deve continuar aqui.')
    servidores.app.config['SESSION_TOKEN_MAX_AGE'] = -1
    posts = []
    page.on('request', lambda req: posts.append(req) if req.method == 'POST' and req.url.endswith('/avaliacoes') else None)
    page.get_by_role('button', name='Publicar avaliação', exact=True).click()
    expect(page.locator('#avaliacao-erro')).to_contain_text('sessão')
    expect(page.get_by_label('Seu comentário')).to_have_value('Meu rascunho deve continuar aqui.')
    assert len(posts) == 1
    expect(page.locator('[data-action="nova-sessao"]')).to_be_visible()
    servidores.app.config['SESSION_TOKEN_MAX_AGE'] = 86400
    # A renovação fica em um aviso dentro do modal aberto; não fecha o rascunho.
    page.locator('[data-action="nova-sessao"]').click()
    expect(page.get_by_label('Seu comentário')).to_have_value('Meu rascunho deve continuar aqui.')
    assert len(posts) == 1
    page.get_by_role('button', name='Publicar avaliação', exact=True).click()
    expect(page.locator('#avaliacao-confirmacao')).to_be_visible()


def test_resposta_html_e_timeout_tem_mensagem_legivel_sem_repetir_post(page, servidores):
    abrir(page, servidores)
    page.route('**/api/desejos', lambda rota: rota.fulfill(status=502, content_type='text/html', body='<html>proxy indisponível</html>', headers={'Access-Control-Allow-Origin': servidores.cliente_url}))
    erro = page.evaluate('async () => {try {await livrariaApi("/api/desejos", "POST", {livro_id:"1984"});} catch (e) {return e.message;}}')
    assert 'resposta' in erro.lower() and '<html>' not in erro
    page.unroute('**/api/desejos')
    page.evaluate('LIVRARIA_CONFIG.TIMEOUT_MS = 50')
    pendentes = []
    page.route('**/api/desejos', lambda rota: pendentes.append(rota))
    erro = page.evaluate('async () => {try {await livrariaApi("/api/desejos", "POST", {livro_id:"1984"});} catch (e) {return e.message;}}')
    assert 'demorou' in erro.lower()
    assert len(pendentes) == 1
    assert all(servidores.app.extensions['livraria'].modulos.catalogo.desejos(c['id']) == [] for c in servidores.app.extensions['livraria'].modulos.clientes.listar_clientes())


def test_atualizacao_pendente_depois_de_mutacao_nao_se_perde(page, servidores):
    abrir(page, servidores)
    antigo = page.evaluate('async () => livrariaApi("/api/estado")')
    capturadas = []
    def capturar(rota):
        if not capturadas:
            capturadas.append(rota)
        else:
            rota.continue_()
    page.route('**/api/estado', capturar)
    with page.expect_request('**/api/estado'):
        page.evaluate('void atualizar()')
    page.evaluate('async () => livrariaApi("/api/desejos", "POST", {livro_id:"hobbit"})')
    page.evaluate('window.concluido=false; void atualizar().then(() => {window.concluido=true})')
    capturadas[0].fulfill(json=antigo, headers={'Access-Control-Allow-Origin': servidores.cliente_url})
    page.wait_for_function('window.concluido')
    expect(page.locator('.book-card [data-action="desejo"][data-id="hobbit"]')).to_have_attribute('aria-pressed', 'true')


def test_renovar_sessao_preserva_opiniao_ao_reentrar_no_clube(page, servidores):
    abrir(page, servidores)
    page.locator('nav [data-tab="comunidade"]').click()
    page.locator('#clubes [data-action="clube"]').click()
    campo = page.locator('.opiniao-form textarea')
    campo.fill('Quero terminar esta opinião depois de renovar.')
    servidores.app.config['SESSION_TOKEN_MAX_AGE'] = -1
    page.locator('.opiniao-form button[type="submit"]').click()
    expect(page.locator('[data-action="nova-sessao"]')).to_be_visible()
    servidores.app.config['SESSION_TOKEN_MAX_AGE'] = 86400
    page.locator('[data-action="nova-sessao"]').click()
    page.locator('#clubes [data-action="clube"]').click()
    expect(campo).to_have_value('Quero terminar esta opinião depois de renovar.')
    page.locator('.opiniao-form button[type="submit"]').click()
    expect(page.locator('#clubes .opinion')).to_contain_text('terminar esta opinião')
    expect(campo).to_have_value('')
    # Publicar com sucesso consome o rascunho; ele não deve reaparecer.
    page.evaluate('async () => {await novaSessaoLivraria(); await atualizar();}')
    page.locator('#clubes [data-action="clube"]').click()
    expect(campo).to_have_value('')


def test_renovar_sessao_preserva_preferencias_nao_salvas_sem_envio_automatico(page, servidores):
    abrir(page, servidores)
    page.locator('nav [data-tab="perfil"]').click()
    genero = page.locator('#preferencias-form input[name="generos"][value="Fantasia"]')
    estoque = page.locator('#preferencias-form input[name="temas"][value="estoque"]')
    genero.check()
    estoque.uncheck()
    servidores.app.config['SESSION_TOKEN_MAX_AGE'] = -1
    page.locator('#preferencias-form button[type="submit"]').click()
    expect(page.locator('[data-action="nova-sessao"]')).to_be_visible()
    servidores.app.config['SESSION_TOKEN_MAX_AGE'] = 86400
    page.locator('[data-action="nova-sessao"]').click()
    expect(page.locator('#toast')).to_contain_text('Nova sessão iniciada')
    expect(genero).to_be_checked()
    expect(estoque).not_to_be_checked()
    assert page.evaluate('async () => (await livrariaApi("/api/estado")).cliente.generos') == []
    page.locator('#preferencias-form button[type="submit"]').click()
    expect(page.locator('#toast')).to_have_text('Suas preferências foram salvas.')
    assert page.evaluate('async () => (await livrariaApi("/api/estado")).cliente.generos') == ['Fantasia']


def test_401_de_requisicao_antiga_nao_invalida_nova_sessao(page, servidores):
    abrir(page, servidores)
    antigas = []
    page.route('**/api/estado', lambda rota: antigas.append(rota))
    with page.expect_request('**/api/estado'):
        page.evaluate('window.resultadoAntigo=livrariaApi("/api/estado").catch(e => e.message); void 0;')
    token_antigo = page.evaluate('sessionStorage.getItem("entrelinhas.sessao")')
    page.evaluate('async () => {await novaSessaoLivraria(); return livrariaApi("/api/livros");}')
    assert page.evaluate('sessionStorage.getItem("entrelinhas.sessao")') != token_antigo
    antigas[0].fulfill(status=401, json={'erro': 'Sessão anterior expirada.'}, headers={'Access-Control-Allow-Origin': servidores.cliente_url})
    resultado_antigo = page.evaluate('async () => window.resultadoAntigo')
    assert isinstance(resultado_antigo, str)
    atual = page.evaluate('async () => {try {return await livrariaApi("/api/livros");} catch (e) {return e.message;}}')
    assert isinstance(atual, list) and len(atual) == 5
    expect(page.locator('[data-action="nova-sessao"]')).to_have_count(0)
