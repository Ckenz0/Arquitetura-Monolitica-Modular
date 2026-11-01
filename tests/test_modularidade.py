"""Limites de negócio, contratos públicos e coordenação entre módulos reais."""

import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest

AGORA = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
PRAZO = '2026-11-03T12:00:00+00:00'


def loja():
    from server.livraria import Livraria
    return Livraria([{'id': '1984', 'titulo': '1984', 'autor': 'George Orwell',
                     'genero': 'Distopia', 'estoque': 1}], agora=lambda: AGORA)


def test_seis_modulos_compostos_com_contexto_da_instancia():
    sistema = loja()
    assert not hasattr(sistema, 'dados')
    assert not hasattr(sistema, 'repositorio')
    assert all(getattr(sistema.modulos, nome) is not None for nome in (
        'clientes', 'catalogo', 'reservas', 'visitas', 'fidelidade', 'comunidade',
    ))
    outra = loja()
    sistema.adicionar_desejo('ana', '1984')
    assert outra.desejos('ana') == []


def test_reserva_coordena_estoque_e_cancelamento_por_api_publica():
    sistema = loja()
    reserva = sistema.modulos.reservas.reservar('ana', '1984', PRAZO)
    assert sistema.modulos.catalogo.livro('1984')['estoque'] == 0
    sistema.modulos.reservas.cancelar_reserva('ana', reserva['id'])
    sistema.modulos.reservas.cancelar_reserva('ana', reserva['id'])
    assert sistema.modulos.catalogo.livro('1984')['estoque'] == 1
    assert sistema.modulos.reservas.reservas('ana')[0]['status'] == 'cancelada'


def test_falha_de_validacao_nao_baixa_estoque_nem_cria_reserva():
    from server.shared.errors import ErroLivraria
    sistema = loja()
    for prazo, embrulho in [('ontem', False), (PRAZO, 'sim')]:
        with pytest.raises(ErroLivraria):
            sistema.modulos.reservas.reservar('ana', '1984', prazo, embrulho)
    assert sistema.modulos.catalogo.livro('1984')['estoque'] == 1
    assert sistema.modulos.reservas.reservas('ana') == []
    assert sistema.modulos.clientes.listar_clientes() == []


def test_ultima_unidade_em_concorrencia_entre_modulos():
    from server.shared.errors import ErroLivraria
    sistema = loja()
    def reservar(cliente):
        try:
            sistema.modulos.reservas.reservar(cliente, '1984', PRAZO)
            return 201
        except ErroLivraria as erro:
            return erro.status
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(reservar, ['ana', 'bia'])) == [201, 409]
    assert sistema.modulos.catalogo.livro('1984')['estoque'] == 0


def test_dtos_nao_expoem_armazenamento_mutavel_dos_modulos():
    sistema = loja()
    perfil = sistema.modulos.clientes.obter_perfil('ana')
    perfil['generos'].append('alterado externamente')
    sistema.modulos.catalogo.livro('1984')['estoque'] = 999
    reserva = sistema.modulos.reservas.reservar('ana', '1984', PRAZO)
    reserva['status'] = 'cancelada'
    assert sistema.modulos.clientes.obter_perfil('ana')['generos'] == []
    assert sistema.modulos.catalogo.livro('1984')['estoque'] == 0
    assert sistema.modulos.reservas.reservas('ana')[0]['status'] == 'pendente'


def test_notificacao_entre_catalogo_e_clientes_respeita_preferencias():
    sistema = loja()
    sistema.modulos.catalogo.atualizar_estoque('1984', 0)
    sistema.modulos.clientes.preferencias('ana', temas_notificacao=[])
    sistema.modulos.catalogo.acompanhar_estoque('ana', '1984')
    sistema.modulos.catalogo.acompanhar_estoque('bia', '1984')
    sistema.modulos.catalogo.atualizar_estoque('1984', 2)
    assert sistema.modulos.clientes.notificacoes('ana') == []
    assert [n['tema'] for n in sistema.modulos.clientes.notificacoes('bia')] == ['estoque']


def test_dois_agregadores_podem_usar_as_mesmas_apis_sem_repo_global():
    from server.livraria import Livraria
    primeiro = loja()
    segundo = Livraria(modulos=primeiro.modulos)
    primeiro.publicar_avaliacao('ana', '1984', 5, 'Leitura marcante.')
    assert segundo.livro('1984', 'ana')['ja_avaliou'] is True


def test_fronteiras_privadas_e_grafo_de_dependencias_dos_modulos():
    raiz = Path(__file__).resolve().parents[1] / 'server/modules'
    permitidos = {
        'clientes': set(), 'catalogo': {'clientes'},
        'reservas': {'catalogo', 'clientes'}, 'visitas': {'clientes'},
        'fidelidade': {'catalogo', 'clientes'}, 'comunidade': {'clientes'},
    }
    assert {p.name for p in raiz.iterdir() if p.is_dir() and not p.name.startswith('_')} == set(permitidos)
    for modulo, dependencias in permitidos.items():
        assert (raiz / modulo / 'api.py').is_file()
        assert (raiz / modulo / '_repository.py').is_file()
        for path in (raiz / modulo).glob('*.py'):
            for no in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(no, ast.ImportFrom):
                    if no.level and no.level > 1:
                        pytest.fail(f'Import relativo cruza fronteira: {path}')
                    nomes = [no.module or '']
                elif isinstance(no, ast.Import):
                    nomes = [alias.name for alias in no.names]
                else:
                    continue
                for nome in nomes:
                    if nome.startswith('server.modules.'):
                        partes = nome.split('.')
                        destino = partes[2]
                        if destino != modulo:
                            assert destino in dependencias, (path, nome)
                            assert len(partes) <= 3 or partes[3] == 'api', (path, nome)
                    if path.name != 'http.py':
                        assert not nome.startswith(('flask', 'server.transport')), path
