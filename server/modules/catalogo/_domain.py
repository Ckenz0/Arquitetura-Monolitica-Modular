"""Regras e valores do catálogo."""

from copy import deepcopy
from dataclasses import dataclass

from server.shared.errors import ErroLivraria
from server.shared.validation import texto_obrigatorio


@dataclass(frozen=True)
class Avaliacao:
    nota: int
    texto: str

    def __post_init__(self):
        if type(self.nota) is not int or not 1 <= self.nota <= 5:
            raise ErroLivraria('Escolha uma nota inteira de 1 a 5.')
        object.__setattr__(self, 'texto', texto_obrigatorio(self.texto, 'seu comentário'))


def filtrar_livros(livros, **criterios):
    return [deepcopy(livro) for livro in livros
            if all(livro.get(campo) == valor for campo, valor in criterios.items())]
