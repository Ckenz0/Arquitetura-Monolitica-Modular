"""Erros públicos de aplicação."""


class ErroLivraria(ValueError):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.status = status
