"""Coleções privadas de eventos e clubes."""

class RepositorioComunidade:
    def __init__(self):
        self._colecoes = {'eventos': {}, 'clubes': {}}

    def obter(self, colecao, identificador):
        return self._colecoes[colecao].get(identificador)

    def salvar(self, colecao, identificador, valor):
        self._colecoes[colecao][identificador] = valor

    def listar(self, colecao):
        return tuple(self._colecoes[colecao].values())
