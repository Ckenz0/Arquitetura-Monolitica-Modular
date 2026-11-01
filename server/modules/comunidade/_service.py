"""Agenda e participação na comunidade de leitores."""

from copy import deepcopy
from uuid import uuid4

from server.modules.clientes.api import ClientesAPI
from server.shared.context import atomico
from server.shared.errors import ErroLivraria
from server.shared.validation import data_iso, inteiro_nao_negativo, texto_obrigatorio
from ._repository import RepositorioComunidade


class Comunidade:
    def __init__(self, contexto, clientes: ClientesAPI):
        self._contexto, self._clientes = contexto, clientes
        self._repo = RepositorioComunidade()

    def _data(self, valor, futuro=False):
        return data_iso(valor, self._contexto.agora, futuro=futuro)

    def _cliente(self, cliente_id):
        return self._clientes.obter_perfil(cliente_id)

    def _notificar(self, cliente_id, tema, mensagem):
        self._clientes.notificar(cliente_id, tema, mensagem)

    def _recurso(self, colecao, identificador, nome):
        try:
            recurso = self._repo.obter(colecao, identificador)
        except TypeError:
            recurso = None
        if recurso is None:
            raise ErroLivraria(f"{nome} não encontrado.", 404)
        return recurso


    @atomico
    def cadastrar_evento(self, titulo, quando, local, capacidade=None, lembrar_em=None):
        titulo = texto_obrigatorio(titulo, "o título do evento")
        local = texto_obrigatorio(local, "o local do evento")
        data = self._data(quando, futuro=True)
        if capacidade is not None:
            inteiro_nao_negativo(capacidade, "Capacidade")
        lembrete = self._data(lembrar_em) if lembrar_em is not None else None
        if lembrete and lembrete >= data:
            raise ErroLivraria("O lembrete deve ocorrer antes do evento.")
        evento = {"id": uuid4().hex, "titulo": titulo, "quando": data.isoformat(), "local": local,
                  "capacidade": capacidade, "lembrar_em": lembrete.isoformat() if lembrete else None,
                  "inscritos": set(), "avisados": set()}
        self._repo.salvar("eventos", evento["id"], evento)
        return next(e for e in self.eventos() if e["id"] == evento["id"])


    @atomico
    def eventos(self, cliente_id=None):
        return [{k: deepcopy(v) for k, v in e.items() if k not in {"inscritos", "avisados"}}
                | {"inscrito": cliente_id in e["inscritos"],
                   "vagas": None if e["capacidade"] is None else e["capacidade"] - len(e["inscritos"])}
                for e in sorted(self._repo.listar("eventos"), key=lambda e: self._data(e["quando"]))]


    @atomico
    def inscrever(self, cliente_id, evento_id):
        evento = self._recurso("eventos", evento_id, "Evento")
        self._data(evento["quando"], futuro=True)
        if cliente_id not in evento["inscritos"]:
            if evento["capacidade"] is not None and len(evento["inscritos"]) >= evento["capacidade"]:
                raise ErroLivraria("Não há vagas disponíveis neste evento.", 409)
            self._cliente(cliente_id)
            evento["inscritos"].add(cliente_id)
        return {"evento_id": evento_id, "confirmada": True}


    @atomico
    def criar_clube(self, nome):
        nome = texto_obrigatorio(nome, "o nome do clube")
        clube = {"id": uuid4().hex, "nome": nome, "membros": set(), "opinioes": []}
        self._repo.salvar("clubes", clube["id"], clube)
        return {"id": clube["id"], "nome": nome}


    @atomico
    def participar_clube(self, cliente_id, clube_id):
        clube = self._recurso("clubes", clube_id, "Clube")
        self._cliente(cliente_id)
        clube["membros"].add(cliente_id)
        return {"clube_id": clube_id, "participando": True}


    @atomico
    def publicar_opiniao(self, cliente_id, clube_id, texto):
        clube = self._recurso("clubes", clube_id, "Clube")
        texto = texto_obrigatorio(texto, "sua opinião")
        if cliente_id not in clube["membros"]:
            raise ErroLivraria("Participe do clube antes de publicar.", 409)
        opiniao = {"cliente": cliente_id, "texto": texto}
        clube["opinioes"].append(opiniao)
        return deepcopy(opiniao)


    @atomico
    def clubes(self, cliente_id):
        return [{"id": c["id"], "nome": c["nome"], "participando": cliente_id in c["membros"],
                 "membros": len(c["membros"]), "opinioes": deepcopy(c["opinioes"])}
                for c in self._repo.listar("clubes")]


    @atomico
    def processar_lembretes(self):
        agora = self._contexto.agora()
        for evento in self._repo.listar('eventos'):
            if (evento['lembrar_em']
                and self._data(evento['lembrar_em']) <= agora < self._data(evento['quando'])):
                for cliente_id in evento['inscritos'] - evento['avisados']:
                    self._notificar(cliente_id, 'eventos',
                                    f'Lembrete: {evento["titulo"]} em {evento["quando"]}.')
                    evento['avisados'].add(cliente_id)
