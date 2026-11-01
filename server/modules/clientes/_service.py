"""Perfis, preferências e notificações dos clientes."""

from copy import deepcopy
from uuid import uuid4

from server.shared.context import atomico
from server.shared.validation import NAO_INFORMADO, texto_obrigatorio
from ._domain import validar_preferencias
from ._repository import RepositorioClientes


class Clientes:
    def __init__(self, contexto):
        self._contexto = contexto
        self._repo = RepositorioClientes()

    def _obter(self, cliente_id):
        texto_obrigatorio(cliente_id, 'o identificador do cliente')
        return self._repo.clientes.setdefault(cliente_id, {
            'id': cliente_id, 'generos': [], 'temas_notificacao': None, 'notificacoes': [],
        })

    @atomico
    def obter_perfil(self, cliente_id):
        cliente = self._obter(cliente_id)
        return {k: deepcopy(cliente[k]) for k in ('id', 'generos', 'temas_notificacao')}

    @atomico
    def preferencias(self, cliente_id, generos=NAO_INFORMADO, temas_notificacao=NAO_INFORMADO):
        validar_preferencias(generos, temas_notificacao)
        cliente = self._obter(cliente_id)
        if generos is not NAO_INFORMADO:
            cliente['generos'] = list(dict.fromkeys(g.strip() for g in generos))
        if temas_notificacao is not NAO_INFORMADO:
            cliente['temas_notificacao'] = None if temas_notificacao is None else list(dict.fromkeys(temas_notificacao))
        return {k: deepcopy(cliente[k]) for k in ('generos', 'temas_notificacao')}

    @atomico
    def notificar(self, cliente_id, tema, mensagem):
        cliente = self._obter(cliente_id)
        temas = cliente['temas_notificacao']
        if temas is None or tema in temas:
            cliente['notificacoes'].append({
                'id': uuid4().hex, 'tema': tema, 'mensagem': mensagem,
                'data': self._contexto.agora().isoformat(),
            })

    @atomico
    def notificacoes(self, cliente_id):
        return deepcopy(self._obter(cliente_id)['notificacoes'])

    @atomico
    def listar_clientes(self):
        return [self.obter_perfil(cid) for cid in self._repo.clientes]
