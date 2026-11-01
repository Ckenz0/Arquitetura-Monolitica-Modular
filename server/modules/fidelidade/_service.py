"""Fidelidade e recomendações compostas a partir de contratos públicos."""

from copy import deepcopy
from uuid import uuid4

from server.modules.catalogo.api import CatalogoAPI
from server.modules.clientes.api import ClientesAPI
from server.shared.context import atomico
from server.shared.errors import ErroLivraria
from server.shared.validation import data_iso, inteiro_nao_negativo, texto_obrigatorio
from ._repository import RepositorioFidelidade


class Fidelidade:
    def __init__(self, contexto, catalogo: CatalogoAPI, clientes: ClientesAPI):
        self._contexto, self._catalogo, self._clientes = contexto, catalogo, clientes
        self._repo = RepositorioFidelidade()

    @atomico
    def registrar_compra(self, cliente_id, livro_id, pontos, expira_em=None, avisar_em=None):
        livro = self._catalogo.livro(livro_id)
        inteiro_nao_negativo(pontos, 'Pontos')
        expiracao = data_iso(expira_em, self._contexto.agora) if expira_em is not None else None
        aviso = data_iso(avisar_em, self._contexto.agora) if avisar_em is not None else None
        if aviso and (not expiracao or aviso >= expiracao):
            raise ErroLivraria('O aviso deve ocorrer antes da expiração dos pontos.')
        self._clientes.obter_perfil(cliente_id)
        compra = {'id': uuid4().hex, 'livro': livro, 'pontos': pontos,
                  'data': self._contexto.agora().isoformat(),
                  'expira_em': expiracao.isoformat() if expiracao else None,
                  'avisar_em': aviso.isoformat() if aviso else None, '_avisado': False}
        self._repo.compras.setdefault(cliente_id, []).append(compra)
        return {k: deepcopy(v) for k, v in compra.items() if not k.startswith('_')}

    @atomico
    def historico(self, cliente_id):
        self._clientes.obter_perfil(cliente_id)
        return [{k: deepcopy(v) for k, v in c.items() if not k.startswith('_')}
                for c in self._repo.compras.get(cliente_id, [])]

    @atomico
    def fidelidade(self, cliente_id):
        self._clientes.obter_perfil(cliente_id)
        saldo = sum(c['pontos'] for c in self._repo.compras.get(cliente_id, [])
                    if c['expira_em'] is None or data_iso(c['expira_em'], self._contexto.agora) > self._contexto.agora())
        return {'saldo': saldo, 'cartao': {'cliente_id': cliente_id, 'numero': f'LIV-{cliente_id}'},
                'cupons': deepcopy(self._repo.cupons.get(cliente_id, []))}

    @atomico
    def conceder_cupom(self, cliente_id, codigo, termos):
        cupom = {'codigo': texto_obrigatorio(codigo, 'o código do cupom'),
                 'termos': texto_obrigatorio(termos, 'os termos do cupom')}
        self._clientes.obter_perfil(cliente_id)
        self._repo.cupons.setdefault(cliente_id, []).append(cupom)
        self._clientes.notificar(cliente_id, 'fidelidade', f'Você recebeu o cupom {cupom["codigo"]}.')
        return deepcopy(cupom)

    @atomico
    def recomendacoes(self, cliente_id):
        cliente = self._clientes.obter_perfil(cliente_id)
        compras = self.historico(cliente_id)
        comprados = {c['livro']['id'] for c in compras}
        generos = {g.casefold() for g in cliente['generos']}
        generos.update(c['livro']['genero'].casefold() for c in compras)
        return [l for l in self._catalogo.buscar()
                if l['genero'].casefold() in generos and l['id'] not in comprados]

    @atomico
    def processar_lembretes(self):
        agora = self._contexto.agora()
        for cliente_id, compras in self._repo.compras.items():
            for compra in compras:
                if (compra['avisar_em'] and not compra['_avisado']
                    and data_iso(compra['avisar_em'], self._contexto.agora) <= agora
                    < data_iso(compra['expira_em'], self._contexto.agora)):
                    self._clientes.notificar(cliente_id, 'fidelidade',
                                            f'{compra["pontos"]} pontos expiram em {compra["expira_em"]}.')
                    compra['_avisado'] = True
