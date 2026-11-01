"""Catálogo, avaliações e interesses privados deste módulo."""

from copy import deepcopy

from server.shared.errors import ErroLivraria


class RepositorioCatalogo:
    def __init__(self, livros):
        self.livros = deepcopy(livros or [])
        self.avaliacoes = {}
        self.acompanhamentos = {}
        self.desejos = {}

    def obter(self, livro_id):
        for livro in self.livros:
            if livro['id'] == livro_id:
                return livro
        raise ErroLivraria('Livro não encontrado.', 404)
