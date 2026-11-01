"""Serviços relacionados à visita à loja física."""

from copy import deepcopy
from uuid import uuid4

from server.modules.clientes.api import ClientesAPI
from server.shared.context import atomico
from server.shared.errors import ErroLivraria
from server.shared.validation import data_iso, inteiro_nao_negativo, texto_obrigatorio
from ._repository import RepositorioVisitas


class Visitas:
    def __init__(self, contexto, clientes: ClientesAPI):
        self._contexto, self._clientes = contexto, clientes
        self._repo = RepositorioVisitas()

    @atomico
    def entrar_fila(self, cliente_id):
        self._clientes.obter_perfil(cliente_id)
        if cliente_id not in self._repo.fila:
            self._repo.fila.append(cliente_id)
        return self.fila(cliente_id)

    @atomico
    def fila(self, cliente_id):
        return {'posicao': self._repo.fila.index(cliente_id) + 1 if cliente_id in self._repo.fila else None}

    @atomico
    def oferecer_horario(self, livreiro, quando):
        nome = texto_obrigatorio(livreiro, 'o livreiro')
        data = data_iso(quando, self._contexto.agora, futuro=True)
        horario = {'id': uuid4().hex, 'livreiro': nome, 'quando': data.isoformat(), 'cliente_id': None}
        self._repo.horarios[horario['id']] = horario
        return deepcopy(horario)

    @atomico
    def agendar(self, cliente_id, horario_id):
        try:
            horario = self._repo.horarios.get(horario_id)
        except TypeError:
            horario = None
        if horario is None:
            raise ErroLivraria('Horário não encontrado.', 404)
        data_iso(horario['quando'], self._contexto.agora, futuro=True)
        if horario['cliente_id'] not in (None, cliente_id):
            raise ErroLivraria('Este horário já foi agendado.', 409)
        self._clientes.obter_perfil(cliente_id)
        horario['cliente_id'] = cliente_id
        return deepcopy(horario)

    @atomico
    def horarios(self):
        return [{k: deepcopy(v) for k, v in h.items() if k != 'cliente_id'}
                for h in self._repo.horarios.values()
                if h['cliente_id'] is None and data_iso(h['quando'], self._contexto.agora) > self._contexto.agora()]

    @atomico
    def agendamentos(self, cliente_id):
        return [deepcopy(h) for h in self._repo.horarios.values() if h['cliente_id'] == cliente_id]

    @atomico
    def configurar_loja(self, horario, lotacao):
        horario = texto_obrigatorio(horario, 'o horário de funcionamento')
        inteiro_nao_negativo(lotacao, 'Lotação')
        self._repo.loja = {'horario': horario, 'lotacao': lotacao}

    @atomico
    def informacoes_loja(self):
        return deepcopy(self._repo.loja)
